package com.visionbridge.android

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.appcompat.app.AlertDialog
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {
    private val apiBase = "https://assistant-cloud-memory.vercel.app"
    private val outgoingMessageUrl =
        "https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/main/SYNC/CHATGPT_TO_DEEPSEEK.md"
    private val archiveIndexUrl =
        "https://github.com/19REKo91/assistant-cloud-memory/blob/main/PROJECTS/raiq/derived-read/RAEQ_MASTER/00-index.md"

    private val client = OkHttpClient.Builder()
        .connectTimeout(12, TimeUnit.SECONDS)
        .readTimeout(35, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .build()
    private val executor = Executors.newSingleThreadExecutor()

    private lateinit var contentInput: EditText
    private lateinit var keyInput: EditText
    private lateinit var status: TextView
    private lateinit var saveButton: Button
    private lateinit var savedButton: Button
    private var savedUrl: String? = null
    private var savingReply = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(18), dp(18), dp(22))
            setBackgroundColor(0xFF101318.toInt())
        }

        val scroll = ScrollView(this).apply {
            isFillViewport = true
            addView(root)
        }

        val title = TextView(this).apply {
            text = "جسر رائق"
            textSize = 27f
            setTextColor(0xFFFFD54F.toInt())
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setPadding(0, dp(4), 0, dp(8))
        }
        root.addView(title, matchWrap())

        val description = TextView(this).apply {
            text = "حمّل رسالة ChatGPT وشارك النصوص يدويًا. يمكن اختياريًا التقاط رد DeepSeek تلقائيًا بعد تفعيل خدمة إمكانية الوصول بنفسك. لا يعدّل هذا التطبيق تطبيق DeepSeek."
            textSize = 14f
            setTextColor(0xFFE0E3E7.toInt())
            setPadding(0, 0, 0, dp(12))
        }
        root.addView(description, matchWrap())

        contentInput = EditText(this).apply {
            hint = "شارك رد DeepSeek إلى هذا التطبيق، أو الصق النص هنا..."
            setTextColor(0xFFFFFFFF.toInt())
            setHintTextColor(0xFF9AA4B2.toInt())
            setBackgroundColor(0xFF252A33.toInt())
            inputType = InputType.TYPE_CLASS_TEXT or
                InputType.TYPE_TEXT_FLAG_MULTI_LINE or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            gravity = Gravity.TOP or Gravity.START
            minLines = 9
            maxLines = 18
            setPadding(dp(12), dp(10), dp(12), dp(10))
        }
        root.addView(contentInput, matchWrap().apply { bottomMargin = dp(12) })

        keyInput = EditText(this).apply {
            hint = "مفتاح الكتابة SYNC_WRITE_KEY"
            setTextColor(0xFFFFFFFF.toInt())
            setHintTextColor(0xFF9AA4B2.toInt())
            setBackgroundColor(0xFF252A33.toInt())
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            isSingleLine = true
            setPadding(dp(12), dp(8), dp(12), dp(8))
        }
        root.addView(keyInput, matchWrap().apply { bottomMargin = dp(10) })

        root.addView(makeButton("حمّل رسالة ChatGPT") { loadOutgoingMessage() }, matchWrap())
        root.addView(makeButton("انسخ النص الحالي") { copyCurrentText() }, matchWrap())
        saveButton = makeButton("احفظ رد DeepSeek في الأرشيف") { confirmSaveReply() }
        root.addView(saveButton, matchWrap())
        savedButton = makeButton("افتح الرد المحفوظ") { openSavedReply() }.apply {
            isEnabled = false
        }
        root.addView(savedButton, matchWrap())
        root.addView(makeButton("افتح فهرس أرشيف رائق") { openUrl(archiveIndexUrl) }, matchWrap())
        root.addView(makeButton("احفظ مفتاح الكتابة بأمان") { saveRelayKeySecurely() }, matchWrap())
        root.addView(makeButton("إعدادات إمكانية الوصول") { openAccessibilitySettings() }, matchWrap())
        root.addView(makeButton("احذف المفتاح المحفوظ") { clearSavedRelayKey() }, matchWrap())
        root.addView(makeButton("افتح تطبيق DeepSeek") { openDeepSeek() }, matchWrap())

        status = TextView(this).apply {
            text = "جاهز. يمكن مشاركة النص من DeepSeek إلى «جسر رائق»."
            textSize = 14f
            setTextColor(0xFFFFD54F.toInt())
            setPadding(0, dp(12), 0, dp(4))
        }
        root.addView(status, matchWrap())

        setContentView(scroll)
        receiveSharedText(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        receiveSharedText(intent)
    }

    private fun receiveSharedText(source: Intent?) {
        if (source == null) return
        val shared = when (source.action) {
            Intent.ACTION_SEND -> source.getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString()
            Intent.ACTION_PROCESS_TEXT -> source.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)?.toString()
            else -> null
        }
        if (!shared.isNullOrBlank()) {
            contentInput.setText(shared)
            contentInput.setSelection(contentInput.text.length)
            status.text = "وصل النص من تطبيق آخر. راجعه ثم اضغط «احفظ رد DeepSeek في الأرشيف»."
            savedUrl = null
            savedButton.isEnabled = false
        }
    }

    private fun loadOutgoingMessage() {
        if (contentInput.text.toString().isNotBlank()) {
            AlertDialog.Builder(this)
                .setTitle("استبدال النص الحالي؟")
                .setMessage("تحميل رسالة ChatGPT سيستبدل النص الظاهر في المربع. انسخه أو احفظه أولًا إن كنت تحتاجه.")
                .setNegativeButton("إلغاء", null)
                .setPositiveButton("تحميل") { _, _ -> fetchOutgoingMessage() }
                .show()
        } else {
            fetchOutgoingMessage()
        }
    }

    private fun fetchOutgoingMessage() {
        status.text = "جارٍ جلب رسالة ChatGPT من المستودع..."
        executor.execute {
            try {
                val request = Request.Builder().url(outgoingMessageUrl).get().build()
                client.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) throw IllegalStateException("HTTP ${response.code}")
                    val text = response.body?.string().orEmpty()
                    if (text.isBlank()) throw IllegalStateException("الملف فارغ")
                    runOnUiThread {
                        contentInput.setText(text)
                        contentInput.setSelection(0)
                        status.text = "تم تحميل رسالة ChatGPT. انسخها ثم افتح DeepSeek والصقها في المحادثة."
                        savedUrl = null
                        savedButton.isEnabled = false
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { status.text = "تعذّر جلب الرسالة: ${e.message ?: e.javaClass.simpleName}" }
            }
        }
    }

    private fun copyCurrentText() {
        val text = contentInput.text.toString()
        if (text.isBlank()) {
            status.text = "لا يوجد نص لنسخه."
            return
        }
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("RAEQ bridge text", text))
        status.text = "نُسخ النص إلى الحافظة."
    }

    /**
     * Presents the complete reply for an explicit user review before any network request.
     * The manually entered key takes precedence over the key stored in Android Keystore.
     */
    private fun confirmSaveReply() {
        if (savingReply) return

        val text = contentInput.text.toString().trim()
        if (text.isBlank()) {
            status.text = "ألصق رد DeepSeek أو شاركه إلى التطبيق أولًا."
            return
        }

        val enteredKey = keyInput.text.toString()
        val key = if (enteredKey.isNotBlank()) enteredKey else SecretStore.read(this).orEmpty()
        if (key.isBlank()) {
            status.text = "أدخل مفتاح الكتابة، أو احفظه أولًا باستخدام «احفظ مفتاح الكتابة بأمان»."
            return
        }

        val previewText = TextView(this).apply {
            text = text
            textSize = 14f
            setTextColor(0xFFE0E3E7.toInt())
            setPadding(dp(10), dp(8), dp(10), dp(8))
            setTextIsSelectable(true)
        }
        val previewScroll = ScrollView(this).apply {
            isFillViewport = false
            addView(
                previewText,
                ScrollView.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                )
            )
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(380)
            )
        }

        val dialog = AlertDialog.Builder(this)
            .setTitle("راجع الرد كاملًا قبل الحفظ")
            .setView(previewScroll)
            .setNegativeButton("إلغاء", null)
            .setPositiveButton("تأكيد الحفظ", null)
            .create()
        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                dialog.dismiss()
                saveReply(text, key)
            }
        }
        dialog.show()
    }

    private fun saveReply(text: String, key: String) {
        if (savingReply) return
        savingReply = true
        savedUrl = null
        savedButton.isEnabled = false
        saveButton.isEnabled = false
        keyInput.setText("")
        status.text = "جارٍ حفظ الرد في ملف أرشيف جديد..."

        executor.execute {
            try {
                val json = JSONObject().put("content", text).toString()
                val body = json.toRequestBody("application/json; charset=utf-8".toMediaType())
                val request = Request.Builder()
                    .url("$apiBase/api/archive")
                    .header("x-sync-write-key", key)
                    .post(body)
                    .build()

                client.newCall(request).execute().use { response ->
                    val raw = response.body?.string().orEmpty()
                    val data = runCatching { JSONObject(raw) }.getOrElse { JSONObject() }
                    if (!response.isSuccessful || !data.optBoolean("ok")) {
                        val error = data.optString("error", "archive_failed")
                        throw IllegalStateException(when (error) {
                            "unauthorized" -> "مفتاح الكتابة غير صحيح."
                            "sync_not_configured" -> "الحفظ غير مفعّل؛ يلزم إعداد أسرار الخادم في Vercel."
                            "request_too_large" -> "الطلب أكبر من الحد المسموح."
                            "invalid_json" -> "لم يستطع الخادم قراءة الطلب."
                            "content_required" -> "لم يتلقّ الخادم نصًا صالحًا."
                            "content_too_large" -> "النص أكبر من الحد المسموح للأرشفة."
                            "github_write_failed" -> "رفض GitHub الحفظ (HTTP ${data.optInt("status")})."
                            "github_unreachable" -> "تعذّر اتصال الخادم بـ GitHub."
                            else -> "فشل الحفظ: $error"
                        })
                    }

                    val url = data.optString("url")
                    val path = data.optString("path")
                    runOnUiThread {
                        savingReply = false
                        saveButton.isEnabled = true
                        savedUrl = url.takeIf { it.startsWith("https://github.com/") }
                        savedButton.isEnabled = savedUrl != null
                        status.text = if (path.isNotBlank()) {
                            "تم الحفظ في ملف أرشيف جديد: $path"
                        } else {
                            "أكد الخادم الحفظ، لكنه لم يُرجع مسار الملف."
                        }
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    savingReply = false
                    saveButton.isEnabled = true
                    status.text = when (e) {
                        is IOException -> "تعذّر الاتصال بالخادم. تحقق من الإنترنت ثم حاول مجددًا."
                        else -> e.message ?: "تعذّر حفظ الرد."
                    }
                }
            }
        }
    }

    private fun openSavedReply() {
        val url = savedUrl
        if (url.isNullOrBlank()) {
            status.text = "لا يوجد رابط محفوظ بعد."
            return
        }
        openUrl(url)
    }

    private fun saveRelayKeySecurely() {
        val key = keyInput.text.toString()
        if (key.isBlank()) {
            status.text = "أدخل SYNC_WRITE_KEY أولًا."
            return
        }
        runCatching { SecretStore.save(this, key) }
            .onSuccess {
                keyInput.setText("")
                status.text = "حُفظ مفتاح الكتابة مشفّرًا باستخدام Android Keystore."
            }
            .onFailure {
                status.text = "تعذّر حفظ المفتاح بأمان: ${it.message ?: "خطأ"}"
            }
    }

    private fun clearSavedRelayKey() {
        val cleared = SecretStore.clear(this)
        status.text = if (cleared) {
            "حُذف مفتاح الكتابة المحفوظ وبياناته المشفّرة."
        } else {
            "حُذفت البيانات المشفّرة، لكن تعذّر تأكيد حذف مدخل المفتاح من Android Keystore."
        }
    }

    private fun openAccessibilitySettings() {
        runCatching {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }.onFailure {
            status.text = "تعذّر فتح إعدادات إمكانية الوصول."
        }
    }

    private fun openDeepSeek() {
        val launch = packageManager.getLaunchIntentForPackage("com.deepseek.chat")
        if (launch == null) {
            openUrl("https://chat.deepseek.com/")
        } else {
            startActivity(launch)
        }
    }

    private fun openUrl(url: String) {
        runCatching {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        }.onFailure {
            status.text = "تعذّر فتح الرابط: ${it.message ?: it.javaClass.simpleName}"
        }
    }

    private fun makeButton(label: String, action: () -> Unit): Button =
        Button(this).apply {
            text = label
            setOnClickListener { action() }
        }

    private fun matchWrap() =
        LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        executor.shutdownNow()
        super.onDestroy()
    }
}
