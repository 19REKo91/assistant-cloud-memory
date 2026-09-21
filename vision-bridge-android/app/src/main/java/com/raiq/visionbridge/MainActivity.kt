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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(View(this).apply { setBackgroundColor(Color.TRANSPARENT) })

        if (!Settings.canDrawOverlays(this)) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")))
            return
        }

        startService(Intent(this, OverlayService::class.java))
        if (intent?.action == "com.raiq.visionbridge.SHOW_BUBBLE") {
            requestCapture()
        }
    }

    private fun requestCapture() {
        val mgr = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        startActivityForResult(mgr.createScreenCaptureIntent(), requestCode)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == this.requestCode && resultCode == RESULT_OK && data != null) {
            val i = Intent(this, CaptureService::class.java).apply {
                putExtra("resultCode", resultCode)
                putExtra("data", data)
            }
            startForegroundService(i)
        } else if (requestCode == this.requestCode) {
            Toast.makeText(this, "لم تتم الموافقة على التقاط الشاشة", Toast.LENGTH_SHORT).show()
        }
        finish()
    }
}
