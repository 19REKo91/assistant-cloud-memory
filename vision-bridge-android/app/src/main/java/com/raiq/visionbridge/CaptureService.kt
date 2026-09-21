package com.raiq.visionbridge

import android.app.*
import android.content.Intent
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

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createChannel()
        startForeground(7, Notification.Builder(this, "vision")
            .setContentTitle("Vision Bridge")
            .setContentText("التقاط الشاشة وإرسال آخر Frame")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .build())

        val resultCode = intent?.getIntExtra("resultCode", Activity.RESULT_CANCELED) ?: return START_NOT_STICKY
        val data = if (Build.VERSION.SDK_INT >= 33)
            intent.getParcelableExtra("data", Intent::class.java)
        else
            @Suppress("DEPRECATION") intent.getParcelableExtra("data")

        if (data == null) return START_NOT_STICKY
        val mgr = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projection = mgr.getMediaProjection(resultCode, data)

        val dm = resources.displayMetrics
        val width = dm.widthPixels
        val height = dm.heightPixels
        reader = ImageReader.newInstance(width, height, android.graphics.PixelFormat.RGBA_8888, 2)
        display = projection?.createVirtualDisplay(
            "VisionBridge", width, height, dm.densityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader?.surface, null, handler
        )
        handler.post(captureLoop)
        return START_STICKY
    }

    private val captureLoop = object : Runnable {
        override fun run() {
            try {
                val image = reader?.acquireLatestImage()
                if (image != null) {
                    val plane = image.planes[0]
                    val buffer = plane.buffer
                    val pixelStride = plane.pixelStride
                    val rowStride = plane.rowStride
                    val rowPadding = rowStride - pixelStride * image.width
                    val bitmap = Bitmap.createBitmap(
                        image.width + rowPadding / pixelStride,
                        image.height,
                        Bitmap.Config.ARGB_8888
                    )
                    bitmap.copyPixelsFromBuffer(buffer)
                    image.close()
                    val cropped = if (bitmap.width != image.width)
                        Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height) else bitmap
                    upload(cropped)
                    if (cropped !== bitmap) bitmap.recycle()
                    cropped.recycle()
                }
            } catch (_: Exception) {}
            handler.postDelayed(this, 1500)
        }
    }

    private fun upload(bitmap: Bitmap) {
        Thread {
            try {
                val out = ByteArrayOutputStream()
                bitmap.compress(Bitmap.CompressFormat.JPEG, 70, out)
                val body = out.toByteArray()
                val boundary = "----VisionBridge"
                val conn = URL(endpoint).openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
                conn.outputStream.use { os ->
                    os.write(("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"latest-frame.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").toByteArray())
                    os.write(body)
                    os.write("\r\n--$boundary--\r\n".toByteArray())
                }
                conn.responseCode
                conn.disconnect()
            } catch (_: Exception) {}
        }.start()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel("vision", "Vision Bridge", NotificationManager.IMPORTANCE_LOW))
        }
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        display?.release()
        reader?.close()
        projection?.stop()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?) = null
}