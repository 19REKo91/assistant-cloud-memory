package com.raiq.visionbridge

import android.app.*
import android.content.*
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.TextView

class OverlayService : Service() {
    private lateinit var wm: WindowManager
    private var bubble: View? = null
    private val action = "com.raiq.visionbridge.SHOW_BUBBLE"

    override fun onCreate() {
        super.onCreate()
        showBubble()
    }

    private fun showBubble() {
        if (bubble != null || !Settings.canDrawOverlays(this)) return
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        val v = TextView(this).apply {
            text = "看"
            textSize = 18f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.DKGRAY)
            gravity = Gravity.CENTER
            setPadding(18, 10, 18, 10)
            setOnClickListener {
                val i = Intent(this@OverlayService, MainActivity::class.java).apply {
                    action = action
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(i)
            }
        }
        val type = if (Build.VERSION.SDK_INT >= 26)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else WindowManager.LayoutParams.TYPE_PHONE
        val p = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 30
            y = 250
        }
        v.setOnTouchListener(object : View.OnTouchListener {
            var downX=0f; var downY=0f; var startX=0; var startY=0; var moved=false
            override fun onTouch(view: View, e: MotionEvent): Boolean {
                when(e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        downX=e.rawX; downY=e.rawY; startX=p.x; startY=p.y; moved=false
                        return false
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx=(e.rawX-downX).toInt(); val dy=(e.rawY-downY).toInt()
                        if (kotlin.math.abs(dx)>8 || kotlin.math.abs(dy)>8) moved=true
                        if (moved) {
                            p.x=startX+dx; p.y=startY+dy
                            wm.updateViewLayout(view,p)
                        }
                        return moved
                    }
                }
                return false
            }
        })
        bubble=v
        wm.addView(v,p)
    }

    private val receiver=object : BroadcastReceiver() {
        override fun onReceive(c: Context?, i: Intent?) {
            if (i?.action=="com.raiq.visionbridge.HIDE_BUBBLE") hideBubble()
            if (i?.action==action) showBubble()
        }
    }

    private fun hideBubble() {
        bubble?.let { runCatching { wm.removeView(it) } }
        bubble=null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action==action) showBubble()
        return START_STICKY
    }

    override fun onDestroy() {
        hideBubble()
        super.onDestroy()
    }
    override fun onBind(intent: Intent?) = null
}
