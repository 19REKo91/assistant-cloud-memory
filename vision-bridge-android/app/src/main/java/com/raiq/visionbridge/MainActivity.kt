package com.raiq.visionbridge

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.view.View

class MainActivity : Activity() {
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
        log("▶ التطبيق الرئيسي بدأ")

        if (!Settings.canDrawOverlays(this)) {
            log("✗ إذن الظهور فوق التطبيقات غير مفعّل")
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
            finish()
            return
        }

        log("✓ إذن الظهور فوق التطبيقات موجود")
        runCatching {
            startService(Intent(this, OverlayService::class.java))
            log("✓ OverlayService طُلب تشغيله")
        }.onFailure {
            log("✗ OverlayService: ${it.javaClass.simpleName}: ${it.message}")
        }

        // زر التطبيق الرئيسي لا يلتقط الشاشة أبدًا.
        // التقاط الشاشة يتم فقط من CaptureActivity التي يفتحها الزر العائم.
        finish()
    }
}