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
        val notification = Notification.Builder(this, "vision")
            .setContentTitle("Vision Bridge")
            .setContentText("التقاط صورة الشاشة")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .build()

        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(7, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(7, notification)
        }

        val resultCode = intent?.getIntExtra("resultCode", Activity.RESULT_CANCELED)
            ?: return START_NOT_STICKY
        @Suppress("DEPRECATION")
        val data = intent.getParcelableExtra<Intent>("data")
            ?: return START_NOT_STICKY

        val mgr = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projection = mgr.getMediaProjection(resultCode, data)
        projection?.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                cleanup()
                stopSelf()
            }
        }, handler)

        val dm = resources.displayMetrics
        reader = ImageReader.newInstance(dm.widthPixels, dm.heightPixels, android.graphics.PixelFormat.RGBA_8888, 2)
        display = projection?.createVirtualDisplay(
            "VisionBridge", dm.widthPixels, dm.heightPixels, dm.densityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader?.surface, null, handler
        )

        handler.postDelayed({ captureOne() }, 250)
        return START_NOT_STICKY
    }

    private fun captureOne() {
        if (captured) return
        val image = reader?.acquireLatestImage() ?: run {
            handler.postDelayed({ captureOne() }, 100)
            return
        }
        captured = true

        try {
            val plane = image.planes[0]
            val bitmapWidth = image.width + (plane.rowStride - plane.pixelStride * image.width) / plane.pixelStride
            val bitmap = Bitmap.createBitmap(bitmapWidth, image.height, Bitmap.Config.ARGB_8888)
            bitmap.copyPixelsFromBuffer(plane.buffer)
            val cropped = Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
            val out = ByteArrayOutputStream()
            cropped.compress(Bitmap.CompressFormat.JPEG, 82, out)
            val body = out.toByteArray()
            cropped.recycle()
            bitmap.recycle()
            image.close()
            upload(body)
        } catch (_: Exception) {
            image.close()
            cleanup()
            stopSelf()
        }
    }

    private fun upload(body: ByteArray) {
        Thread {
            try {
                val boundary = "----VisionBridge"
                val conn = URL(endpoint).openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.connectTimeout = 15000
                conn.readTimeout = 15000
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
                conn.outputStream.use { os ->
                    os.write("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"latest-frame.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".toByteArray())
                    os.write(body)
                    os.write("\r\n--$boundary--\r\n".toByteArray())
                }
                conn.responseCode
                conn.disconnect()
            } catch (_: Exception) {
            } finally {
                cleanup()
                stopSelf()
            }
        }.start()
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
