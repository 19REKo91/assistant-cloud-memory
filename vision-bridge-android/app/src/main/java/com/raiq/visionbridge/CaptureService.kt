package com.raiq.visionbridge

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.*
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL

class CaptureService : Service() {
    private var projection: MediaProjection? = null
    private var display: VirtualDisplay? = null
    private var reader: ImageReader? = null
    private val handler = Handler(Looper.getMainLooper())
    private val endpoint = "https://assistant-cloud-memory.vercel.app/api/upload"
    private var captured = false

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createChannel()
        log("▶ CaptureService بدأ")
        val notification = Notification.Builder(this, "vision")
            .setContentTitle("Vision Bridge")
            .setContentText("التقاط صورة الشاشة")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .build()
        if (Build.VERSION.SDK_INT >= 29)
            startForeground(7, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        else startForeground(7, notification)
        log("✓ Foreground service بدأ")

        val resultCode = intent?.getIntExtra("resultCode", Activity.RESULT_CANCELED)
            ?: return fail("✗ resultCode مفقود")
        @Suppress("DEPRECATION")
        val data = intent.getParcelableExtra<Intent>("data")
            ?: return fail("✗ بيانات MediaProjection مفقودة")

        val mgr = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projection = try {
            mgr.getMediaProjection(resultCode, data)
        } catch (e: Exception) {
            return fail("✗ MediaProjection: " + e.javaClass.simpleName + ": " + e.message)
        }
        if (projection == null) return fail("✗ MediaProjection = null")
        log("✓ MediaProjection حصلنا عليها")

        projection?.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                log("✗ MediaProjection توقفت")
                cleanup()
                stopSelf()
            }
        }, handler)

        val dm = resources.displayMetrics
        reader = try {
            ImageReader.newInstance(dm.widthPixels, dm.heightPixels,
                android.graphics.PixelFormat.RGBA_8888, 2)
        } catch (e: Exception) {
            return fail("✗ ImageReader: " + e.javaClass.simpleName + ": " + e.message)
        }
        log("✓ ImageReader " + dm.widthPixels + "x" + dm.heightPixels)

        display = try {
            projection?.createVirtualDisplay("VisionBridge", dm.widthPixels, dm.heightPixels,
                dm.densityDpi, DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                reader?.surface, null, handler)
        } catch (e: Exception) {
            return fail("✗ VirtualDisplay: " + e.javaClass.simpleName + ": " + e.message)
        }
        if (display == null) return fail("✗ VirtualDisplay = null")
        log("✓ ScreenStream بدأ")
        handler.postDelayed({ captureOne() }, 400)
        return START_NOT_STICKY
    }

    private fun captureOne() {
        if (captured) return
        val image = reader?.acquireLatestImage()
        if (image == null) {
            log("… لا يوجد Frame، إعادة المحاولة")
            handler.postDelayed({ captureOne() }, 150)
            return
        }
        captured = true
        log("✓ Frame وصل " + image.width + "x" + image.height)
        try {
            val plane = image.planes[0]
            val bitmapWidth = image.width +
                (plane.rowStride - plane.pixelStride * image.width) / plane.pixelStride
            val bitmap = Bitmap.createBitmap(bitmapWidth, image.height, Bitmap.Config.ARGB_8888)
            bitmap.copyPixelsFromBuffer(plane.buffer)
            val cropped = Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
            val out = ByteArrayOutputStream()
            if (!cropped.compress(Bitmap.CompressFormat.JPEG, 82, out))
                throw IllegalStateException("JPEG compression failed")
            val body = out.toByteArray()
            log("✓ JPEG جاهز: " + body.size + " bytes")
            cropped.recycle()
            bitmap.recycle()
            image.close()
            upload(body)
        } catch (e: Exception) {
            runCatching { image.close() }
            fail("✗ تحويل الصورة: " + e.javaClass.simpleName + ": " + e.message)
        }
    }

    private fun upload(body: ByteArray) {
        log("→ إرسال إلى: " + endpoint)
        Thread {
            var conn: HttpURLConnection? = null
            try {
                val boundary = "----VisionBridge"
                conn = URL(endpoint).openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.connectTimeout = 15000
                conn.readTimeout = 15000
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary)
                conn.outputStream.use { os ->
                    os.write(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"file\"; filename=\"latest-frame.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").toByteArray())
                    os.write(body)
                    os.write("\r\n--".toByteArray())
                    os.write((boundary + "--\r\n").toByteArray())
                }
                val code = conn.responseCode
                val stream = if (code in 200..299) conn.inputStream else conn.errorStream
                val response = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
                log("← HTTP " + code)
                if (response.isNotBlank())
                    log("← الرد: " + response.replace("\\s+".toRegex(), " ").take(180))
                if (code !in 200..299) fail("✗ Bridge HTTP " + code)
                else log("✓ Bridge استجاب")
            } catch (e: Exception) {
                fail("✗ HTTP: " + e.javaClass.simpleName + ": " + e.message)
            } finally {
                conn?.disconnect()
                cleanup()
                stopSelf()
            }
        }.start()
    }

    private fun fail(message: String): Int {
        log(message)
        cleanup()
        stopSelf()
        return START_NOT_STICKY
    }

    private fun log(message: String) {
        sendBroadcast(Intent("com.raiq.visionbridge.DIAGNOSTIC_LOG").apply {
            setPackage(packageName)
            putExtra("message", message)
        })
    }

    private fun cleanup() {
        display?.release(); display=null
        reader?.close(); reader=null
        projection?.stop(); projection=null
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel("vision", "Vision Bridge", NotificationManager.IMPORTANCE_LOW))
        }
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        cleanup()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?) = null
}
