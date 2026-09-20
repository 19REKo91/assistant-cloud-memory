package com.visionbridge.android

import android.content.Context
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.media.ImageReader
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import android.util.Base64
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    private val client = OkHttpClient()
    private val executor = Executors.newSingleThreadExecutor()
    private var latestFrame: ByteArray? = null
    private var projection: android.media.projection.MediaProjection? = null
    private var virtualDisplay: android.hardware.display.VirtualDisplay? = null
    private var reader: ImageReader? = null
    private lateinit var status: TextView
    private lateinit var urlInput: EditText

    private val capturePermission = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode != RESULT_OK || result.data == null) {
            status.text = "لم تُمنح صلاحية التقاط الشاشة"
            return@registerForActivityResult
        }
        val mgr = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projection = mgr.getMediaProjection(result.resultCode, result.data!!)
        startCapture()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }
        urlInput = EditText(this).apply {
            hint = "Bridge URL"
            setText("http://10.0.2.2:8787")
            isSingleLine = true
        }
        val start = Button(this).apply {
            text = "بدء التقاط الشاشة"
            setOnClickListener { requestCapture() }
        }
        val see = Button(this).apply {
            text = "شوف الشاشة"
            setOnClickListener { sendLatestFrame() }
        }
        status = TextView(this).apply {
            text = "جاهز. ابدأ التقاط الشاشة."
            textSize = 16f
        }
        root.addView(urlInput)
        root.addView(start)
        root.addView(see)
        root.addView(status)
        setContentView(root)
    }

    private fun requestCapture() {
        val mgr = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        capturePermission.launch(mgr.createScreenCaptureIntent())
    }

    private fun startCapture() {
        val metrics = resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi
        reader?.close()
        reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
        reader!!.setOnImageAvailableListener({ ir ->
            val image = ir.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                val plane = image.planes[0]
                val buffer = plane.buffer
                val pixelStride = plane.pixelStride
                val rowStride = plane.rowStride
                val rowPadding = rowStride - pixelStride * width
                val bmpWidth = width + rowPadding / pixelStride
                val bitmap = Bitmap.createBitmap(bmpWidth, height, Bitmap.Config.ARGB_8888)
                bitmap.copyPixelsFromBuffer(buffer)
                val cropped = if (bmpWidth != width) Bitmap.createBitmap(bitmap, 0, 0, width, height) else bitmap
                val out = ByteArrayOutputStream()
                cropped.compress(Bitmap.CompressFormat.JPEG, 70, out)
                latestFrame = out.toByteArray()
                if (cropped !== bitmap) cropped.recycle()
                bitmap.recycle()
            } finally {
                image.close()
            }
        }, null)
        virtualDisplay?.release()
        virtualDisplay = projection!!.createVirtualDisplay(
            "VisionBridge", width, height, density, 0, reader!!.surface, null, null
        )
        status.text = "التقاط الشاشة يعمل — آخر Frame محفوظ فقط."
    }

    private fun sendLatestFrame() {
        val frame = latestFrame ?: run {
            status.text = "لا توجد لقطة بعد. اضغط بدء التقاط الشاشة."
            return
        }
        val base64 = Base64.encodeToString(frame, Base64.NO_WRAP)
        val body = JSONObject()
            .put("image_base64", base64)
            .put("mime_type", "image/jpeg")
            .put("prompt", "Describe exactly what is visible on this phone screen. Mention important text, buttons, dialogs, and the current screen state. Be concise.")
            .toString()
            .toRequestBody("application/json".toMediaType())
        val base = urlInput.text.toString().trim().removeSuffix("/")
        val request = Request.Builder().url("$base/vision").post(body).build()
        status.text = "جارٍ إرسال آخر Frame..."
        executor.execute {
            try {
                client.newCall(request).execute().use { response ->
                    val responseText = response.body?.string().orEmpty()
                    runOnUiThread {
                        if (response.isSuccessful) {
                            val answer = JSONObject(responseText).optString("text", responseText)
                            status.text = answer.ifBlank { "لم يصل وصف." }
                        } else {
                            status.text = "خطأ ${response.code}: $responseText"
                        }
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { status.text = "فشل الاتصال: ${e.message}" }
            }
        }
    }

    override fun onDestroy() {
        virtualDisplay?.release()
        reader?.close()
        projection?.stop()
        executor.shutdownNow()
        super.onDestroy()
    }
}
