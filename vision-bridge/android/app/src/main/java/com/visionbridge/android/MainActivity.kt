package com.visionbridge.android

import android.os.Bundle
import android.util.Base64
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.activity.ComponentActivity
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaType
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    private val client = OkHttpClient()
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var status: TextView
    private lateinit var streamInput: EditText
    private lateinit var bridgeInput: EditText

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        streamInput = EditText(this).apply {
            hint = "ScreenStream URL"
            setText("http://192.168.0.197:8080/stream.mjpeg")
            isSingleLine = true
        }

        bridgeInput = EditText(this).apply {
            hint = "Bridge URL"
            setText("http://10.0.2.2:8787")
            isSingleLine = true
        }

        val see = Button(this).apply {
            text = "شوف الشاشة"
            setOnClickListener { fetchAndSendFrame() }
        }

        status = TextView(this).apply {
            text = "جاهز. شغّل ScreenStream ثم اضغط «شوف الشاشة»."
            textSize = 16f
        }

        root.addView(streamInput)
        root.addView(bridgeInput)
        root.addView(see)
        root.addView(status)
        setContentView(root)
    }

    private fun fetchAndSendFrame() {
        val streamUrl = normalizeStreamUrl(streamInput.text.toString().trim())
        val bridgeUrl = bridgeInput.text.toString().trim().removeSuffix("/")

        if (streamUrl.isBlank() || bridgeUrl.isBlank()) {
            status.text = "أدخل رابط ScreenStream ورابط Bridge."
            return
        }

        status.text = "جارٍ أخذ أحدث Frame من ScreenStream..."

        executor.execute {
            try {
                val frame = fetchFirstJpeg(streamUrl)
                if (frame == null) {
                    runOnUiThread { status.text = "لم أجد صورة JPEG في بث ScreenStream." }
                    return@execute
                }

                runOnUiThread { status.text = "تم أخذ Frame — جارٍ إرساله للرؤية..." }
                sendFrame(frame, bridgeUrl)
            } catch (e: Exception) {
                runOnUiThread { status.text = "فشل ScreenStream: " + e.message }
            }
        }
    }

    private fun normalizeStreamUrl(url: String): String {
        if (url.isBlank()) return url
        val clean = url.removeSuffix("/")
        return if (clean.endsWith(".mjpeg") || clean.endsWith(".jpeg")) {
            clean
        } else {
            "$clean/stream.mjpeg"
        }
    }

    private fun fetchFirstJpeg(url: String): ByteArray? {
        val request = Request.Builder()
            .url(url)
            .header("Accept", "multipart/x-mixed-replace, image/jpeg, */*")
            .get()
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                throw IllegalStateException("HTTP " + response.code)
            }

            val body = response.body ?: throw IllegalStateException("لا يوجد بث")
            val input = BufferedInputStream(body.byteStream(), 64 * 1024)
            val out = ByteArrayOutputStream()
            var started = false
            var previous = -1

            while (true) {
                val current = input.read()
                if (current == -1) break

                if (!started) {
                    if (previous == 0xFF && current == 0xD8) {
                        started = true
                        out.write(0xFF)
                        out.write(0xD8)
                    }
                } else {
                    out.write(current)
                    if (previous == 0xFF && current == 0xD9) {
                        return out.toByteArray()
                    }
                    if (out.size() > 8 * 1024 * 1024) {
                        throw IllegalStateException("Frame أكبر من 8MB")
                    }
                }

                previous = current
            }
        }

        return null
    }

    private fun sendFrame(frame: ByteArray, bridgeUrl: String) {
        val base64 = Base64.encodeToString(frame, Base64.NO_WRAP)
        val body = JSONObject()
            .put("image_base64", base64)
            .put("mime_type", "image/jpeg")
            .put(
                "prompt",
                "Describe exactly what is visible on this phone screen. Mention important text, buttons, dialogs, and the current screen state. Be concise."
            )
            .toString()
            .toRequestBody("application/json".toMediaType())

        val request = Request.Builder()
            .url(bridgeUrl + "/vision")
            .post(body)
            .build()

        try {
            client.newCall(request).execute().use { response ->
                val responseText = response.body?.string().orEmpty()
                runOnUiThread {
                    if (response.isSuccessful) {
                        val answer = JSONObject(responseText).optString("text", responseText)
                        status.text = answer.ifBlank { "لم يصل وصف." }
                    } else {
                        status.text = "خطأ Bridge " + response.code + ": " + responseText
                    }
                }
            }
        } catch (e: Exception) {
            runOnUiThread { status.text = "فشل الاتصال بالـ Bridge: " + e.message }
        }
    }

    override fun onDestroy() {
        executor.shutdownNow()
        super.onDestroy()
    }
}
