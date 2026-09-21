package com.raiq.visionbridge

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Toast

class MainActivity : Activity() {
    private val requestCode = 9001
    private val logAction = "com.raiq.visionbridge.DIAGNOSTIC_LOG"
    private fun log(message: String) {
        sendBroadcast(Intent(logAction).apply {
            setPackage(packageName)
            putExtra("message", message)
        })
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(View(this).apply { setBackgroundColor(Color.TRANSPARENT) })
        log("▶ MainActivity بدأ")
        if (!Settings.canDrawOverlays(this)) {
            log("✗ إذن الظهور فوق التطبيقات غير مفعّل")
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            return
        }
        log("✓ إذن الظهور فوق التطبيقات موجود")
        try {
            startService(Intent(this, OverlayService::class.java))
            log("✓ OverlayService طُلب تشغيله")
        } catch (e: Exception) {
            log("✗ OverlayService: ${e.javaClass.simpleName}: ${e.message}")
            finish(); return
        }
        if (intent?.action == "com.raiq.visionbridge.SHOW_BUBBLE") {
            log("→ طلب التقاط الشاشة")
            requestCapture()
        } else log("✓ فتح عادي بدون طلب التقاط")
    }

    private fun requestCapture() {
        try {
            val mgr = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            log("✓ MediaProjectionManager جاهز")
            startActivityForResult(mgr.createScreenCaptureIntent(), requestCode)
            log("✓ نافذة إذن التقاط الشاشة فُتحت")
        } catch (e: Exception) {
            log("✗ فتح إذن الشاشة: ${e.javaClass.simpleName}: ${e.message}")
            Toast.makeText(this, "خطأ في فتح إذن التقاط الشاشة", Toast.LENGTH_LONG).show()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != this.requestCode) return
        if (resultCode == RESULT_OK && data != null) {
            log("✓ تمت الموافقة على التقاط الشاشة")
            try {
                val i = Intent(this, CaptureService::class.java).apply {
                    putExtra("resultCode", resultCode)
                    putExtra("data", data)
                }
                startForegroundService(i)
                log("✓ CaptureService طُلب تشغيله")
            } catch (e: Exception) {
                log("✗ تشغيل CaptureService: ${e.javaClass.simpleName}: ${e.message}")
                Toast.makeText(this, "خطأ في تشغيل خدمة التقاط الشاشة", Toast.LENGTH_LONG).show()
            }
        } else {
            log("✗ المستخدم لم يوافق على التقاط الشاشة")
            Toast.makeText(this, "لم تتم الموافقة على التقاط الشاشة", Toast.LENGTH_SHORT).show()
        }
        finish()
    }
}
