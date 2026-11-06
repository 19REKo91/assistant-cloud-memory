package com.triangleapp

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.SharedPreferences
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.triangleapp.geometry.GeometryEngine
import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

private enum class EditMode { SIDES, ANGLES, COORDS, COMPARE }

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    TriangleHome()
                }
            }
        }
    }
}

@Composable
private fun TriangleHome() {
    val context = LocalContext.current
    val preferences = remember { context.getSharedPreferences("triangle_lab", Context.MODE_PRIVATE) }
    var mode by remember { mutableStateOf(EditMode.SIDES) }
    var triangle by remember { mutableStateOf(GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!) }
    var compareTriangle by remember { mutableStateOf<Triangle?>(null) }
    var message by remember { mutableStateOf("مثلث صالح — يمكنك تغيير المدخلات") }

    var sideA by remember { mutableStateOf("5") }
    var sideB by remember { mutableStateOf("4") }
    var sideC by remember { mutableStateOf("3") }
    var angleA by remember { mutableStateOf("90") }
    var angleB by remember { mutableStateOf("53.13") }
    var referenceSide by remember { mutableStateOf('c') }
    var referenceLength by remember { mutableStateOf("3") }
    var ax by remember { mutableStateOf("0") }
    var ay by remember { mutableStateOf("0") }
    var bx by remember { mutableStateOf("3") }
    var by by remember { mutableStateOf("0") }
    var cx by remember { mutableStateOf("0") }
    var cy by remember { mutableStateOf("4") }
    var compareA by remember { mutableStateOf("5") }
    var compareB by remember { mutableStateOf("4") }
    var compareC by remember { mutableStateOf("3") }
    var english by remember { mutableStateOf(false) }

    var options by remember { mutableStateOf(DrawOptions()) }
    var zoom by remember { mutableFloatStateOf(1f) }
    var pan by remember { mutableStateOf(Offset.Zero) }
    val saved = remember { mutableStateListOf<Triangle>() }

    fun setSideFields(t: Triangle) {
        sideA = "%.4f".format(Locale.US, t.a); sideB = "%.4f".format(Locale.US, t.b); sideC = "%.4f".format(Locale.US, t.c)
    }
    fun setAngleFields(t: Triangle) {
        angleA = "%.4f".format(Locale.US, t.angleA); angleB = "%.4f".format(Locale.US, t.angleB)
        referenceLength = when (referenceSide) { 'a' -> t.a; 'b' -> t.b; else -> t.c }.let { "%.4f".format(Locale.US, it) }
    }
    fun applyCurrent(): Boolean {
        val result = when (mode) {
            EditMode.SIDES -> {
                val a = parseNumber(sideA); val b = parseNumber(sideB); val c = parseNumber(sideC)
                if (a == null || b == null || c == null) null else GeometryEngine.triangleFromSides(a, b, c)
            }
            EditMode.ANGLES -> {
                val a = parseNumber(angleA); val b = parseNumber(angleB); val length = parseNumber(referenceLength)
                if (a == null || b == null || length == null) null else GeometryEngine.triangleFromAngles(a, b, referenceSide, length)
            }
            EditMode.COORDS -> {
                val points = listOf(ax, ay, bx, by, cx, cy).map { parseNumber(it) }
                if (points.any { it == null }) null else {
                    val v = points.map { it!! }
                    Triangle(Vec2(v[0], v[1]), Vec2(v[2], v[3]), Vec2(v[4], v[5])).takeUnless { it.isDegenerate }
                }
            }
            EditMode.COMPARE -> {
                val a = parseNumber(compareA); val b = parseNumber(compareB); val c = parseNumber(compareC)
                val candidate = if (a == null || b == null || c == null) null else GeometryEngine.triangleFromSides(a, b, c)
                if (candidate == null) {
                    message = if (english) "Comparison values do not form a valid triangle" else "أضلاع مثلث المقارنة غير صالحة"
                    return false
                }
                compareTriangle = candidate
                message = if (english) "Comparison triangle updated" else "تم تحديث مثلث المقارنة"
                return true
            }
        }
        if (result == null || result.isDegenerate) {
            message = if (english) "Invalid values: no valid triangle can be formed" else "مدخلات غير صالحة: لا يمكن تكوين مثلث بهذه القيم"
            return false
        }
        triangle = result
        message = if (english) "Valid triangle — geometry updated" else "مثلث صالح — تم تحديث الرسم والقياسات"
        return true
    }

    LaunchedEffect(Unit) {
        val raw = preferences.getString("saved_triangles", null)
        if (!raw.isNullOrBlank()) {
            runCatching {
                val array = JSONArray(raw)
                for (i in 0 until array.length()) {
                    val item = array.getJSONObject(i)
                    val t = triangleFromJson(item)
                    if (!t.isDegenerate) saved.add(t)
                }
            }
        }
        val restored = preferences.getString("current_triangle", null)
        if (!restored.isNullOrBlank()) {
            runCatching {
                val t = triangleFromJson(JSONObject(restored))
                if (!t.isDegenerate) {
                    triangle = t
                    setSideFields(t)
                    setAngleFields(t)
                }
            }
        }
    }

    fun changeMode(next: EditMode) {
        if (next == mode) return
        when (next) {
            EditMode.SIDES -> setSideFields(triangle)
            EditMode.ANGLES -> setAngleFields(triangle)
            EditMode.COORDS -> {
                ax = "%.4f".format(Locale.US, triangle.A.x); ay = "%.4f".format(Locale.US, triangle.A.y)
                bx = "%.4f".format(Locale.US, triangle.B.x); by = "%.4f".format(Locale.US, triangle.B.y)
                cx = "%.4f".format(Locale.US, triangle.C.x); cy = "%.4f".format(Locale.US, triangle.C.y)
            }
            EditMode.COMPARE -> {
                val t = compareTriangle ?: triangle
                compareA = "%.4f".format(Locale.US, t.a); compareB = "%.4f".format(Locale.US, t.b); compareC = "%.4f".format(Locale.US, t.c)
            }
        }
        mode = next
    }

    CompositionLocalProvider(LocalLayoutDirection provides if (english) LayoutDirection.Ltr else LayoutDirection.Rtl) {
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(if (english) "Triangle Lab" else "مختبر المثلث", style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = { english = !english }) { Text(if (english) "العربية" else "English") }
        }
        Text(if (english) "Geometry workspace — values are validated before applying" else "مساحة هندسية — تُفحص القيم قبل اعتمادها")

        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            FilterChip(selected = mode == EditMode.SIDES, onClick = { changeMode(EditMode.SIDES) }, label = { Text(if (english) "Sides" else "الأضلاع") })
            FilterChip(selected = mode == EditMode.ANGLES, onClick = { changeMode(EditMode.ANGLES) }, label = { Text(if (english) "Angles" else "الزوايا") })
            FilterChip(selected = mode == EditMode.COORDS, onClick = { changeMode(EditMode.COORDS) }, label = { Text(if (english) "Coordinates" else "الإحداثيات") })
            FilterChip(selected = mode == EditMode.COMPARE, onClick = { changeMode(EditMode.COMPARE) }, label = { Text(if (english) "Compare" else "المقارنة") })
        }

        when (mode) {
            EditMode.SIDES -> {
                Text(if (english) "Side lengths (a=BC, b=CA, c=AB)" else "أطوال الأضلاع (a=BC، b=CA، c=AB)")
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    NumberInput(sideA, { sideA = it }, "a", Modifier.weight(1f))
                    NumberInput(sideB, { sideB = it }, "b", Modifier.weight(1f))
                    NumberInput(sideC, { sideC = it }, "c", Modifier.weight(1f))
                }
            }
            EditMode.ANGLES -> {
                Text(if (english) "Enter A and B, then select the fixed reference side" else "أدخل الزاويتين A وB ثم اختر الضلع المرجعي الثابت")
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    NumberInput(angleA, { angleA = it }, if (english) "Angle A°" else "زاوية A°", Modifier.weight(1f))
                    NumberInput(angleB, { angleB = it }, if (english) "Angle B°" else "زاوية B°", Modifier.weight(1f))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf('a', 'b', 'c').forEach { side ->
                        FilterChip(selected = referenceSide == side, onClick = {
                            referenceSide = side
                            referenceLength = "%.4f".format(Locale.US, when (side) { 'a' -> triangle.a; 'b' -> triangle.b; else -> triangle.c })
                        }, label = { Text(if (english) "Side ${side.uppercaseChar()}" else "الضلع ${side.uppercaseChar()}") })
                    }
                    NumberInput(referenceLength, { referenceLength = it }, if (english) "Fixed length" else "الطول الثابت", Modifier.weight(1f))
                }
            }
            EditMode.COORDS -> {
                Text(if (english) "Vertex coordinates" else "إحداثيات الرؤوس")
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    NumberInput(ax, { ax = it }, "Ax", Modifier.weight(1f)); NumberInput(ay, { ay = it }, "Ay", Modifier.weight(1f))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    NumberInput(bx, { bx = it }, "Bx", Modifier.weight(1f)); NumberInput(by, { by = it }, "By", Modifier.weight(1f))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    NumberInput(cx, { cx = it }, "Cx", Modifier.weight(1f)); NumberInput(cy, { cy = it }, "Cy", Modifier.weight(1f))
                }
            }
            EditMode.COMPARE -> {
                Text(if (english) "Comparison triangle side lengths" else "أطوال أضلاع مثلث المقارنة")
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    NumberInput(compareA, { compareA = it }, "a₂", Modifier.weight(1f))
                    NumberInput(compareB, { compareB = it }, "b₂", Modifier.weight(1f))
                    NumberInput(compareC, { compareC = it }, "c₂", Modifier.weight(1f))
                }
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { applyCurrent() }) { Text(if (english) "Apply" else "اعتماد") }
            OutlinedButton(onClick = {
                triangle = GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!
                compareTriangle = null
                setSideFields(triangle); setAngleFields(triangle)
                message = if (english) "Reset to the reference triangle" else "أُعيد ضبط المثلث المرجعي"
            }) { Text(if (english) "Reset" else "إعادة ضبط") }
            if (compareTriangle != null) {
                TextButton(onClick = {
                    compareTriangle = null
                    message = if (english) "Comparison removed" else "أُزيل مثلث المقارنة"
                }) { Text(if (english) "Clear compare" else "إزالة المقارنة") }
            }
        }
        Text(message, color = MaterialTheme.colorScheme.primary)

        TriangleCanvas(
            triangle = triangle,
            compare = compareTriangle,
            options = options,
            zoom = zoom,
            pan = pan,
            onViewTransform = { newZoom, newPan -> zoom = newZoom; pan = newPan },
            modifier = Modifier.fillMaxWidth().height(330.dp)
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { zoom = (zoom * 1.2f).coerceAtMost(5f) }) { Text("+") }
            OutlinedButton(onClick = { zoom = (zoom / 1.2f).coerceAtLeast(0.6f) }) { Text("−") }
            TextButton(onClick = { zoom = 1f; pan = Offset.Zero }) { Text(if (english) "Reset view" else "إعادة ضبط العرض") }
            Text(if (english) "Pinch to zoom • drag to pan" else "قرّب بإصبعين واسحب لتحريك الرسم")
        }

        Text(if (english) "Display controls" else "عناصر الرسم", style = MaterialTheme.typography.titleMedium)
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ToggleChip(if (english) "Altitudes" else "الارتفاعات", options.altitudes) { options = options.copy(altitudes = it) }
                ToggleChip(if (english) "Vertex bisectors" else "منصفات الرؤوس", options.vertexBisectors) { options = options.copy(vertexBisectors = it) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ToggleChip(if (english) "Centers" else "المراكز G/I/O/H", options.centers) { options = options.copy(centers = it) }
                ToggleChip(if (english) "I radii" else "وصلات I للأضلاع", options.centerRadii) { options = options.copy(centerRadii = it) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ToggleChip(if (english) "Internal angles" else "الزوايا الداخلية", options.internalAngles) { options = options.copy(internalAngles = it) }
                ToggleChip(if (english) "External angles" else "الزوايا الخارجية", options.externalAngles) { options = options.copy(externalAngles = it) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ToggleChip(if (english) "Extend sides" else "تطويل الأضلاع", options.sideExtensions) { options = options.copy(sideExtensions = it) }
                ToggleChip(if (english) "Side labels" else "قياسات الأضلاع", options.sideLabels) { options = options.copy(sideLabels = it) }
            }
        }

        Text(if (english) "Measurements" else "القياسات", style = MaterialTheme.typography.titleMedium)
        Text("a = %.4f    b = %.4f    c = %.4f".format(triangle.a, triangle.b, triangle.c))
        Text("A = %.3f°    B = %.3f°    C = %.3f°".format(triangle.angleA, triangle.angleB, triangle.angleC))
        Text((if (english) "Perimeter" else "المحيط") + ": %.4f".format(triangle.perimeter) + "    " + (if (english) "Area" else "المساحة") + ": %.4f".format(triangle.area))
        Text("G(%.3f, %.3f)    I(%.3f, %.3f)".format(triangle.centroid.x, triangle.centroid.y, triangle.incenter.x, triangle.incenter.y))
        Text("O(%.3f, %.3f)    H(%.3f, %.3f)".format(triangle.circumcenter.x, triangle.circumcenter.y, triangle.orthocenter.x, triangle.orthocenter.y))

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                saved.add(triangle)
                persistTriangles(preferences, saved)
                message = if (english) "Triangle saved on this device" else "تم حفظ المثلث على هذا الجهاز"
            }) { Text(if (english) "Save" else "حفظ") }
            OutlinedButton(onClick = {
                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                clipboard.setPrimaryClip(ClipData.newPlainText("Triangle Lab", triangleToJson(triangle).toString()))
                message = if (english) "Triangle data copied as JSON" else "نُسخت بيانات المثلث بصيغة JSON"
            }) { Text(if (english) "Export" else "تصدير") }
            OutlinedButton(onClick = {
                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val raw = clipboard.primaryClip?.getItemAt(0)?.coerceToText(context)?.toString()
                val imported = runCatching { raw?.let { triangleFromJson(JSONObject(it)) } }.getOrNull()
                if (imported != null && !imported.isDegenerate) {
                    triangle = imported; setSideFields(imported); setAngleFields(imported)
                    message = if (english) "Triangle imported" else "تم استيراد المثلث"
                } else message = if (english) "Clipboard does not contain valid Triangle Lab JSON" else "محتوى الحافظة ليس بيانات مثلث صالحة"
            }) { Text(if (english) "Import" else "استيراد") }
        }

        if (saved.isNotEmpty()) {
            Text(if (english) "Saved triangles" else "المثلثات المحفوظة", style = MaterialTheme.typography.titleMedium)
            saved.forEachIndexed { index, item ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("${index + 1}. a=%.2f, b=%.2f, c=%.2f".format(item.a, item.b, item.c))
                    Row {
                        TextButton(onClick = { triangle = item; setSideFields(item); setAngleFields(item) }) { Text(if (english) "Load" else "تحميل") }
                        TextButton(onClick = {
                            saved.removeAt(index)
                            persistTriangles(preferences, saved)
                        }) { Text(if (english) "Delete" else "حذف") }
                    }
                }
            }
        }
        Spacer(Modifier.height(8.dp))
    }
    }

    SideEffect {
        preferences.edit().putString("current_triangle", triangleToJson(triangle).toString()).apply()
    }
}

@Composable
private fun NumberInput(value: String, onValueChange: (String) -> Unit, label: String, modifier: Modifier = Modifier) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier,
        label = { Text(label) },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal)
    )
}

@Composable
private fun ToggleChip(label: String, checked: Boolean, onChecked: (Boolean) -> Unit) {
    FilterChip(selected = checked, onClick = { onChecked(!checked) }, label = { Text(label) })
}


private fun parseNumber(raw: String): Double? {
    val normalized = buildString {
        raw.trim().forEach { ch ->
            when (ch) {
                in '٠'..'٩' -> append(('0'.code + (ch.code - '٠'.code)).toChar())
                in '۰'..'۹' -> append(('0'.code + (ch.code - '۰'.code)).toChar())
                '٫', '،' -> append('.')
                '٬', ' ' -> Unit
                else -> append(ch)
            }
        }
    }
    return normalized.toDoubleOrNull()
}

private fun triangleToJson(t: Triangle): JSONObject = JSONObject().apply {
    put("ax", t.A.x); put("ay", t.A.y)
    put("bx", t.B.x); put("by", t.B.y)
    put("cx", t.C.x); put("cy", t.C.y)
}

private fun triangleFromJson(json: JSONObject): Triangle = Triangle(
    Vec2(json.getDouble("ax"), json.getDouble("ay")),
    Vec2(json.getDouble("bx"), json.getDouble("by")),
    Vec2(json.getDouble("cx"), json.getDouble("cy"))
)

private fun persistTriangles(preferences: SharedPreferences, triangles: List<Triangle>) {
    val array = JSONArray()
    triangles.forEach { array.put(triangleToJson(it)) }
    preferences.edit().putString("saved_triangles", array.toString()).apply()
}
