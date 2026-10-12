package com.visionbridge.android

import android.accessibilityservice.AccessibilityService
import android.os.Handler
import android.os.Looper
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Toast
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Opt-in prototype. It observes accessibility text only while DeepSeek is foregrounded.
 * Candidate selection is heuristic; users should treat automatic capture as experimental.
 */
class DeepSeekReplyAccessibilityService : AccessibilityService() {
    private enum class ReplyState {
        IDLE,
        IN_FLIGHT,
        RETRY_WAIT,
        EXHAUSTED
    }

    private data class AttemptResult(
        val success: Boolean,
        val retryable: Boolean,
        val message: String
    )

    private val handler = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    // All fields below are read and written on the main thread only.
    private var pendingCapture: Runnable? = null
    private var retryRunnable: Runnable? = null
    private var state = ReplyState.IDLE
    private var activeCandidate: String? = null
    private var activeHash: String? = null
    private var pendingCandidate: String? = null
    private var lastConfirmedHash: String? = null
    private var lastMissingKeyHash: String? = null
    private var failureCount = 0
    private var destroyed = false

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val packageName = event?.packageName?.toString() ?: return
        val eventType = event.eventType
        if (packageName != DEEPSEEK_PACKAGE) return
        if (eventType != AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED &&
            eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return

        // Copy event fields first, then serialize all state changes on the main looper.
        handler.post {
            if (destroyed) return@post
            pendingCapture?.let(handler::removeCallbacks)
            pendingCapture = Runnable {
                pendingCapture = null
                captureReplyCandidate()
            }.also { handler.postDelayed(it, DEBOUNCE_MS) }
        }
    }

    private fun captureReplyCandidate() {
        if (destroyed) return
        val root = rootInActiveWindow ?: return
        val candidates = mutableListOf<String>()
        try {
            if (root.packageName?.toString() != DEEPSEEK_PACKAGE) return
            collectLeafText(root, candidates)
        } finally {
            root.recycle()
        }

        // The last long leaf is only a heuristic, not proof that this is the assistant's final reply.
        val candidate = candidates.lastOrNull { it.length >= MIN_REPLY_LENGTH } ?: return
        processCandidate(candidate)
    }

    private fun processCandidate(candidate: String) {
        val digest = sha256(candidate)

        if (digest == lastConfirmedHash) {
            // If the visible tree has returned to the already-saved reply, discard a stale queued candidate.
            if (state == ReplyState.IN_FLIGHT) pendingCandidate = null
            return
        }

        when (state) {
            ReplyState.IN_FLIGHT -> {
                // Keep only the newest observed candidate; do not launch concurrent writes.
                pendingCandidate = if (digest != activeHash) candidate else null
                return
            }

            ReplyState.RETRY_WAIT -> {
                if (digest == activeHash) return
                cancelRetry()
                pendingCandidate = null
                activeCandidate = null
                activeHash = null
                failureCount = 0
                state = ReplyState.IDLE
            }

            ReplyState.EXHAUSTED -> {
                if (digest == activeHash) return
                activeCandidate = null
                activeHash = null
                failureCount = 0
                state = ReplyState.IDLE
            }

            ReplyState.IDLE -> Unit
        }

        startAttempt(candidate, isRetry = false)
    }

    private fun startAttempt(candidate: String, isRetry: Boolean) {
        if (destroyed) return
        val digest = sha256(candidate)
        if (!isRetry && digest != activeHash) failureCount = 0

        val key = runCatching { SecretStore.read(this) }.getOrNull()
        if (key.isNullOrBlank()) {
            state = ReplyState.IDLE
            activeCandidate = null
            activeHash = null
            if (lastMissingKeyHash != digest) {
                notifyUser("افتح جسر رائق واحفظ مفتاح الكتابة بأمان أولًا.")
            }
            lastMissingKeyHash = digest
            return
        }
        lastMissingKeyHash = null

        activeCandidate = candidate
        activeHash = digest
        state = ReplyState.IN_FLIGHT

        try {
            worker.execute {
                val result = performAttempt(candidate, key)
                handler.post {
                    completeAttempt(candidate, digest, result)
                }
            }
        } catch (_: Exception) {
            completeAttempt(
                candidate,
                digest,
                AttemptResult(false, true, "تعذّر بدء طلب الحفظ.")
            )
        }
    }

    private fun performAttempt(candidate: String, key: String): AttemptResult {
        return try {
            val payload = JSONObject().put("content", candidate).toString()
            val body = payload.toRequestBody("application/json; charset=utf-8".toMediaType())
            val request = Request.Builder()
                .url("$API_BASE/api/sync")
                .header("x-sync-write-key", key)
                .post(body)
                .build()

            client.newCall(request).execute().use { response ->
                val result = runCatching {
                    JSONObject(response.body?.string().orEmpty())
                }.getOrElse { JSONObject() }

                if (response.isSuccessful && result.optBoolean("ok")) {
                    AttemptResult(true, false, "")
                } else {
                    val error = result.optString("error", "HTTP ${response.code}")
                    val status = result.optInt("status", response.code)
                    val message = when (error) {
                        "unauthorized" -> "مفتاح الكتابة غير صحيح. راجع المفتاح المحفوظ."
                        "sync_not_configured" -> "الحفظ غير مفعّل؛ يلزم إعداد أسرار الخادم في Vercel."
                        "request_too_large", "content_too_large" -> "رد DeepSeek أكبر من الحد المسموح."
                        "content_required" -> "الخادم لم يتلقّ نصًا صالحًا."
                        "github_read_failed", "github_write_failed" ->
                            "فشل الحفظ لدى GitHub (HTTP $status)."
                        "github_read_invalid_response", "github_write_invalid_response" ->
                            "أعاد GitHub استجابة غير صالحة."
                        "github_unreachable" -> "تعذّر اتصال الخادم بـ GitHub."
                        else -> "فشل الحفظ: $error (HTTP ${response.code})."
                    }
                    AttemptResult(
                        success = false,
                        retryable = response.code >= 500,
                        message = message
                    )
                }
            }
        } catch (_: Exception) {
            AttemptResult(false, true, "تعذّر الاتصال بالخادم. تحقق من الإنترنت.")
        }
    }

    private fun completeAttempt(candidate: String, digest: String, result: AttemptResult) {
        if (destroyed || state != ReplyState.IN_FLIGHT || activeHash != digest) return

        val newerCandidate = pendingCandidate?.takeIf {
            val nextHash = sha256(it)
            nextHash != digest && nextHash != lastConfirmedHash
        }
        pendingCandidate = null

        if (result.success) {
            lastConfirmedHash = digest
            activeCandidate = null
            activeHash = null
            failureCount = 0
            state = ReplyState.IDLE
            notifyUser("تم حفظ رد DeepSeek في SYNC/DEEPSEEK_REPLY.md")
        } else if (result.retryable) {
            failureCount += 1
            if (failureCount >= MAX_FAILURES) {
                state = ReplyState.EXHAUSTED
                notifyUser("${result.message} أُوقفت المحاولات بعد $MAX_FAILURES محاولات.")
            } else {
                state = ReplyState.RETRY_WAIT
                notifyUser("${result.message} ستُعاد المحاولة ($failureCount/$MAX_FAILURES).")
                scheduleRetry(digest)
            }
        } else {
            // Configuration/authentication/client errors should not be retried automatically.
            state = ReplyState.EXHAUSTED
            notifyUser(result.message)
        }

        // If the UI changed while the request was running, handle only the newest distinct candidate next.
        if (newerCandidate != null) {
            cancelRetry()
            activeCandidate = null
            activeHash = null
            failureCount = 0
            state = ReplyState.IDLE
            processCandidate(newerCandidate)
        }
    }

    private fun scheduleRetry(digest: String) {
        cancelRetry()
        val retry = Runnable {
            retryRunnable = null
            if (destroyed || state != ReplyState.RETRY_WAIT || activeHash != digest) {
                return@Runnable
            }
            val candidate = activeCandidate ?: return@Runnable
            startAttempt(candidate, isRetry = true)
        }
        retryRunnable = retry
        handler.postDelayed(retry, RETRY_DELAY_MS)
    }

    private fun cancelRetry() {
        retryRunnable?.let(handler::removeCallbacks)
        retryRunnable = null
    }

    private fun collectLeafText(node: AccessibilityNodeInfo, output: MutableList<String>) {
        val text = node.text?.toString()?.trim().orEmpty()
        if (node.childCount == 0 && text.length >= MIN_REPLY_LENGTH && !looksLikeInput(text)) {
            output.add(text)
        }
        for (index in 0 until node.childCount) {
            val child = node.getChild(index) ?: continue
            try {
                collectLeafText(child, output)
            } finally {
                child.recycle()
            }
        }
    }

    private fun looksLikeInput(text: String): Boolean {
        val value = text.lowercase()
        return value.contains("send a message") ||
            value.contains("ask anything") ||
            (value.contains("deepseek") && text.length < 180)
    }

    private fun notifyUser(message: String) {
        if (destroyed) return
        handler.post {
            if (!destroyed) {
                Toast.makeText(applicationContext, message, Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun sha256(value: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest(value.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }

    override fun onInterrupt() {
        pendingCapture?.let(handler::removeCallbacks)
        pendingCapture = null
    }

    override fun onDestroy() {
        destroyed = true
        pendingCapture?.let(handler::removeCallbacks)
        pendingCapture = null
        cancelRetry()
        pendingCandidate = null
        worker.shutdownNow()
        super.onDestroy()
    }

    companion object {
        private const val DEEPSEEK_PACKAGE = "com.deepseek.chat"
        private const val API_BASE = "https://assistant-cloud-memory.vercel.app"
        private const val MIN_REPLY_LENGTH = 120
        private const val DEBOUNCE_MS = 2200L
        private const val RETRY_DELAY_MS = 5000L
        private const val MAX_FAILURES = 3
    }
}
