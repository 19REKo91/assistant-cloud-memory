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
 * The user must explicitly enable it in Android Accessibility settings.
 */
class DeepSeekReplyAccessibilityService : AccessibilityService() {
    private val handler = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()
    private var pendingCapture: Runnable? = null
    private var lastCandidate: String? = null
    private var lastSavedHash: String? = null

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null || event.packageName?.toString() != DEEPSEEK_PACKAGE) return
        if (event.eventType != AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED &&
            event.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return
        pendingCapture?.let(handler::removeCallbacks)
        pendingCapture = Runnable { captureReplyCandidate() }.also {
            handler.postDelayed(it, DEBOUNCE_MS)
        }
    }

    private fun captureReplyCandidate() {
        val root = rootInActiveWindow ?: return
        if (root.packageName?.toString() != DEEPSEEK_PACKAGE) return
        val candidates = mutableListOf<String>()
        collectLeafText(root, candidates)
        val candidate = candidates.lastOrNull { it.length >= MIN_REPLY_LENGTH } ?: return
        if (candidate == lastCandidate) return
        lastCandidate = candidate

        val key = SecretStore.read(this)
        if (key.isNullOrBlank()) {
            notifyUser("افتح جسر رائق واحفظ مفتاح الكتابة بأمان أولًا.")
            return
        }
        val digest = sha256(candidate)
        if (digest == lastSavedHash) return

        worker.execute {
            try {
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
                        lastSavedHash = digest
                        notifyUser("تم حفظ رد DeepSeek في SYNC/DEEPSEEK_REPLY.md")
                    } else {
                        notifyUser("لم يُحفظ الرد: " + result.optString("error", "HTTP ${response.code}"))
                    }
                }
            } catch (error: Exception) {
                notifyUser("تعذّر حفظ الرد: ${error.message ?: "خطأ اتصال"}")
            }
        }
    }

    private fun collectLeafText(node: AccessibilityNodeInfo, output: MutableList<String>) {
        val text = node.text?.toString()?.trim().orEmpty()
        if (node.childCount == 0 && text.length >= MIN_REPLY_LENGTH && !looksLikeInput(text)) {
            output.add(text)
        }
        for (index in 0 until node.childCount) {
            val child = node.getChild(index) ?: continue
            collectLeafText(child, output)
            child.recycle()
        }
    }

    private fun looksLikeInput(text: String): Boolean {
        val value = text.lowercase()
        return value.contains("send a message") ||
            value.contains("ask anything") ||
            (value.contains("deepseek") && text.length < 180)
    }

    private fun notifyUser(message: String) {
        handler.post { Toast.makeText(applicationContext, message, Toast.LENGTH_LONG).show() }
    }

    private fun sha256(value: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest(value.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }

    override fun onInterrupt() {
        pendingCapture?.let(handler::removeCallbacks)
    }

    override fun onDestroy() {
        pendingCapture?.let(handler::removeCallbacks)
        worker.shutdownNow()
        super.onDestroy()
    }

    companion object {
        private const val DEEPSEEK_PACKAGE = "com.deepseek.chat"
        private const val API_BASE = "https://assistant-cloud-memory.vercel.app"
        private const val MIN_REPLY_LENGTH = 120
        private const val DEBOUNCE_MS = 2200L
    }
}
