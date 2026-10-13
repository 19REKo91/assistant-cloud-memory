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
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
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
import java.util.ArrayDeque
import java.util.EnumMap

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
        private const val SCAN_RECOVERY_INTERVAL_MS = 8_000L
        private const val MAX_SCAN_RECOVERY_ATTEMPTS = 2
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
    private lateinit var resetButton: Button
    private lateinit var bluetoothSettingsButton: Button

    private var pair: PairingPayload? = null
    private var role: String? = null
    private var showingQr = false
    private var showDiagnostics = false
    private var active = false
    private var latestRadioError: String? = null
    private var latestAdvertiseError: String? = null
    private var latestScanError: String? = null
    private var radioStarts = 0
    private var radioStartElapsed: Long = 0L
    private val recentScanEvents = ArrayDeque<ScanEvent>(3)
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
    private var currentPartnerUuid: java.util.UUID? = null
    private var scanRecoveryAttempts = 0
    private var lastScanRecoveryAtMs = 0L
    private var activeScanUsesPartnerFilter = false
    private var pulseAnimator: AnimatorSet? = null

    private val tickTask = object : Runnable {
        override fun run() {
            if (!active || !isRadioRunning) return
            val now = SystemClock.elapsedRealtime()
            if (partnerMatches == 0 && scanRecoveryAttempts < MAX_SCAN_RECOVERY_ATTEMPTS &&
                now - lastScanRecoveryAtMs >= SCAN_RECOVERY_INTERVAL_MS) {
                recoverScan()
            }
            proximity.tick(now)?.let(::onTransition)
            updateDiagnostic()
            handler.postDelayed(this, 250L)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(24, 29, 44)
        window.navigationBarColor = Color.rgb(24, 29, 44)
        loadPair()
        buildUi()
        renderScreen()
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
        if (active) {
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            stopRadio()
        }
        super.onPause()
    }

    override fun onDestroy() {
        stopRadio()
        
        pulseAnimator?.cancel()
        super.onDestroy()
    }

    private fun loadPair() {
        val a = preferences.getString(KEY_SIDE_A, null)
        val b = preferences.getString(KEY_SIDE_B, null)
        val savedRole = preferences.getString(KEY_ROLE, null)
        if (a != null && b != null && (savedRole == "A" || savedRole == "B")) {
            pair = PairingPayload.parse("TWOHEARTS|1|$a|$b")
            role = if (pair != null) savedRole else null
        }
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
        stopButton = makeButton("إيقاف التجربة", false) {
            active = false; latestRadioError = null
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            stopRadio(); proximity.reset();  renderScreen()
        }
        resetButton = makeButton("إعادة الاقتران", false) { confirmResetPair() }
        bluetoothSettingsButton = makeButton("فتح إعدادات البلوتوث", false) {
            startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
        }
        listOf(createButton, scanButton, activateButton, hideQrButton, showQrButton, stopButton,
            resetButton, bluetoothSettingsButton).forEach(::addButton)
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
        when (proximity.state) {
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
        // LINK is intentionally silent; visual state changes are the only proximity feedback.
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
            .putString(KEY_ROLE, savedRole).apply()
    }
    private fun confirmResetPair() {
        AlertDialog.Builder(this).setTitle("إعادة الاقتران")
            .setMessage("سيُحذف رمز هذا الهاتف. لإعادة الربط، أنشئ رمزًا جديدًا وامسحه من الهاتف الآخر.")
            .setNegativeButton("إلغاء", null)
            .setPositiveButton("حذف") { _, _ ->
                active = false; stopRadio();  pair = null; role = null
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
        active = true
        if (!startRadio()) {
            active = false
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        } else {
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
        renderScreen()
    }

    @SuppressLint("MissingPermission")
    private fun startRadio(): Boolean {
        radioStarts++
        latestAdvertiseError = null
        latestScanError = null
        val payload = pair ?: return false
        val savedRole = role ?: return false
        if (!hasBluetoothPermissions()) { latestRadioError = "امنح أذونات الأجهزة القريبة ثم فعّل التجربة."; return false }
        val adapter: BluetoothAdapter? = (getSystemService(BLUETOOTH_SERVICE) as BluetoothManager).adapter
        if (adapter == null) { latestRadioError = "لا يتوفر محول بلوتوث على هذا الجهاز."; return false }
        if (!adapter.isEnabled) { latestRadioError = "يجب تفعيل البلوتوث أولًا."; return false }
        val localAdvertiser = adapter.bluetoothLeAdvertiser
        val localScanner = adapter.bluetoothLeScanner
        if (localAdvertiser == null || localScanner == null) {
            latestRadioError = "لا يتوفر الإعلان أو المسح عبر BLE على هذا الجهاز."; return false
        }

        stopRadio()
        scanner = localScanner; advertiser = localAdvertiser
        val localUuid = payload.ownUuid(savedRole)
        val partnerUuid = payload.partnerUuid(savedRole)
        diagnosticLocalUuid = localUuid.toString()
        diagnosticPartnerUuid = partnerUuid.toString()
        val advSettings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_MEDIUM)
            .setConnectable(false).setTimeout(0).build()
        val advData = AdvertiseData.Builder().setIncludeDeviceName(false)
            .setIncludeTxPowerLevel(false).addServiceUuid(ParcelUuid(localUuid)).build()
        scanResultsSeen = 0
        partnerMatches = 0
        rawScanResultsReceived = 0
        resultsWithoutScanRecord = 0
        resultsWithoutServiceUuids = 0
        scanStartedAtMs = SystemClock.elapsedRealtime()
        radioStartElapsed = scanStartedAtMs ?: SystemClock.elapsedRealtime()
        recentScanEvents.clear()
        lastRssi = null
        lastRssiElapsedMs = null
        lastMatchElapsedMs = null
        advertisingStatus = "جارٍ البدء"
        scanningStatus = "جارٍ البدء"
        val advCb = object : AdvertiseCallback() {
            override fun onStartSuccess(settingsInEffect: AdvertiseSettings?) {
                runOnUiThread {
                    advertisingStatus = "يعمل"
                    if (active) updateDiagnostic()
                }
            }
            override fun onStartFailure(errorCode: Int) {
                runOnUiThread {
                    advertisingStatus = "فشل: $errorCode"
                    latestRadioError = when (errorCode) {
                        AdvertiseCallback.ADVERTISE_FAILED_DATA_TOO_LARGE -> "بيانات إعلان BLE أكبر من المسموح."
                        AdvertiseCallback.ADVERTISE_FAILED_TOO_MANY_ADVERTISERS -> "لا تتوفر خانة إعلان BLE حاليًا."
                        AdvertiseCallback.ADVERTISE_FAILED_FEATURE_UNSUPPORTED -> "إعلان BLE غير مدعوم على هذا الجهاز."
                        AdvertiseCallback.ADVERTISE_FAILED_ALREADY_STARTED -> "إعلان BLE بدأ مسبقًا."
                        AdvertiseCallback.ADVERTISE_FAILED_INTERNAL_ERROR -> "تعذّر بدء إعلان BLE."
                        else -> "فشل إعلان BLE، الرمز: $errorCode"
                    }
                    latestAdvertiseError = latestRadioError
                    active = false; window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); stopRadio(); renderScreen()
                }
            }
        }
        advertiseCallback = advCb
        return try {
            localAdvertiser.startAdvertising(advSettings, advData, advCb)
            // Scan without an OS-level UUID filter for diagnosis; validate the partner UUID ourselves.
            currentPartnerUuid = partnerUuid
            scanRecoveryAttempts = 0
            activeScanUsesPartnerFilter = false
            lastScanRecoveryAtMs = radioStartElapsed
            val scanSettings = ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build()
            val scanCb = createScanCallback(partnerUuid)
            scanCallback = scanCb
            localScanner.startScan(null, scanSettings, scanCb)
            scanningStatus = "بدأ المسح العام؛ بانتظار الهاتف المرتبط"
            isRadioRunning = true; latestRadioError = null
            handler.removeCallbacks(tickTask); handler.post(tickTask)
            true
        } catch (_: SecurityException) {
            latestRadioError = "لم يسمح النظام باستخدام البلوتوث. راجع أذونات الأجهزة القريبة."
            stopRadio(); false
        } catch (_: IllegalStateException) {
            latestRadioError = "تعذّر تشغيل BLE. أوقف البلوتوث وشغّله ثم حاول مرة واحدة."
            stopRadio(); false
        }
    }
    @SuppressLint("MissingPermission")
    private fun recoverScan() {
        val localScanner = scanner ?: return
        val partnerUuid = currentPartnerUuid ?: return
        val oldCallback = scanCallback
        try {
            if (oldCallback != null) localScanner.stopScan(oldCallback)
        } catch (_: Exception) {
            // A stale callback must not prevent the recovery attempt.
        }

        scanRecoveryAttempts++
        val usePartnerFilter = scanRecoveryAttempts == 1
        val scanFilters: List<ScanFilter>? = if (usePartnerFilter) {
            listOf(ScanFilter.Builder().setServiceUuid(ParcelUuid(partnerUuid)).build())
        } else {
            null
        }
        val newCallback = createScanCallback(partnerUuid)
        scanCallback = newCallback
        activeScanUsesPartnerFilter = usePartnerFilter
        lastScanRecoveryAtMs = SystemClock.elapsedRealtime()
        scanningStatus = if (usePartnerFilter) {
            "إعادة المسح 1/2 بمرشح UUID الشريك"
        } else {
            "إعادة المسح 2/2 دون مرشح"
        }

        try {
            localScanner.startScan(
                scanFilters,
                ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(),
                newCallback
            )
        } catch (error: Exception) {
            latestScanError = "فشلت إعادة المسح: ${error.javaClass.simpleName}"
            scanningStatus = "فشلت إعادة المسح"
        }
        updateDiagnostic()
    }

    private fun createScanCallback(partnerUuid: java.util.UUID): ScanCallback =
        object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                inspectScanResult(result, partnerUuid)
            }

            override fun onBatchScanResults(results: MutableList<ScanResult>) {
                results.forEach { inspectScanResult(it, partnerUuid) }
            }

            override fun onScanFailed(errorCode: Int) {
                runOnUiThread {
                    scanningStatus = "فشل: $errorCode"
                    latestRadioError = "تعذّر البحث عن الهاتف المرتبط، الرمز: $errorCode"
                    latestScanError = latestRadioError
                    active = false
                    window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                    stopRadio()
                    renderScreen()
                }
            }
        }

    private fun inspectScanResult(result: ScanResult, partnerUuid: java.util.UUID) {
        val record = result.scanRecord
        val uuids = record?.serviceUuids
        runOnUiThread {
            rawScanResultsReceived++
            if (recentScanEvents.size == 3) recentScanEvents.removeFirst()
            recentScanEvents.addLast(
                ScanEvent(
                    elapsedMs = SystemClock.elapsedRealtime() - radioStartElapsed,
                    rssi = result.rssi,
                    uuids = uuids?.map { it.uuid.toString() } ?: emptyList(),
                    active = active,
                    radio = isRadioRunning
                )
            )
            if (record == null) {
                resultsWithoutScanRecord++
            } else if (uuids.isNullOrEmpty()) {
                resultsWithoutServiceUuids++
            }
            if (!active || !isRadioRunning) {
                updateDiagnostic()
                return@runOnUiThread
            }
            scanResultsSeen++
            if (uuids?.contains(ParcelUuid(partnerUuid)) == true) {
                partnerMatches++
                lastMatchElapsedMs = SystemClock.elapsedRealtime() - radioStartElapsed
                lastRssi = result.rssi
                lastRssiElapsedMs = lastMatchElapsedMs
                proximity.onRssi(result.rssi, SystemClock.elapsedRealtime())?.let(::onTransition)
            }
            updateDiagnostic()
        }
    }
    @SuppressLint("MissingPermission")
    private fun stopRadio() {
        handler.removeCallbacks(tickTask)
        try { val cb = scanCallback; val s = scanner; if (cb != null && s != null) s.stopScan(cb) } catch (_: Exception) {}
        try { val cb = advertiseCallback; val a = advertiser; if (cb != null && a != null) a.stopAdvertising(cb) } catch (_: Exception) {}
        scanCallback = null; advertiseCallback = null; scanner = null; advertiser = null; isRadioRunning = false
    }
    private fun updateDiagnostic() {
        if (!::diagnostic.isInitialized) return
        diagnostic.visibility = if (showDiagnostics) View.VISIBLE else View.GONE

        val elapsedSeconds = scanStartedAtMs?.let {
            ((SystemClock.elapsedRealtime() - it) / 1000L).coerceAtLeast(0L)
        }
        val receiveState = when {
            scanResultsSeen > 0 -> "وصلت نتائج للمسح"
            rawScanResultsReceived > 0 -> "وصلت callbacks لكن النتائج لم تُعالج"
            elapsedSeconds != null && elapsedSeconds >= 8L ->
                "لا تصل أي نتيجة من ماسح BLE منذ ${elapsedSeconds}ث"
            else -> "بانتظار أول نتيجة"
        }
        val rawDelta = rawScanResultsReceived
        val seenDelta = scanResultsSeen
        val matchDelta = partnerMatches
        val eventLines = recentScanEvents.toList().asReversed().mapIndexed { index, event ->
            "#${index + 1} +${event.elapsedMs}ms RSSI=${event.rssi} active=${event.active} radio=${event.radio} UUIDs=${event.uuids.ifEmpty { listOf("—") }.joinToString(",")}"
        }.joinToString("\n")
        val eventBlock = if (eventLines.isEmpty()) "لا توجد أحداث مسح بعد" else eventLines
        val errorLine = latestRadioError?.let { "\nالخطأ العام: $it" } ?: ""
        val lastRssiLine = lastRssi?.let { "$it dBm عند +${lastRssiElapsedMs ?: 0L}ms" } ?: "—"
        val lastMatchLine = lastMatchElapsedMs?.let { "+${it}ms" } ?: "—"
        diagnostic.text =
            "الدور المحفوظ: ${role ?: "—"} | active=$active | isRadioRunning=$isRadioRunning | radioStarts=$radioStarts\n" +
            "localUuid=${diagnosticLocalUuid ?: "—"}\npartnerUuid=${diagnosticPartnerUuid ?: "—"}\n" +
            "RSSI الأخير: $lastRssiLine | آخر مطابقة: $lastMatchLine\n" +
            "raw=$rawScanResultsReceived (Δ منذ بدء الراديو=$rawDelta) | seen=$scanResultsSeen (Δ=$seenDelta) | matches=$partnerMatches (Δ=$matchDelta)\n" +
            "بلا ScanRecord=$resultsWithoutScanRecord | بلا UUID=$resultsWithoutServiceUuids\n" +
            "الإعلان: $advertisingStatus | خطأ الإعلان: ${latestAdvertiseError ?: "—"}\n" +
            "المسح: $scanningStatus | الوضع=${if (activeScanUsesPartnerFilter) "UUID الشريك" else "عام"} | محاولات الاستعادة=$scanRecoveryAttempts/$MAX_SCAN_RECOVERY_ATTEMPTS | خطأ المسح: ${latestScanError ?: "—"}\n" +
            "حالة الاستقبال: $receiveState\nآخر 3 أحداث (الأحدث أولًا):\n$eventBlock$errorLine"
    }
    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
