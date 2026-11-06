package com.triangleapp

import android.graphics.Paint
import android.graphics.Typeface
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

data class DrawOptions(
    val altitudes: Boolean = true,
    val vertexBisectors: Boolean = true,
    val centerRadii: Boolean = true,
    val centers: Boolean = true,
    val internalAngles: Boolean = true,
    val externalAngles: Boolean = false,
    val sideLabels: Boolean = true
)

@Composable
fun TriangleCanvas(
    triangle: Triangle,
    compare: Triangle?,
    options: DrawOptions,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val extra = compare?.let { listOf(it.A, it.B, it.C) }.orEmpty()
        val all = listOf(triangle.A, triangle.B, triangle.C) + extra
        val minX = all.minOf { it.x }; val maxX = all.maxOf { it.x }
        val minY = all.minOf { it.y }; val maxY = all.maxOf { it.y }
        val spanX = max(maxX - minX, 1e-8)
        val spanY = max(maxY - minY, 1e-8)
        val pad = 44f
        val scale = min((size.width - pad * 2) / spanX.toFloat(), (size.height - pad * 2) / spanY.toFloat())
        val usedW = spanX.toFloat() * scale
        val usedH = spanY.toFloat() * scale
        val left = (size.width - usedW) / 2f
        val top = (size.height - usedH) / 2f
        fun point(p: Vec2) = Offset(left + ((p.x - minX) * scale).toFloat(), size.height - top - ((p.y - minY) * scale).toFloat())
        fun segment(p: Vec2, q: Vec2, color: Color, width: Float = 2.5f, dashed: Boolean = false) {
            drawLine(color, point(p), point(q), width, pathEffect = if (dashed) androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(12f, 8f)) else null)
        }
        fun label(text: String, at: Vec2, color: Int = android.graphics.Color.DKGRAY) {
            val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                this.color = color
                textSize = 31f
                typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            }
            drawContext.canvas.nativeCanvas.drawText(text, point(at).x + 8f, point(at).y - 8f, paint)
        }
        fun foot(p: Vec2, u: Vec2, v: Vec2): Vec2 {
            val e = v - u
            val d = e.x * e.x + e.y * e.y
            if (d <= 1e-16) return u
            val t = ((p.x - u.x) * e.x + (p.y - u.y) * e.y) / d
            return u + e * t
        }
        val colors = listOf(Color(0xFF1565C0), Color(0xFF2E7D32), Color(0xFFEF6C00))
        val vertices = listOf(triangle.A, triangle.B, triangle.C)
        val edges = listOf(triangle.B to triangle.C, triangle.C to triangle.A, triangle.A to triangle.B)

        compare?.let {
            val cp = listOf(it.A, it.B, it.C)
            val p = Path().apply {
                moveTo(point(cp[0]).x, point(cp[0]).y)
                lineTo(point(cp[1]).x, point(cp[1]).y)
                lineTo(point(cp[2]).x, point(cp[2]).y)
                close()
            }
            drawPath(p, Color(0xFF8E24AA), style = Stroke(width = 3.5f, pathEffect = androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(14f, 9f))))
            cp.forEachIndexed { i, v -> label("D${i + 1}", v, android.graphics.Color.rgb(142, 36, 170)) }
        }

        edges.forEachIndexed { i, edge -> segment(edge.first, edge.second, colors[i], 5f) }

        if (options.altitudes) {
            vertices.forEachIndexed { i, v ->
                val edge = edges[i]
                val h = foot(v, edge.first, edge.second)
                segment(v, h, Color(0xFF00838F), 2f, true)
                drawCircle(Color(0xFF00838F), 5f, point(h))
            }
        }

        if (options.vertexBisectors) {
            vertices.forEachIndexed { i, v ->
                val f = triangle.bisectorFoot("ABC"[i]) ?: return@forEachIndexed
                segment(v, f, Color(0xFFD81B60), 2.8f)
            }
        }

        if (options.centerRadii) {
            val center = triangle.incenter
            edges.forEach { (u, v) ->
                val h = foot(center, u, v)
                segment(center, h, Color(0xFF6A1B9A), 2f, true)
            }
        }

        if (options.internalAngles || options.externalAngles) {
            vertices.forEachIndexed { i, v ->
                val p1 = vertices[(i + 1) % 3] - v
                val p2 = vertices[(i + 2) % 3] - v
                val a1 = atan2(-p1.y, p1.x)
                val a2 = atan2(-p2.y, p2.x)
                var delta = a2 - a1
                while (delta > Math.PI) delta -= 2 * Math.PI
                while (delta < -Math.PI) delta += 2 * Math.PI
                val radius = min(size.width, size.height) * 0.075f
                if (options.internalAngles) {
                    val path = Path()
                    val steps = 24
                    for (s in 0..steps) {
                        val angle = a1 + delta * s / steps
                        val p = point(v)
                        val x = p.x + cos(angle).toFloat() * radius
                        val y = p.y + sin(angle).toFloat() * radius
                        if (s == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    }
                    drawPath(path, Color(0xFF455A64), style = Stroke(width = 2f))
                    label("%.1f°".format(listOf(triangle.angleA, triangle.angleB, triangle.angleC)[i]), v)
                }
                if (options.externalAngles) {
                    val mid = a1 + delta / 2.0 + Math.PI
                    val p = point(v)
                    val q = Offset(p.x + cos(mid).toFloat() * radius * 1.4f, p.y + sin(mid).toFloat() * radius * 1.4f)
                    drawLine(Color(0xFF5D4037), p, q, 2f)
                }
            }
        }

        if (options.centers) {
            val centerList = listOf(
                "G" to triangle.centroid,
                "I" to triangle.incenter,
                "O" to triangle.circumcenter,
                "H" to triangle.orthocenter
            )
            centerList.forEach { (name, p) ->
                if (p.isFinite()) {
                    val color = when (name) {
                        "G" -> Color(0xFF00897B)
                        "I" -> Color(0xFFE91E63)
                        "O" -> Color(0xFF5E35B1)
                        else -> Color(0xFF3949AB)
                    }
                    drawCircle(color, 7f, point(p))
                    label(name, p)
                }
            }
        }

        vertices.forEachIndexed { i, v ->
            drawCircle(Color(0xFFD32F2F), 7f, point(v))
            label("ABC"[i].toString(), v, android.graphics.Color.BLACK)
        }
        if (options.sideLabels) {
            val sideNames = listOf("a=%.2f".format(triangle.a), "b=%.2f".format(triangle.b), "c=%.2f".format(triangle.c))
            edges.forEachIndexed { i, edge ->
                val mid = (edge.first + edge.second) / 2.0
                label(sideNames[i], mid, android.graphics.Color.DKGRAY)
            }
        }
    }
}
