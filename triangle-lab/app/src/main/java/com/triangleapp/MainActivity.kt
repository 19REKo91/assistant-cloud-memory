package com.triangleapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.triangleapp.geometry.GeometryEngine
import com.triangleapp.geometry.Triangle
import kotlin.math.max

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { Surface(Modifier.fillMaxSize()) { TriangleHome() } } }
    }
}

@Composable
private fun TriangleHome() {
    var a by remember { mutableStateOf("5") }
    var b by remember { mutableStateOf("4") }
    var c by remember { mutableStateOf("3") }
    var triangle by remember { mutableStateOf(GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)) }
    var message by remember { mutableStateOf("أدخل أطوال الأضلاع") }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("مختبر المثلث", style = MaterialTheme.typography.headlineMedium)
        Text("إدخال أطوال الأضلاع والتحقق الهندسي الفوري")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(a, { a = it }, Modifier.weight(1f), label = { Text("a = BC") })
            OutlinedTextField(b, { b = it }, Modifier.weight(1f), label = { Text("b = CA") })
            OutlinedTextField(c, { c = it }, Modifier.weight(1f), label = { Text("c = AB") })
        }
        Button(onClick = {
            val av = a.toDoubleOrNull()
            val bv = b.toDoubleOrNull()
            val cv = c.toDoubleOrNull()
            triangle = if (av != null && bv != null && cv != null)
                GeometryEngine.triangleFromSides(av, bv, cv) else null
            message = if (triangle == null) "الأطوال لا تكوّن مثلثاً صالحاً" else "مثلث صالح"
        }) { Text("تحقق وارسم") }
        Text(message)
        triangle?.let { tri ->
            TrianglePreview(tri, Modifier.fillMaxWidth().height(260.dp))
            Text("المحيط: %.4f".format(tri.perimeter))
            Text("المساحة: %.4f".format(tri.area))
            Text("الزوايا: A %.2f°  |  B %.2f°  |  C %.2f°".format(tri.angleA, tri.angleB, tri.angleC))
            Text("مركز الثقل G: (%.3f, %.3f)".format(tri.centroid.x, tri.centroid.y))
            Text("مركز الدائرة الداخلية I: (%.3f, %.3f)".format(tri.incenter.x, tri.incenter.y))
            Text("مركز الدائرة المحيطة O: (%.3f, %.3f)".format(tri.circumcenter.x, tri.circumcenter.y))
            Text("مركز التعامد H: (%.3f, %.3f)".format(tri.orthocenter.x, tri.orthocenter.y))
        }
        Spacer(Modifier.size(8.dp))
    }
}

@Composable
private fun TrianglePreview(triangle: Triangle, modifier: Modifier = Modifier) {
    Canvas(modifier) {
        val points = listOf(triangle.A, triangle.B, triangle.C)
        val minX = points.minOf { it.x }; val maxX = points.maxOf { it.x }
        val minY = points.minOf { it.y }; val maxY = points.maxOf { it.y }
        val spanX = max(maxX - minX, 1e-6); val spanY = max(maxY - minY, 1e-6)
        val scale = minOf((size.width - 48f) / spanX.toFloat(), (size.height - 48f) / spanY.toFloat())
        fun map(p: com.triangleapp.geometry.Vec2) = Offset(
            24f + ((p.x - minX) * scale).toFloat(),
            size.height - 24f - ((p.y - minY) * scale).toFloat()
        )
        val path = Path().apply {
            moveTo(map(triangle.A).x, map(triangle.A).y)
            lineTo(map(triangle.B).x, map(triangle.B).y)
            lineTo(map(triangle.C).x, map(triangle.C).y)
            close()
        }
        drawPath(path, Color(0xFF1565C0), style = Stroke(width = 4f))
        listOf(triangle.A, triangle.B, triangle.C).forEach { drawCircle(Color(0xFFD32F2F), 7f, map(it)) }
    }
}
