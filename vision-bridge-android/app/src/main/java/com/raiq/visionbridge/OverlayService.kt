package com.raiq.visionbridge

import android.app.*
import android.content.*
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.LinearLayout
import android.widget.TextView

class OverlayService : Service() {
    private lateinit var wm: WindowManager
    private var container: View? = null
    private var logView: TextView? = null
    private val action = "com.raiq.visionbridge.SHOW_BUBBLE"
    private val logAction = "com.raiq.visionbridge.DIAGNOSTIC_LOG"

    override fun onCreate() {
        super.onCreate()
        registerReceiver(logReceiver, IntentFilter(logAction), RECEIVER_NOT_EXPORTED)
        showBubble()
        appendLog("✓ التطبيق بدأ / OverlayService")
    }

    private fun showBubble() {
        if (container != null || !Settings.canDrawOverlays(this)) return
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(4, 4, 4, 4)
            setBackgroundColor(Color.argb(210, 35, 35, 35))
        }
        val button = TextView(this).apply {
            text = "شوف الشاشة"
            textSize = 16f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.DKGRAY)
            gravity = Gravity.CENTER
            setPadding(18, 12, 18, 12)
            setOnClickListener {
                appendLog("→ الضغط على شوف الشاشة")
                val i = Intent(this@OverlayService, MainActivity::class.java).apply {
                    action = action
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                }
                startActivity(i)
            }
        }
        logView = TextView(this).apply {
            text = "السجل: جاهز"
            textSize = 11f
            setTextColor(Color.WHITE)
            setPadding(8, 6, 8, 6)
            maxLines = 8
        }
        root.addView(button)
        root.addView(logView)
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
        root.setOnTouchListener(object : View.OnTouchListener {
            var downX=0f; var downY=0f; var startX=0; var startY=0; var moved=false
            override fun onTouch(view: View, e: MotionEvent): Boolean {
                when(e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        downX=e.rawX; downY=e.rawY; startX=p.x; startY=p.y; moved=false
                        return false
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx=(e.rawX-downX).toInt()
                        val dy=(e.rawY-downY).toInt()
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
        container=root
        wm.addView(root,p)
    }

    private val logReceiver=object : BroadcastReceiver() {
        override fun onReceive(c: Context?, i: Intent?) {
            i?.getStringExtra("message")?.let { appendLog(it) }
        }
    }

    private fun appendLog(message: String) {
        val current=logView?.text?.toString().orEmpty()
        logView?.text=(current.lines()+message).takeLast(8).joinToString("\n")
    }

    private fun hideBubble() {
        container?.let { runCatching { wm.removeView(it) } }
        container=null
        logView=null
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action==action) showBubble()
        return START_STICKY
    }

    override fun onDestroy() {
        runCatching { unregisterReceiver(logReceiver) }
        hideBubble()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?) = null
}
