package com.triangleapp.geometry

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt

data class Triangle(val A: Vec2, val B: Vec2, val C: Vec2) {
    val a: Double get() = dist(B, C)
    val b: Double get() = dist(C, A)
    val c: Double get() = dist(A, B)
    val perimeter: Double get() = a + b + c
    val area: Double get() {
        val cross = (B.x - A.x) * (C.y - A.y) - (B.y - A.y) * (C.x - A.x)
        return abs(cross) / 2.0
    }
    val isDegenerate: Boolean
        get() = !A.isFinite() || !B.isFinite() || !C.isFinite() ||
            !a.isFinite() || !b.isFinite() || !c.isFinite() || !area.isFinite() ||
            !perimeter.isFinite() || minOf(a, b, c) <= 0.0 ||
            (area / max(a, max(b, c)) / max(a, max(b, c))) <= 1e-12

    private fun angle(opposite: Double, side1: Double, side2: Double): Double {
        if (side1 <= 0.0 || side2 <= 0.0 || !opposite.isFinite() ||
            !side1.isFinite() || !side2.isFinite()) return Double.NaN
        val scale = max(opposite, max(side1, side2))
        val x = opposite / scale
        val y = side1 / scale
        val z = side2 / scale
        val cosine = ((y * y + z * z - x * x) / (2.0 * y * z)).coerceIn(-1.0, 1.0)
        return Math.toDegrees(kotlin.math.acos(cosine))
    }

    val angleA: Double get() = angle(a, b, c)
    val angleB: Double get() = angle(b, a, c)
    val angleC: Double get() = angle(c, a, b)

    val centroid: Vec2 get() = (A + B + C) / 3.0

    val incenter: Vec2
        get() = (A * a + B * b + C * c) / perimeter

    val circumcenter: Vec2
        get() {
            val d = 2.0 * (A.x * (B.y - C.y) + B.x * (C.y - A.y) + C.x * (A.y - B.y))
            val edgeScale = max(a, max(b, c))
            val relativeDeterminant = abs(d / edgeScale / edgeScale)
            if (!d.isFinite() || !relativeDeterminant.isFinite() || relativeDeterminant <= 4e-12)
                return Vec2(Double.NaN, Double.NaN)
            val aa = A.x * A.x + A.y * A.y
            val bb = B.x * B.x + B.y * B.y
            val cc = C.x * C.x + C.y * C.y
            val ux = (aa * (B.y - C.y) + bb * (C.y - A.y) + cc * (A.y - B.y)) / d
            val uy = (aa * (C.x - B.x) + bb * (A.x - C.x) + cc * (B.x - A.x)) / d
            return Vec2(ux, uy)
        }

    // Vector identity valid for every non-degenerate Euclidean triangle: H = A + B + C - 2O.
    val orthocenter: Vec2
        get() {
            val o = circumcenter
            return if (o.isFinite()) A + B + C - o * 2.0 else Vec2(Double.NaN, Double.NaN)
        }

    fun footFromVertex(vertex: Char): Vec2? {
        val (p, u, v) = when (vertex.uppercaseChar()) {
            'A' -> Triple(A, B, C)
            'B' -> Triple(B, C, A)
            'C' -> Triple(C, A, B)
            else -> return null
        }
        val edge = v - u
        val denominator = edge.x * edge.x + edge.y * edge.y
        if (denominator <= 0.0 || !denominator.isFinite()) return null
        // Do not clamp t: an altitude may meet the supporting line outside the segment.
        val t = ((p - u).x * edge.x + (p - u).y * edge.y) / denominator
        return u + edge * t
    }

    fun bisectorFoot(vertex: Char): Vec2? {
        fun divide(p1: Vec2, p2: Vec2, len1: Double, len2: Double): Vec2? {
            val sum = len1 + len2
            if (sum <= 0.0 || !sum.isFinite()) return null
            // Angle-bisector theorem: distance ratio from p1 to p2 is len1:len2.
            return (p1 * len2 + p2 * len1) / sum
        }
        return when (vertex.uppercaseChar()) {
            'A' -> divide(B, C, c, b)
            'B' -> divide(C, A, a, c)
            'C' -> divide(A, B, b, a)
            else -> null
        }
    }
}
