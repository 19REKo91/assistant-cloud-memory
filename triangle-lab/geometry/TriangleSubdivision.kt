package com.triangleapp.geometry

import kotlin.math.PI
import kotlin.math.atan2

data class InternalTriangle(
    val name: String,
    val triangle: Triangle,
    val vertexLabels: List<String>
)

data class CentroidSector(
    val startRay: String,
    val endRay: String,
    val angleDegrees: Double
)

/**
 * Divides a triangle into the three regions formed by its vertices and centroid.
 * Each region has exactly one third of the original area.
 */
fun Triangle.internalTriangles(): List<InternalTriangle> {
    val g = centroid
    return listOf(
        InternalTriangle("ABG", Triangle(A, B, g), listOf("A", "B", "G")),
        InternalTriangle("ACG", Triangle(A, C, g), listOf("A", "C", "G")),
        InternalTriangle("BCG", Triangle(B, C, g), listOf("B", "C", "G"))
    )
}

/**
 * Returns the six consecutive sectors formed by the three medians at centroid G.
 * Each median contributes two opposite rays: a vertex and the midpoint of its
 * opposite side. Sectors are ordered counter-clockwise in Cartesian coordinates.
 */
fun Triangle.centroidSectors(): List<CentroidSector> {
    val g = centroid
    data class Ray(val label: String, val angle: Double)

    fun midpoint(p: Vec2, q: Vec2) = (p + q) / 2.0
    fun normalizedAngle(value: Double): Double {
        val full = 2.0 * PI
        return ((value % full) + full) % full
    }

    val rays = listOf(
        "A" to A,
        "M_BC" to midpoint(B, C),
        "B" to B,
        "M_CA" to midpoint(C, A),
        "C" to C,
        "M_AB" to midpoint(A, B)
    ).map { (label, p) ->
        Ray(label, normalizedAngle(atan2(p.y - g.y, p.x - g.x)))
    }.sortedBy { it.angle }

    return rays.indices.map { index ->
        val start = rays[index]
        val end = rays[(index + 1) % rays.size]
        val delta = normalizedAngle(end.angle - start.angle)
        CentroidSector(start.label, end.label, Math.toDegrees(delta))
    }
}
