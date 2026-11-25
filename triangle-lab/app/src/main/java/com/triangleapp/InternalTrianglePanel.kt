package com.triangleapp

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.triangleapp.geometry.Triangle
import java.util.Locale
import kotlin.math.abs

@Composable
fun InternalTrianglePanel(triangle: Triangle, english: Boolean) {
    val parts = triangle.centroidSubtriangles()
    Column(Modifier.fillMaxWidth().padding(top = 8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(if (english) "Centroid subtriangles" else "المثلثات الداخلية حول مركز الثقل G", style = MaterialTheme.typography.titleMedium)
        Text(if (english) "Calculated from original coordinates, not estimated from the drawing." else "تُحسب من الإحداثيات الأصلية، ولا تُقدّر من الرسم.")
        parts.forEach { (name, sub) ->
            Text(name + "  |  " + (if (english) "Sides" else "الأضلاع") + ": a=" + fmt(sub.a) + ", b=" + fmt(sub.b) + ", c=" + fmt(sub.c))
            Text((if (english) "Angles" else "الزوايا") + ": A=" + fmt(sub.angleA) + "°, B=" + fmt(sub.angleB) + "°, C=" + fmt(sub.angleC) + "°")
            Text((if (english) "Area" else "المساحة") + ": " + fmt(sub.area) + "    " + (if (english) "Perimeter" else "المحيط") + ": " + fmt(sub.perimeter))
            Text((if (english) "Type" else "النوع") + ": " + triangleType(sub, english))
        }
        val totalArea = parts.sumOf { it.second.area }
        val passed = abs(totalArea - triangle.area) <= maxOf(1.0, triangle.area) * 1e-9
        Text((if (english) "Area check (sum / original)" else "فحص المساحة (المجموع / الأصل)") + ": " + fmt(totalArea) + " / " + fmt(triangle.area))
        Text(if (passed) { if (english) "Partition check: passed" else "فحص التقسيم: ناجح" } else { if (english) "Partition check: failed" else "فحص التقسيم: فشل" }, color = if (passed) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
    }
}

private fun triangleType(t: Triangle, english: Boolean): String {
    val scale = maxOf(t.a, t.b, t.c)
    val ab = abs(t.a - t.b) <= scale * 1e-8
    val bc = abs(t.b - t.c) <= scale * 1e-8
    val ca = abs(t.c - t.a) <= scale * 1e-8
    val side = when { ab && bc -> if (english) "equilateral" else "متساوي الأضلاع"; ab || bc || ca -> if (english) "isosceles" else "متساوي الساقين"; else -> if (english) "scalene" else "مختلف الأضلاع" }
    val largest = maxOf(t.angleA, t.angleB, t.angleC)
    val angle = when { abs(largest - 90.0) <= 1e-7 -> if (english) "right" else "قائم"; largest > 90.0 -> if (english) "obtuse" else "منفرج"; else -> if (english) "acute" else "حاد" }
    return side + " / " + angle
}

private fun fmt(value: Double): String = "%.4f".format(Locale.US, value)
