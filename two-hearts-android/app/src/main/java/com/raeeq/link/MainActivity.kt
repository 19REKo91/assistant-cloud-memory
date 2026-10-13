package com.raeeq.link

import android.Manifest
import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.annotation.SuppressLint
import androidx.activity.ComponentActivity
import android.app.AlertDialog
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Intent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.IntentFilter
import android.os.Build
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.ParcelUuid
import android.os.SystemClock
import android.provider.Settings
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import java.text.SimpleDateFormat
import java.util.ArrayDeque
import java.util.Date
import java.util.EnumMap
import java.util.Locale

class MainActivity : ComponentActivity() {
    private data class ScanEvent(
        val elapsedMs: Long,
        val rssi: Int,
        val uuids: List<String>,
        val active: Boolean,
        val radio: Boolean
    )
    companion object {
        private const val REQUEST_BLUETOOTH = 3101
        private const val REQUEST_CAMERA = 3102
        private const val KEY_SIDE_A = "side_a"
        private const val KEY_SIDE_B = "side_b"
        private const val KEY_ROLE = "role"
        private const val KEY_ACTIVE = "active"
        private const val KEY_LAST_RECEIVED_MESSAGE = "last_received_message"
    }

    private val handler = Handler(Looper.getMainLooper())
    private val qrScanLauncher = registerForActivityResult(ScanContract()) { result ->
        handleQrScanResult(result.contents)
    }
    private val preferences by lazy { getSharedPreferences("link_pair", MODE_PRIVATE) }
    private val proximity = ProximityEngine()
    private lateinit var root: LinearLayout
    private lateinit var scene: TextView
    private lateinit var status: TextView
    private lateinit var detail: TextView
    private lateinit var diagnostic: TextView
    private lateinit var qrImage: ImageView
    private lateinit var createButton: Button
    private lateinit var scanButton: Button
    private lateinit var activateButton: Button
    private lateinit var hideQrButton: Button
    private lateinit var showQrButton: Button
    private lateinit var stopButton: Button
    private lateinit var connectionButton: Button
    private lateinit var messageInput: EditText
    private lateinit var sendMessageButton: Button
    private lateinit var messageInbox: TextView
    private lateinit var resetButton: Button
    private lateinit var bluetoothSettingsButton: Button

    private var pair: PairingPayload? = null
    private var role: String? = null
    private var showingQr = false
    private var showDiagnostics = false
    private var active = false
    private var displayedProximityState = ProximityState.WAITING
    private var serviceDiagnostic = ""
    private var serviceReceiverRegistered = false
    private val serviceUpdateReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == LinkProximityService.ACTION_CONNECTION_RESULT) {
                val result = intent.getStringExtra(LinkProximityService.EXTRA_CONNECTION_RESULT).orEmpty()
                if (result.isNotBlank()) Toast.makeText(this@MainActivity, result, Toast.LENGTH_LONG).show()
                return
            }
            if (intent?.action == LinkProximityService.ACTION_MESSAGE_RECEIVED) {
                val message = intent.getStringExtra(LinkProximityService.EXTRA_MESSAGE).orEmpty()
                if (message.isNotBlank()) {
                    messageInbox.text = "آخر رسالة مستلمة: $message"
                    Toast.makeText(this@MainActivity, "رسالة من الهاتف المرتبط: $message", Toast.LENGTH_LONG).show()
                }
                return
            }
            if (intent?.action != LinkProximityService.ACTION_UPDATE) return
            displayedProximityState = runCatching {
                ProximityState.valueOf(intent.getStringExtra(LinkProximityService.EXTRA_STATE) ?: ProximityState.WAITING.name)
            }.getOrDefault(ProximityState.WAITING)
            active = intent.getBooleanExtra(LinkProximityService.EXTRA_ACTIVE, false)
            isRadioRunning = active
            latestRadioError = intent.getStringExtra(LinkProximityService.EXTRA_ERROR)
            serviceDiagnostic = intent.getStringExtra(LinkProximityService.EXTRA_DIAGNOSTICS).orEmpty()
            preferences.edit().putBoolean(KEY_ACTIVE, active).apply()
            if (!active) window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            if (!::status.isInitialized) return
            if (active) updateInteractionUi() else renderScreen()
        }
    }
    private var latestRadioError: String? = null
    private var latestAdvertiseError: String? = null
    private var latestScanError: String? = null
    private var radioStarts = 0
    private var radioStartElapsed: Long = 0L
    private val recentScanEvents = ArrayDeque<ScanEvent>(3)
    private val timingEvents = ArrayDeque<String>(12)
    private var firstPartnerMatchElapsedMs: Long? = null
    private var firstStrongRssiElapsedMs: Long? = null
    private var diagnosticLocalUuid: String? = null
    private var diagnosticPartnerUuid: String? = null
    private var lastRssi: Int? = null
    private var lastRssiElapsedMs: Long? = null
    private var lastMatchElapsedMs: Long? = null
    private var isRadioRunning = false
    private var scanResultsSeen = 0
    private var partnerMatches = 0
    // Raw ScanResult deliveries are counted separately from results accepted by the UI state.
    private var rawScanResultsReceived = 0
    private var resultsWithoutScanRecord = 0
    private var resultsWithoutServiceUuids = 0
    private var scanStartedAtMs: Long? = null
    private var advertisingStatus = "لم يبدأ"
    private var scanningStatus = "لم يبدأ"
    private var scanner: BluetoothLeScanner? = null
    private var advertiser: BluetoothLeAdvertiser? = null
    private var scanCallback: ScanCallback? = null
    private var advertiseCallback: AdvertiseCallback? = null
    private var toneGenerator: ToneGenerator? = null
    private var pulseAnimator: AnimatorSet? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(24, 29, 44)
        window.navigationBarColor = Color.rgb(24, 29, 44)
        loadPair()
        buildUi()
        preferences.getString(KEY_LAST_RECEIVED_MESSAGE, null)?.takeIf { it.isNotBlank() }?.let {
            messageInbox.text = "آخر رسالة مستلمة: $it"
        }
        renderScreen()
    }

    override fun onStart() {
        super.onStart()
        if (!serviceReceiverRegistered) {
            val filter = IntentFilter().apply {
                addAction(LinkProximityService.ACTION_UPDATE)
                addAction(LinkProximityService.ACTION_CONNECTION_RESULT)
                addAction(LinkProximityService.ACTION_MESSAGE_RECEIVED)
            }
            if (Build.VERSION.SDK_INT >= 33) {
                registerReceiver(serviceUpdateReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
            } else {
                @Suppress("DEPRECATION")
                registerReceiver(serviceUpdateReceiver, filter)
            }
            serviceReceiverRegistered = true
        }
        // Respect Stop from the ongoing notification even if this Activity missed its broadcast.
        if (!preferences.getBoolean(KEY_ACTIVE, false)) {
            active = false
            isRadioRunning = false
            displayedProximityState = ProximityState.WAITING
        }
    }

    override fun onStop() {
        if (serviceReceiverRegistered) {
            unregisterReceiver(serviceUpdateReceiver)
            serviceReceiverRegistered = false
        }
        super.onStop()
    }

    override fun onResume() {
        super.onResume()
        if (active && pair != null) {
            if (hasBluetoothPermissions()) {
                if (!startRadio()) {
                    active = false
                    window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                    renderScreen()
                } else {
                    window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                }
            } else {
                active = false
                latestRadioError = "امنح أذونات الأجهزة القريبة ثم فعّل التجربة."
                renderScreen()
            }
        }
    }

    override fun onPause() {
        // BLE is owned by the foreground service; pausing the UI must not end the session.
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        super.onPause()
    }

    override fun onDestroy() {
        // Keep the active BLE session in its service until the user explicitly stops it.
        if (!active) stopRadio()
        pulseAnimator?.cancel()
        super.onDestroy()
    }

    private fun loadPair() {
        val a = preferences.getString(KEY_SIDE_A, null)
        val b = preferences.getString(KEY_SIDE_B, null)
        val savedRole = preferences.getString(KEY_ROLE, null)
        active = preferences.getBoolean(KEY_ACTIVE, false)
        if (a != null && b != null && (savedRole == "A" || savedRole == "B")) {
            pair = PairingPayload.parse("TWOHEARTS|1|$a|$b")
            role = if (pair != null) savedRole else null
        }
        if (pair == null) active = false
    }

    private fun buildUi() {
        val scroll = ScrollView(this)
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(24), dp(22), dp(24), dp(24))
            background = GradientDrawable(GradientDrawable.Orientation.TL_BR,
                intArrayOf(Color.rgb(22, 27, 43), Color.rgb(45, 39, 65)))
        }
        scroll.addView(root, ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        setContentView(scroll)

        val header = TextView(this).apply {
            text = "LINK"
            setTextColor(Color.rgb(235, 239, 247))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 17f)
            letterSpacing = 0.22f
            gravity = Gravity.CENTER
            setTypeface(typeface, Typeface.BOLD)
            setOnLongClickListener {
                showDiagnostics = !showDiagnostics
                diagnostic.visibility = if (showDiagnostics) View.VISIBLE else View.GONE
                updateDiagnostic()
                true
            }
        }
        addFixed(header, 36)

        val intro = TextView(this).apply {
            text = "تجربة محلية بين هاتفين"
            setTextColor(Color.rgb(174, 184, 203))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            gravity = Gravity.CENTER
        }
        addFixed(intro, 30)

        scene = TextView(this).apply {
            text = "○"
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 78f)
            gravity = Gravity.CENTER
        }
        addFixed(scene, 136)

        status = TextView(this).apply {
            text = "جاهز"
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 26f)
            setTypeface(typeface, Typeface.BOLD)
            gravity = Gravity.CENTER
        }
        addFixed(status, 48)

        detail = TextView(this).apply {
            text = "يمكن ربط الهاتفين مرة واحدة ثم استخدامهما دون إنترنت."
            setTextColor(Color.rgb(218, 222, 235))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(8), dp(8), dp(8))
        }
        root.addView(detail, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))

        diagnostic = TextView(this).apply {
            text = ""
            setTextColor(Color.rgb(173, 203, 226))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            gravity = Gravity.CENTER
            visibility = View.GONE
        }
        root.addView(diagnostic, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = dp(8); bottomMargin = dp(8)
        })

        qrImage = ImageView(this).apply {
            visibility = View.GONE
            adjustViewBounds = true
            scaleType = ImageView.ScaleType.FIT_CENTER
            setPadding(dp(8), dp(8), dp(8), dp(8))
            setBackgroundColor(Color.WHITE)
            contentDescription = "رمز الاقتران"
        }
        root.addView(qrImage, LinearLayout.LayoutParams(dp(248), dp(248)).apply {
            topMargin = dp(12); bottomMargin = dp(8)
        })

        createButton = makeButton("إنشاء رمز الاقتران", true) { createPair() }
        scanButton = makeButton("مسح رمز الهاتف الآخر", false) { requestCameraAndScan() }
        activateButton = makeButton("تفعيل التجربة", true) { requestBluetoothAndActivate() }
        hideQrButton = makeButton("إخفاء الرمز", false) { showingQr = false; renderScreen() }
        showQrButton = makeButton("إظهار رمز نقل الاقتران", false) { showPairingTransferQr() }
        connectionButton = makeButton("اختبار الاتصال بالهاتف الآخر", true) {
            if (!active) {
                Toast.makeText(this, "فعّل التجربة على الهاتفين أولًا.", Toast.LENGTH_LONG).show()
            } else {
                Toast.makeText(this, "جارٍ اختبار الاتصال بالهاتف الآخر…", Toast.LENGTH_SHORT).show()
                startService(Intent(this, LinkProximityService::class.java).setAction(LinkProximityService.ACTION_TEST_CONNECTION))
            }
        }
        messageInput = EditText(this).apply {
            hint = "اكتب رسالة قصيرة للهاتف المرتبط"
            setTextColor(Color.WHITE)
            setHintTextColor(Color.rgb(174, 184, 203))
            textSize = 15f
            maxLines = 3
            setPadding(dp(14), dp(10), dp(14), dp(10))
            background = GradientDrawable().apply {
                cornerRadius = dp(12).toFloat()
                setColor(Color.rgb(53, 49, 70))
            }
        }
        root.addView(messageInput, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(12) })
        messageInbox = TextView(this).apply {
            text = "لا توجد رسائل مستلمة بعد."
            setTextColor(Color.rgb(218, 222, 235))
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            setPadding(dp(4), dp(8), dp(4), dp(4))
        }
        root.addView(messageInbox, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        sendMessageButton = makeButton("إرسال رسالة للهاتف الآخر", true) {
            val message = messageInput.text?.toString()?.trim().orEmpty()
            if (!active) {
                Toast.makeText(this, "فعّل LINK على الهاتفين أولًا.", Toast.LENGTH_LONG).show()
            } else if (message.isBlank()) {
                Toast.makeText(this, "اكتب رسالة أولًا.", Toast.LENGTH_SHORT).show()
            } else if (message.toByteArray(Charsets.UTF_8).size > 180) {
                Toast.makeText(this, "اجعل الرسالة أقصر من 180 بايت.", Toast.LENGTH_LONG).show()
            } else {
                startService(Intent(this, LinkProximityService::class.java)
                    .setAction(LinkProximityService.ACTION_SEND_MESSAGE)
                    .putExtra(LinkProximityService.EXTRA_MESSAGE, message))
                Toast.makeText(this, "جارٍ إرسال الرسالة…", Toast.LENGTH_SHORT).show()
            }
        }
        stopButton = makeButton("إيقاف التجربة", false) {
            active = false
            preferences.edit().putBoolean(KEY_ACTIVE, false).apply()
            latestRadioError = null
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            stopRadio()
            proximity.reset()
            displayedProximityState = ProximityState.WAITING
            renderScreen()
        }
        resetButton = makeButton("إعادة الاقتران", false) { confirmResetPair() }
        bluetoothSettingsButton = makeButton("فتح إعدادات البلوتوث", false) {
            startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
        }
        listOf(createButton, scanButton, activateButton, hideQrButton, showQrButton, connectionButton,
            sendMessageButton, stopButton, resetButton, bluetoothSettingsButton).forEach(::addButton)
    }

    private fun addFixed(view: View, heightDp: Int) {
        root.addView(view, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(heightDp)))
    }
    private fun addButton(button: Button) {
        root.addView(button, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(9) })
    }
    private fun makeButton(label: String, prominent: Boolean, action: () -> Unit): Button =
        Button(this).apply {
            text = label; isAllCaps = false; textSize = 15f; setTextColor(Color.WHITE)
            setPadding(dp(16), dp(10), dp(16), dp(10))
            background = GradientDrawable().apply {
                cornerRadius = dp(17).toFloat()
                setColor(if (prominent) Color.rgb(187, 70, 113) else Color.rgb(62, 70, 94))
            }
            setOnClickListener { action() }
        }

    private fun renderScreen() {
        createButton.visibility = if (pair == null) View.VISIBLE else View.GONE
        scanButton.visibility = if (pair == null) View.VISIBLE else View.GONE
        activateButton.visibility = if (pair != null && !active) View.VISIBLE else View.GONE
        stopButton.visibility = if (active) View.VISIBLE else View.GONE
        connectionButton.visibility = if (active) View.VISIBLE else View.GONE
        resetButton.visibility = if (pair != null && !active) View.VISIBLE else View.GONE
        bluetoothSettingsButton.visibility =
            if (!active && latestRadioError != null && latestRadioError!!.contains("البلوتوث")) View.VISIBLE else View.GONE
        val qrVisible = pair != null && showingQr && !active
        qrImage.visibility = if (qrVisible) View.VISIBLE else View.GONE
        hideQrButton.visibility = if (qrVisible) View.VISIBLE else View.GONE
        showQrButton.visibility = if (pair != null && !active && !showingQr) View.VISIBLE else View.GONE

        if (active) { updateInteractionUi(); return }
        stopPulse()
        scene.text = "○"
        scene.setTextColor(Color.rgb(221, 227, 239))
        status.text = if (pair == null) "غير مرتبط" else "الاقتران محفوظ"
        status.setTextColor(Color.WHITE)
        detail.text = when {
            latestRadioError != null -> latestRadioError
            pair == null -> "اربط الهاتفين مرة واحدة برمز QR. بعد ذلك يعمل التفاعل محليًا، دون إنترنت."
            qrVisible -> "امسح هذا الرمز من الهاتف الآخر مرة واحدة. احتفظ بالتطبيق مفتوحًا حتى ينتهي الإعداد."
            else -> "التهيئة جاهزة. فعّل التجربة على الهاتفين عندما يحين الوقت."
        }
        updateDiagnostic()
    }

    private fun updateInteractionUi() {
        if (latestRadioError != null) {
            status.text = "تعذر تشغيل الاتصال"; detail.text = latestRadioError
            stopPulse(); scene.text = "!"; scene.setTextColor(Color.rgb(245, 199, 117)); return
        }
        when (displayedProximityState) {
            ProximityState.WAITING -> {
                root.background = GradientDrawable(GradientDrawable.Orientation.TL_BR,
                    intArrayOf(Color.rgb(22, 27, 43), Color.rgb(45, 39, 65)))
                scene.text = "○"; scene.setTextColor(Color.rgb(221, 227, 239))
                status.text = "بانتظار الاقتراب"; detail.text = "عندما يقترب الهاتف المرتبط، يبدأ التفاعل تلقائيًا."
                stopPulse()
            }
            ProximityState.NEAR -> {
                root.setBackgroundColor(Color.rgb(105, 37, 70))
                scene.text = "💞"; scene.setTextColor(Color.WHITE)
                status.text = "معًا الآن"; detail.text = "اقتربنا…"; startPulse()
            }
            ProximityState.APART -> {
                root.setBackgroundColor(Color.rgb(35, 52, 76))
                scene.text = "💔"; scene.setTextColor(Color.WHITE)
                status.text = "أفتقدك"; detail.text = "تأكد الفراق بعد 10 ثوانٍ. سأنتظر عودتك."
                stopPulse()
            }
        }
        updateDiagnostic()
    }

    private fun startPulse() {
        if (pulseAnimator != null) return
        val sx = ObjectAnimator.ofFloat(scene, "scaleX", 1f, 1.12f, 1f).apply {
            duration = 900L; repeatCount = ValueAnimator.INFINITE
        }
        val sy = ObjectAnimator.ofFloat(scene, "scaleY", 1f, 1.12f, 1f).apply {
            duration = 900L; repeatCount = ValueAnimator.INFINITE
        }
        pulseAnimator = AnimatorSet().apply { playTogether(sx, sy); start() }
    }
    private fun stopPulse() {
        pulseAnimator?.cancel(); pulseAnimator = null
        if (::scene.isInitialized) { scene.scaleX = 1f; scene.scaleY = 1f }
    }
    private fun onTransition(next: ProximityState) {
        displayedProximityState = next
        updateInteractionUi()
    }

    private fun createPair() {
        val payload = PairingPayload.create()
        pair = payload; role = "A"; showingQr = true; active = false; latestRadioError = null
        savePair(payload, "A")
        try {
            renderQrBitmap(payload.encode())
            renderScreen()
        } catch (_: Exception) {
            latestRadioError = "تعذّر إنشاء رمز الاقتران. أعد الاقتران وحاول مرة أخرى."
            renderScreen()
        }
    }

    private fun showPairingTransferQr() {
        val savedPair = pair ?: return
        val senderRole = role ?: return
        val receiverRole = if (senderRole == "A") "B" else "A"
        showingQr = true
        latestRadioError = null
        try {
            renderQrBitmap(savedPair.encodeForReceiverRole(receiverRole))
            renderScreen()
        } catch (_: Exception) {
            showingQr = false
            latestRadioError = "تعذّر إنشاء رمز نقل الاقتران."
            renderScreen()
        }
    }

    private fun renderQrBitmap(contents: String) {
        val hints = EnumMap<EncodeHintType, Any>(EncodeHintType::class.java)
        hints[EncodeHintType.MARGIN] = 3
        val matrix = QRCodeWriter().encode(contents, BarcodeFormat.QR_CODE, 520, 520, hints)
        val bitmap = Bitmap.createBitmap(520, 520, Bitmap.Config.ARGB_8888)
        for (x in 0 until 520) for (y in 0 until 520) {
            bitmap.setPixel(x, y, if (matrix[x, y]) Color.BLACK else Color.WHITE)
        }
        qrImage.setImageBitmap(bitmap)
    }

    private fun requestCameraAndScan() {
        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) startQrScan()
        else requestPermissions(arrayOf(Manifest.permission.CAMERA), REQUEST_CAMERA)
    }
    private fun startQrScan() {
        val options = ScanOptions().apply {
            setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            setPrompt("امسح رمز الاقتران من الهاتف الأول")
            setBeepEnabled(false)
            setOrientationLocked(true)
        }
        try {
            qrScanLauncher.launch(options)
        } catch (error: Exception) {
            Toast.makeText(
                this,
                "تعذّر فتح الماسح: ${error.localizedMessage ?: "خطأ غير معروف"}",
                Toast.LENGTH_LONG
            ).show()
        }
    }
    private fun handleQrScanResult(contents: String?) {
        if (contents == null) {
            Toast.makeText(this, "تم إلغاء المسح.", Toast.LENGTH_SHORT).show()
            return
        }
        val payload = PairingPayload.parse(contents)
        if (payload == null) {
            Toast.makeText(this, "هذا الرمز ليس رمز اقتران صالحًا.", Toast.LENGTH_LONG).show()
        } else {
            val assignedRole = payload.receiverRole ?: "B"
            val savedPayload = PairingPayload(payload.sideA, payload.sideB)
            pair = savedPayload
            role = assignedRole
            showingQr = false
            active = false
            preferences.edit().putBoolean(KEY_ACTIVE, false).apply()
            latestRadioError = null
            savePair(savedPayload, assignedRole)
            renderScreen()
            val confirmation = if (payload.receiverRole == null) {
                "تم حفظ الاقتران على هذا الهاتف."
            } else {
                "تم نقل الاقتران المحفوظ إلى هذا الهاتف."
            }
            Toast.makeText(this, confirmation, Toast.LENGTH_LONG).show()
        }
    }
    private fun savePair(payload: PairingPayload, savedRole: String) {
        preferences.edit().putString(KEY_SIDE_A, payload.sideA).putString(KEY_SIDE_B, payload.sideB)
            .putString(KEY_ROLE, savedRole).putBoolean(KEY_ACTIVE, false).apply()
    }
    private fun confirmResetPair() {
        AlertDialog.Builder(this).setTitle("إعادة الاقتران")
            .setMessage("سيُحذف رمز هذا الهاتف. لإعادة الربط، أنشئ رمزًا جديدًا وامسحه من الهاتف الآخر.")
            .setNegativeButton("إلغاء", null)
            .setPositiveButton("حذف") { _, _ ->
                active = false
                preferences.edit().putBoolean(KEY_ACTIVE, false).apply()
                stopRadio()
                pair = null; role = null
                displayedProximityState = ProximityState.WAITING
                window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                showingQr = false; latestRadioError = null; proximity.reset()
                preferences.edit().clear().apply(); renderScreen()
            }.show()
    }
    private fun requestBluetoothAndActivate() {
        latestRadioError = null
        if (!hasBluetoothPermissions()) {
            requestPermissions(arrayOf(Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_ADVERTISE, Manifest.permission.BLUETOOTH_CONNECT), REQUEST_BLUETOOTH)
            return
        }
        activateExperience()
    }
    private fun hasBluetoothPermissions(): Boolean =
        checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED &&
        checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE) == PackageManager.PERMISSION_GRANTED &&
        checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CAMERA) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) startQrScan()
            else Toast.makeText(this, "يلزم إذن الكاميرا لمسح رمز الاقتران فقط.", Toast.LENGTH_LONG).show()
        } else if (requestCode == REQUEST_BLUETOOTH) {
            if (hasBluetoothPermissions()) activateExperience()
            else { latestRadioError = "لم تُمنح أذونات الأجهزة القريبة."; renderScreen() }
        }
    }
    private fun activateExperience() {
        latestRadioError = null
        proximity.reset()
        displayedProximityState = ProximityState.WAITING
        active = true
        preferences.edit().putBoolean(KEY_ACTIVE, true).apply()
        if (!startRadio()) {
            active = false
            preferences.edit().putBoolean(KEY_ACTIVE, false).apply()
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        } else {
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
        renderScreen()
    }

    private fun startRadio(): Boolean {
        val payload = pair ?: return false
        val savedRole = role ?: return false
        if (!hasBluetoothPermissions()) {
            latestRadioError = "امنح أذونات الأجهزة القريبة ثم فعّل التجربة."
            return false
        }
        val serviceIntent = Intent(this, LinkProximityService::class.java).apply {
            action = LinkProximityService.ACTION_START
            putExtra(LinkProximityService.EXTRA_LOCAL_UUID, payload.ownUuid(savedRole).toString())
            putExtra(LinkProximityService.EXTRA_PARTNER_UUID, payload.partnerUuid(savedRole).toString())
        }
        return try {
            startForegroundService(serviceIntent)
            latestRadioError = null
            isRadioRunning = true
            true
        } catch (error: Exception) {
            latestRadioError = "تعذّر بدء مراقبة LINK في الخلفية: ${error.localizedMessage ?: error.javaClass.simpleName}"
            isRadioRunning = false
            stopService(Intent(this, LinkProximityService::class.java))
            false
        }
    }

    private fun stopRadio() {
        stopService(Intent(this, LinkProximityService::class.java))
        isRadioRunning = false
    }

    private fun updateDiagnostic() {
        if (!::diagnostic.isInitialized) return
        diagnostic.visibility = if (showDiagnostics) View.VISIBLE else View.GONE
        diagnostic.text = serviceDiagnostic.ifBlank {
            "سيظهر تشخيص خدمة BLE هنا بعد تفعيل التجربة."
        }
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
 

/**
 * Owns the BLE radio independently of MainActivity, so proximity keeps running while UI is paused.
 */
class LinkProximityService : android.app.Service() {
    companion object {
        const val ACTION_START="com.raeeq.link.action.START_PROXIMITY"
        const val ACTION_STOP="com.raeeq.link.action.STOP_PROXIMITY"
        const val ACTION_TEST_CONNECTION="com.raeeq.link.action.TEST_CONNECTION"
        const val ACTION_SEND_MESSAGE="com.raeeq.link.action.SEND_MESSAGE"
        const val ACTION_MESSAGE_RECEIVED="com.raeeq.link.action.MESSAGE_RECEIVED"
        const val ACTION_UPDATE="com.raeeq.link.action.PROXIMITY_UPDATE"
        const val ACTION_CONNECTION_RESULT="com.raeeq.link.action.CONNECTION_RESULT"
        const val EXTRA_CONNECTION_RESULT="connection_result"
        const val EXTRA_MESSAGE="message"
        const val EXTRA_LOCAL_UUID="local_uuid"
        const val EXTRA_PARTNER_UUID="partner_uuid"
        const val EXTRA_STATE="state"
        const val EXTRA_ACTIVE="active"
        const val EXTRA_ERROR="error"
        const val EXTRA_DIAGNOSTICS="diagnostics"
        private const val CHANNEL="link_proximity_active"
        private const val NOTIFICATION_ID=6105
        private val PROBE_SERVICE_UUID=java.util.UUID.fromString("6b4e1000-1d4a-4f20-9f30-11c0a2e0b001")
        private val PROBE_CHARACTERISTIC_UUID=java.util.UUID.fromString("6b4e1001-1d4a-4f20-9f30-11c0a2e0b001")
    }
    private val mainHandler=android.os.Handler(android.os.Looper.getMainLooper())
    private val engine=ProximityEngine()
    private val events=java.util.ArrayDeque<String>(8)
    private var running=false
    private var localUuid:java.util.UUID?=null
    private var partnerUuid:java.util.UUID?=null
    private var advertiser:android.bluetooth.le.BluetoothLeAdvertiser?=null
    private var scanner:android.bluetooth.le.BluetoothLeScanner?=null
    private var advertiseCb:android.bluetooth.le.AdvertiseCallback?=null
    private var scanCb:android.bluetooth.le.ScanCallback?=null
    private var startElapsed=0L
    private var lastPublished=0L
    private var rawResults=0
    private var partnerMatches=0
    private var lastRssi:Int?=null
    private var firstMatch:Long?=null
    private var firstStrong:Long?=null
    private var latestError:String?=null
    private var latestPartnerDevice:android.bluetooth.BluetoothDevice?=null
    private var gattServer:android.bluetooth.BluetoothGattServer?=null
    private var clientGatt:android.bluetooth.BluetoothGatt?=null
    private var connectionTestPending=false
    private var pendingMessage:String?=null
    private var messageWriteRetryCount=0
    private var bluetoothReceiverRegistered=false

    private val bluetoothStateReceiver=object:android.content.BroadcastReceiver() {
        override fun onReceive(context:android.content.Context?,intent:android.content.Intent?) {
            if(intent?.action!=android.bluetooth.BluetoothAdapter.ACTION_STATE_CHANGED) return
            when(intent.getIntExtra(android.bluetooth.BluetoothAdapter.EXTRA_STATE,android.bluetooth.BluetoothAdapter.ERROR)) {
                android.bluetooth.BluetoothAdapter.STATE_OFF -> {
                    if(running) {
                        stopRadio()
                        engine.reset()
                        latestError="البلوتوث متوقف مؤقتًا؛ سيستأنف LINK تلقائيًا عند تشغيله."
                        note("Bluetooth off; waiting for radio",android.os.SystemClock.elapsedRealtime())
                        publish()
                    }
                }
                android.bluetooth.BluetoothAdapter.STATE_ON -> {
                    val local=localUuid
                    val partner=partnerUuid
                    if(local!=null && partner!=null && running) {
                        running=false
                        latestError=null
                        note("Bluetooth on; restarting BLE",android.os.SystemClock.elapsedRealtime())
                        startSession(local,partner)
                    }
                }
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        val filter=android.content.IntentFilter(android.bluetooth.BluetoothAdapter.ACTION_STATE_CHANGED)
        if(android.os.Build.VERSION.SDK_INT>=33) {
            registerReceiver(bluetoothStateReceiver,filter,android.content.Context.RECEIVER_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(bluetoothStateReceiver,filter)
        }
        bluetoothReceiverRegistered=true
    }

    private val serverCallback=object:android.bluetooth.BluetoothGattServerCallback() {
        override fun onConnectionStateChange(device:android.bluetooth.BluetoothDevice,status:Int,newState:Int) {
            if(status==android.bluetooth.BluetoothGatt.GATT_SUCCESS &&
                newState==android.bluetooth.BluetoothProfile.STATE_CONNECTED) {
                note("connection test client connected",android.os.SystemClock.elapsedRealtime())
            } else if(newState==android.bluetooth.BluetoothProfile.STATE_DISCONNECTED) {
                note("connection test client disconnected",android.os.SystemClock.elapsedRealtime())
            }
            publish()
        }
        override fun onCharacteristicReadRequest(
            device:android.bluetooth.BluetoothDevice,requestId:Int,offset:Int,
            characteristic:android.bluetooth.BluetoothGattCharacteristic
        ) {
            if(characteristic.uuid!=PROBE_CHARACTERISTIC_UUID) {
                gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_FAILURE,offset,null)
                return
            }
            val bytes=(localUuid?.toString() ?: "").toByteArray(Charsets.UTF_8)
            if(offset>bytes.size) {
                gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_INVALID_OFFSET,offset,null)
            } else {
                gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_SUCCESS,offset,bytes.copyOfRange(offset,bytes.size))
                note("connection test response sent",android.os.SystemClock.elapsedRealtime())
                publish()
            }
        }
        override fun onCharacteristicWriteRequest(
            device:android.bluetooth.BluetoothDevice,requestId:Int,characteristic:android.bluetooth.BluetoothGattCharacteristic,
            preparedWrite:Boolean,responseNeeded:Boolean,offset:Int,value:ByteArray
        ) {
            val now=android.os.SystemClock.elapsedRealtime()
            if(characteristic.uuid!=PROBE_CHARACTERISTIC_UUID || preparedWrite || offset!=0 || value.size>180) {
                if(responseNeeded) gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_FAILURE,offset,null)
                return
            }
            val message=value.toString(Charsets.UTF_8).trim()
            if(message.isBlank()) {
                if(responseNeeded) gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_FAILURE,offset,null)
                return
            }
            // Persist before acknowledging the GATT write, so a closed Activity cannot lose the inbox update.
            val saved = getSharedPreferences("link_pair", MODE_PRIVATE).edit()
                .putString("last_received_message", message)
                .putLong("last_received_message_at", System.currentTimeMillis())
                .commit()
            if(!saved) {
                if(responseNeeded) gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_FAILURE,offset,null)
                note("message persistence failed",now)
                publish()
                return
            }
            if(responseNeeded) gattServer?.sendResponse(device,requestId,android.bluetooth.BluetoothGatt.GATT_SUCCESS,offset,null)
            sendBroadcast(android.content.Intent(ACTION_MESSAGE_RECEIVED).setPackage(packageName)
                .putExtra(EXTRA_MESSAGE,message))
            note("message received and saved (${value.size} bytes)",now)
            publish()
        }
    }

    private val clientCallback=object:android.bluetooth.BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt:android.bluetooth.BluetoothGatt,status:Int,newState:Int) {
            if(status!=android.bluetooth.BluetoothGatt.GATT_SUCCESS) {
                finishConnectionTest(false,"فشل اتصال BLE (رمز $status).",gatt)
            } else if(newState==android.bluetooth.BluetoothProfile.STATE_CONNECTED) {
                if(!gatt.discoverServices()) finishConnectionTest(false,"اتصل الهاتف، لكن تعذّر فحص خدمة التأكيد.",gatt)
            } else if(newState==android.bluetooth.BluetoothProfile.STATE_DISCONNECTED && connectionTestPending) {
                finishConnectionTest(false,"انقطع الاتصال قبل وصول التأكيد.",gatt)
            }
        }
        override fun onServicesDiscovered(gatt:android.bluetooth.BluetoothGatt,status:Int) {
            if(status!=android.bluetooth.BluetoothGatt.GATT_SUCCESS) {
                finishConnectionTest(false,"تعذّر اكتشاف خدمة تأكيد LINK.",gatt); return
            }
            val characteristic=gatt.getService(PROBE_SERVICE_UUID)?.getCharacteristic(PROBE_CHARACTERISTIC_UUID)
            if(characteristic==null) {
                finishConnectionTest(false,"الهاتف الآخر لا يوفّر خدمة تأكيد LINK.",gatt); return
            }
            if(!gatt.readCharacteristic(characteristic)) finishConnectionTest(false,"تعذّر طلب تأكيد من الهاتف الآخر.",gatt)
        }
        override fun onCharacteristicWrite(
            gatt:android.bluetooth.BluetoothGatt,characteristic:android.bluetooth.BluetoothGattCharacteristic,status:Int
        ) {
            if(characteristic.uuid!=PROBE_CHARACTERISTIC_UUID || pendingMessage==null) return
            if(status==android.bluetooth.BluetoothGatt.GATT_SUCCESS) {
                messageWriteRetryCount=0
                finishConnectionTest(true,"أُرسلت الرسالة إلى الهاتف المرتبط.",gatt)
            } else {
                val message=pendingMessage
                if(status==133 && message!=null && messageWriteRetryCount<1) {
                    messageWriteRetryCount++
                    connectionTestPending=false
                    pendingMessage=null
                    if(clientGatt===gatt) clientGatt=null
                    try { gatt.disconnect() } catch(_:Exception) { }
                    try { gatt.close() } catch(_:Exception) { }
                    sendConnectionResult("تعذّر الإرسال في المحاولة الأولى؛ يعيد LINK المحاولة مرة واحدة…")
                    note("message write failed status=$status; retrying once",android.os.SystemClock.elapsedRealtime())
                    publish()
                    mainHandler.postDelayed({
                        if(running && !connectionTestPending) requestConnectionTest(message,true)
                        else messageWriteRetryCount=0
                    },1000L)
                } else {
                    finishConnectionTest(false,"فشل إرسال الرسالة (رمز $status).",gatt)
                }
            }
        }
        override fun onCharacteristicRead(
            gatt:android.bluetooth.BluetoothGatt,characteristic:android.bluetooth.BluetoothGattCharacteristic,status:Int
        ) {
            if(characteristic.uuid!=PROBE_CHARACTERISTIC_UUID) return
            if(status!=android.bluetooth.BluetoothGatt.GATT_SUCCESS) {
                finishConnectionTest(false,"لم يكتمل طلب التأكيد (رمز $status).",gatt); return
            }
            val remoteUuid=characteristic.value?.toString(Charsets.UTF_8)
            val expected=partnerUuid?.toString()
            if(remoteUuid!=expected) {
                finishConnectionTest(false,"وصل رد، لكن هوية الهاتف لا تطابق الاقتران المحفوظ.",gatt)
            } else {
                val message=pendingMessage
                if(message==null) {
                    finishConnectionTest(true,"نجح الاتصال: استلمنا تأكيد الهاتف المرتبط.",gatt)
                } else {
                    characteristic.writeType=android.bluetooth.BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
                    characteristic.value=message.toByteArray(Charsets.UTF_8)
                    if(!gatt.writeCharacteristic(characteristic)) finishConnectionTest(false,"تم التحقق من الهاتف لكن تعذّر إرسال الرسالة.",gatt)
                }
            }
        }
    }

    private val ticker=object:Runnable {
        override fun run() {
            if(!running) return
            val now=android.os.SystemClock.elapsedRealtime()
            val transition=engine.tick(now)
            if(transition!=null) { note("state=$transition",now); publish() }
            else if(now-lastPublished>=1_000L) publish()
            if(running) mainHandler.postDelayed(this,250L)
        }
    }

    override fun onBind(intent:android.content.Intent?):android.os.IBinder?=null

    override fun onStartCommand(intent:android.content.Intent?,flags:Int,startId:Int):Int {
        when(intent?.action) {
            ACTION_STOP -> { stopSession(); stopSelf(startId) }
            ACTION_TEST_CONNECTION -> requestConnectionTest()
            ACTION_SEND_MESSAGE -> requestConnectionTest(intent.getStringExtra(EXTRA_MESSAGE)?.trim().orEmpty())
            ACTION_START -> {
                val local=intent.getStringExtra(EXTRA_LOCAL_UUID)?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                val partner=intent.getStringExtra(EXTRA_PARTNER_UUID)?.let { runCatching { java.util.UUID.fromString(it) }.getOrNull() }
                if(local==null || partner==null) fail("بيانات الاقتران غير صالحة أو غير مكتملة.")
                else startSession(local,partner)
            }
            else -> if(running) publish() else stopSelf(startId)
        }
        return START_NOT_STICKY
    }

    private fun startSession(local:java.util.UUID,partner:java.util.UUID) {
        if(running && localUuid==local && partnerUuid==partner) { publish(); return }
        if(!hasBluetoothPermissions()) {
            latestError="أذونات البلوتوث غير متاحة؛ افتح LINK وامنح أذونات الأجهزة القريبة."
            running=false; persistActive(false); publish(); stopSelf(); return
        }
        running=false
        stopRadio()
        localUuid=local; partnerUuid=partner
        engine.reset(); latestError=null
        rawResults=0; partnerMatches=0; lastRssi=null; firstMatch=null; firstStrong=null
        events.clear()
        startElapsed=android.os.SystemClock.elapsedRealtime()
        lastPublished=0L
        createChannel()
        running=true
        persistActive(true)
        try {
            startForeground(NOTIFICATION_ID,makeNotification(),
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE)
        } catch(error:Exception) {
            running=false
            persistActive(false)
            latestError="تعذّر تشغيل خدمة LINK في الخلفية: ${error.localizedMessage ?: error.javaClass.simpleName}"
            publish(); stopSelf(); return
        }
        val manager=getSystemService(android.content.Context.BLUETOOTH_SERVICE) as android.bluetooth.BluetoothManager
        val adapter:android.bluetooth.BluetoothAdapter?=manager.adapter
        if(adapter==null) { fail("لا يتوفر محول بلوتوث على هذا الجهاز."); return }
        if(!adapter.isEnabled) {
            latestError="البلوتوث متوقف مؤقتًا؛ سيستأنف LINK تلقائيًا عند تشغيله."
            note("Bluetooth currently off; waiting for radio",android.os.SystemClock.elapsedRealtime())
            publish()
            return
        }
        val localAdvertiser=adapter.bluetoothLeAdvertiser
        val localScanner=adapter.bluetoothLeScanner
        if(localAdvertiser==null || localScanner==null) { fail("لا يتوفر الإعلان أو المسح عبر BLE على هذا الجهاز."); return }
        advertiser=localAdvertiser; scanner=localScanner
        startGattProbe(adapter)
        val advSettings=android.bluetooth.le.AdvertiseSettings.Builder()
            .setAdvertiseMode(android.bluetooth.le.AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(android.bluetooth.le.AdvertiseSettings.ADVERTISE_TX_POWER_MEDIUM)
            .setConnectable(true).setTimeout(0).build()
        val advData=android.bluetooth.le.AdvertiseData.Builder()
            .setIncludeDeviceName(false).setIncludeTxPowerLevel(false)
            .addServiceUuid(android.os.ParcelUuid(local)).build()
        val advertisingCallback=object:android.bluetooth.le.AdvertiseCallback() {
            override fun onStartSuccess(settingsInEffect:android.bluetooth.le.AdvertiseSettings?) { if(running) publish() }
            override fun onStartFailure(errorCode:Int) {
                mainHandler.post {
                    if(running) fail(when(errorCode) {
                        android.bluetooth.le.AdvertiseCallback.ADVERTISE_FAILED_DATA_TOO_LARGE -> "بيانات إعلان BLE أكبر من المسموح."
                        android.bluetooth.le.AdvertiseCallback.ADVERTISE_FAILED_TOO_MANY_ADVERTISERS -> "لا تتوفر خانة إعلان BLE حاليًا."
                        android.bluetooth.le.AdvertiseCallback.ADVERTISE_FAILED_FEATURE_UNSUPPORTED -> "إعلان BLE غير مدعوم على هذا الجهاز."
                        android.bluetooth.le.AdvertiseCallback.ADVERTISE_FAILED_ALREADY_STARTED -> "إعلان BLE بدأ مسبقًا."
                        android.bluetooth.le.AdvertiseCallback.ADVERTISE_FAILED_INTERNAL_ERROR -> "تعذّر بدء إعلان BLE."
                        else -> "فشل إعلان BLE، الرمز: $errorCode"
                    })
                }
            }
        }
        advertiseCb=advertisingCallback
        val scanSettings=android.bluetooth.le.ScanSettings.Builder()
            .setScanMode(android.bluetooth.le.ScanSettings.SCAN_MODE_LOW_LATENCY).build()
        val scanningCallback=object:android.bluetooth.le.ScanCallback() {
            override fun onScanResult(callbackType:Int,result:android.bluetooth.le.ScanResult) { inspect(result,partner) }
            override fun onBatchScanResults(results:MutableList<android.bluetooth.le.ScanResult>) { results.forEach { inspect(it,partner) } }
            override fun onScanFailed(errorCode:Int) { mainHandler.post { if(running) fail("تعذّر البحث عن الهاتف المرتبط، الرمز: $errorCode") } }
        }
        scanCb=scanningCallback
        try {
            localAdvertiser.startAdvertising(advSettings,advData,advertisingCallback)
            // Preserve the old strategy: scan without an OS filter, then match the partner UUID locally.
            localScanner.startScan(null,scanSettings,scanningCallback)
            mainHandler.removeCallbacks(ticker)
            mainHandler.post(ticker)
            note("BLE session started",startElapsed)
            publish()
        } catch(_:SecurityException) {
            fail("لم يسمح النظام باستخدام البلوتوث. راجع أذونات الأجهزة القريبة.")
        } catch(_:IllegalStateException) {
            fail("تعذّر تشغيل BLE. أوقف البلوتوث وشغّله ثم حاول مرة واحدة.")
        } catch(error:Exception) {
            fail("تعذّر تشغيل BLE: ${error.localizedMessage ?: error.javaClass.simpleName}")
        }
    }

    private fun inspect(result:android.bluetooth.le.ScanResult,expected:java.util.UUID) {
        if(!running) return
        rawResults++
        val uuids=result.scanRecord?.serviceUuids
        val now=android.os.SystemClock.elapsedRealtime()
        if(uuids?.contains(android.os.ParcelUuid(expected))==true) {
            latestPartnerDevice=result.device
            partnerMatches++; lastRssi=result.rssi
            if(firstMatch==null) { firstMatch=now-startElapsed; note("first partner match",now) }
            if(result.rssi>=-56 && firstStrong==null) { firstStrong=now-startElapsed; note("first strong RSSI",now) }
            val transition=engine.onRssi(result.rssi,now)
            if(transition!=null) note("state=$transition",now)
            if(transition!=null || now-lastPublished>=400L) publish()
        } else if(now-lastPublished>=1_000L) publish()
    }

    @SuppressLint("MissingPermission")
    private fun startGattProbe(adapter:android.bluetooth.BluetoothAdapter) {
        try {
            val manager=getSystemService(android.content.Context.BLUETOOTH_SERVICE) as android.bluetooth.BluetoothManager
            val server=manager.openGattServer(this,serverCallback)
            if(server==null) { note("GATT server unavailable",android.os.SystemClock.elapsedRealtime()); return }
            val service=android.bluetooth.BluetoothGattService(
                PROBE_SERVICE_UUID,android.bluetooth.BluetoothGattService.SERVICE_TYPE_PRIMARY
            ).apply {
                addCharacteristic(android.bluetooth.BluetoothGattCharacteristic(
                    PROBE_CHARACTERISTIC_UUID,
                    android.bluetooth.BluetoothGattCharacteristic.PROPERTY_READ or android.bluetooth.BluetoothGattCharacteristic.PROPERTY_WRITE,
                    android.bluetooth.BluetoothGattCharacteristic.PERMISSION_READ or android.bluetooth.BluetoothGattCharacteristic.PERMISSION_WRITE
                ))
            }
            gattServer=server
            if(!server.addService(service)) {
                note("GATT service registration failed",android.os.SystemClock.elapsedRealtime())
                server.close(); gattServer=null
            }
        } catch(error:Exception) {
            note("GATT server error: ${error.javaClass.simpleName}",android.os.SystemClock.elapsedRealtime())
        }
    }

    @SuppressLint("MissingPermission")
    private fun requestConnectionTest(message:String?=null,retry:Boolean=false) {
        if(!retry) messageWriteRetryCount=0
        if(!running) { messageWriteRetryCount=0; sendConnectionResult("فعّل LINK على هذا الهاتف أولًا."); return }
        if(!hasBluetoothPermissions()) { messageWriteRetryCount=0; sendConnectionResult("أذونات البلوتوث غير متاحة."); return }
        if(connectionTestPending) { messageWriteRetryCount=0; sendConnectionResult("اختبار الاتصال جارٍ بالفعل."); return }
        val device=latestPartnerDevice
        if(device==null) {
            messageWriteRetryCount=0
            sendConnectionResult("لم يُكتشف الهاتف المرتبط بعد. قرّب الهاتفين وحاول مجددًا.")
            return
        }
        connectionTestPending=true
        pendingMessage=message?.takeIf { it.isNotBlank() }
        sendConnectionResult(if(pendingMessage==null) "جارٍ طلب تأكيد من الهاتف المرتبط…" else "جارٍ الاتصال لإرسال الرسالة…")
        try {
            clientGatt=device.connectGatt(this,false,clientCallback,android.bluetooth.BluetoothDevice.TRANSPORT_LE)
            if(clientGatt==null) finishConnectionTest(false,"تعذّر بدء اتصال BLE.",null)
        } catch(error:Exception) {
            finishConnectionTest(false,"تعذّر بدء الاختبار: ${error.localizedMessage ?: error.javaClass.simpleName}",null)
        }
    }

    @SuppressLint("MissingPermission")
    private fun finishConnectionTest(success:Boolean,message:String,gatt:android.bluetooth.BluetoothGatt?) {
        if(!connectionTestPending && gatt!=null) return
        connectionTestPending=false
        pendingMessage=null
        messageWriteRetryCount=0
        sendConnectionResult(message)
        note(if(success) "connection test success" else "connection test failed",android.os.SystemClock.elapsedRealtime())
        if(gatt!=null) {
            if(clientGatt===gatt) clientGatt=null
            try { gatt.disconnect() } catch(_:Exception) { }
            try { gatt.close() } catch(_:Exception) { }
        }
        publish()
    }

    private fun sendConnectionResult(message:String) {
        sendBroadcast(android.content.Intent(ACTION_CONNECTION_RESULT).setPackage(packageName)
            .putExtra(EXTRA_CONNECTION_RESULT,message))
    }

    @SuppressLint("MissingPermission")
    private fun stopRadio() {
        mainHandler.removeCallbacks(ticker)
        try { clientGatt?.disconnect() } catch(_:Exception) { }
        try { clientGatt?.close() } catch(_:Exception) { }
        clientGatt=null; connectionTestPending=false; latestPartnerDevice=null
        try { gattServer?.close() } catch(_:Exception) { }
        gattServer=null
        try { val cb=scanCb; val radio=scanner; if(cb!=null && radio!=null) radio.stopScan(cb) } catch(_:Exception) { }
        try { val cb=advertiseCb; val radio=advertiser; if(cb!=null && radio!=null) radio.stopAdvertising(cb) } catch(_:Exception) { }
        scanCb=null; advertiseCb=null; scanner=null; advertiser=null
    }

    private fun stopSession() {
        running=false; persistActive(false); stopRadio(); engine.reset(); latestError=null
        sendConnectionResult("توقفت تجربة LINK.")
        note("session stopped",android.os.SystemClock.elapsedRealtime())
        publish(); stopForeground(STOP_FOREGROUND_REMOVE)
    }

    private fun fail(message:String) {
        latestError=message; running=false; persistActive(false); stopRadio(); engine.reset()
        note("error",android.os.SystemClock.elapsedRealtime())
        publish(); stopForeground(STOP_FOREGROUND_REMOVE); stopSelf()
    }

    private fun persistActive(value:Boolean) {
        getSharedPreferences("link_pair", MODE_PRIVATE).edit().putBoolean("active", value).apply()
    }

    private fun hasBluetoothPermissions():Boolean =
        checkSelfPermission(android.Manifest.permission.BLUETOOTH_SCAN)==android.content.pm.PackageManager.PERMISSION_GRANTED &&
        checkSelfPermission(android.Manifest.permission.BLUETOOTH_ADVERTISE)==android.content.pm.PackageManager.PERMISSION_GRANTED &&
        checkSelfPermission(android.Manifest.permission.BLUETOOTH_CONNECT)==android.content.pm.PackageManager.PERMISSION_GRANTED

    private fun createChannel() {
        getSystemService(android.app.NotificationManager::class.java).createNotificationChannel(
            android.app.NotificationChannel(CHANNEL,"LINK — مراقبة الاقتراب",
                android.app.NotificationManager.IMPORTANCE_LOW).apply {
                description="يبقي تجربة الاقتراب المحلية بين الهاتفين فعّالة."
                setShowBadge(false)
            })
    }

    private fun makeNotification():android.app.Notification {
        val openIntent=android.content.Intent(this,MainActivity::class.java).apply {
            flags=android.content.Intent.FLAG_ACTIVITY_SINGLE_TOP or android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openPending=android.app.PendingIntent.getActivity(this,0,openIntent,
            android.app.PendingIntent.FLAG_UPDATE_CURRENT or android.app.PendingIntent.FLAG_IMMUTABLE)
        val stopIntent=android.content.Intent(this,LinkProximityService::class.java).setAction(ACTION_STOP)
        val stopPending=android.app.PendingIntent.getService(this,1,stopIntent,
            android.app.PendingIntent.FLAG_UPDATE_CURRENT or android.app.PendingIntent.FLAG_IMMUTABLE)
        return android.app.Notification.Builder(this,CHANNEL)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("LINK — التجربة فعّالة")
            .setContentText(notificationText()).setContentIntent(openPending)
            .setOngoing(running).setOnlyAlertOnce(true).addAction(0,"إيقاف",stopPending).build()
    }

    private fun notificationText():String=when {
        latestError!=null -> latestError ?: "تعذّر تشغيل LINK"
        !running -> "التجربة متوقفة"
        engine.state==ProximityState.NEAR -> "الهاتفان قريبان — التفاعل فعّال"
        engine.state==ProximityState.APART -> "الهاتفان متباعدان — بانتظار العودة"
        else -> "يبحث عن الهاتف المرتبط في الخلفية"
    }

    private fun note(label:String,elapsed:Long) {
        if(events.size>=8) events.removeFirst()
        events.addLast("$label | +${(elapsed-startElapsed).coerceAtLeast(0L)}ms")
    }

    private fun diagnosticText():String {
        val seconds=if(startElapsed>0L) (android.os.SystemClock.elapsedRealtime()-startElapsed).coerceAtLeast(0L)/1000L else 0L
        val rssi=lastRssi?.let { "$it dBm" } ?: "—"
        val match=firstMatch?.let { "+${it}ms" } ?: "—"
        val strong=firstStrong?.let { "+${it}ms" } ?: "—"
        val eventText=events.toList().asReversed().joinToString("\n").ifEmpty { "لم يُسجّل حدث بعد" }
        return "الخدمة الأمامية: ${if(running) "تعمل" else "متوقفة"} | الحالة=${engine.state.name} | المدة=${seconds}ث\n"+
            "localUuid=${localUuid ?: "—"}\npartnerUuid=${partnerUuid ?: "—"}\n"+
            "المسح الخام=$rawResults | مطابقات الشريك=$partnerMatches | RSSI الأخير=$rssi\n"+
            "أول مطابقة=$match | أول RSSI قوي=$strong\nالأحداث (+ms):\n$eventText"+
            (latestError?.let { "\nالخطأ: $it" } ?: "")
    }

    private fun publish() {
        lastPublished=android.os.SystemClock.elapsedRealtime()
        sendBroadcast(android.content.Intent(ACTION_UPDATE).setPackage(packageName)
            .putExtra(EXTRA_STATE,engine.state.name).putExtra(EXTRA_ACTIVE,running)
            .putExtra(EXTRA_ERROR,latestError).putExtra(EXTRA_DIAGNOSTICS,diagnosticText()))
        if(running) getSystemService(android.app.NotificationManager::class.java)
            .notify(NOTIFICATION_ID,makeNotification())
    }

    override fun onDestroy() {
        val wasRunning=running
        running=false; persistActive(false); stopRadio()
        if(bluetoothReceiverRegistered) {
            try { unregisterReceiver(bluetoothStateReceiver) } catch(_:Exception) { }
            bluetoothReceiverRegistered=false
        }
        if(wasRunning) { engine.reset(); publish() }
        super.onDestroy()
    }
}

