package com.triangleapp

import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import org.json.JSONObject

/**
 * Creates a complete, machine-readable snapshot of the currently displayed geometry.
 * Length units are intentionally marked as unspecified because the app accepts unitless input.
 */
internal fun triangleExportJson(
    triangle: Triangle,
    comparison: Triangle?,
    options: DrawOptions
): JSONObject {
    fun number(value: Double): Any = if (value.isFinite()) value else JSONObject.NULL

    fun point(point: Vec2): JSONObject = JSONObject().apply {
        put("x", number(point.x))
        put("y", number(point.y))
    }

    fun triangleData(t: Triangle): JSONObject {
        val angleA = t.angleA
        val angleB = t.angleB
        val angleC = t.angleC
        val maxSide = maxOf(t.a, t.b, t.c)
        val sideTolerance = maxSide * 1e-8
        val sideType = when {
            !maxSide.isFinite() || maxSide <= 0.0 -> "unknown"
            maxOf(kotlin.math.abs(t.a - t.b), kotlin.math.abs(t.b - t.c), kotlin.math.abs(t.c - t.a)) <= sideTolerance -> "equilateral"
            kotlin.math.abs(t.a - t.b) <= sideTolerance ||
                kotlin.math.abs(t.b - t.c) <= sideTolerance ||
                kotlin.math.abs(t.c - t.a) <= sideTolerance -> "isosceles"
            else -> "scalene"
        }
        val angleType = when {
            !angleA.isFinite() || !angleB.isFinite() || !angleC.isFinite() -> "unknown"
            listOf(angleA, angleB, angleC).any { kotlin.math.abs(it - 90.0) <= 1e-7 } -> "right"
            listOf(angleA, angleB, angleC).all { it < 90.0 } -> "acute"
            else -> "obtuse"
        }

        return JSONObject().apply {
            put("vertices", JSONObject().apply {
                put("A", point(t.A))
                put("B", point(t.B))
                put("C", point(t.C))
            })
            put("sides", JSONObject().apply {
                put("a_BC", number(t.a))
                put("b_CA", number(t.b))
                put("c_AB", number(t.c))
            })
            put("internal_angles_degrees", JSONObject().apply {
                put("A", number(angleA))
                put("B", number(angleB))
                put("C", number(angleC))
            })
            put("external_angles_degrees", JSONObject().apply {
                put("A", number(180.0 - angleA))
                put("B", number(180.0 - angleB))
                put("C", number(180.0 - angleC))
            })
            put("angle_sum_degrees", number(angleA + angleB + angleC))
            put("perimeter", number(t.perimeter))
            put("area", number(t.area))
            put("centers", JSONObject().apply {
                put("G_centroid", point(t.centroid))
                put("I_incenter", point(t.incenter))
                put("O_circumcenter", point(t.circumcenter))
                put("H_orthocenter", point(t.orthocenter))
            })
            put("classification", JSONObject().apply {
                put("by_sides", sideType)
                put("by_angles", angleType)
            })
        }
    }

    val current = triangleData(triangle)
    val comparisonData = comparison?.let { other ->
        JSONObject().apply {
            put("triangle", triangleData(other))
            put("differences_comparison_minus_current", JSONObject().apply {
                put("a", number(other.a - triangle.a))
                put("b", number(other.b - triangle.b))
                put("c", number(other.c - triangle.c))
                put("area", number(other.area - triangle.area))
                put("perimeter", number(other.perimeter - triangle.perimeter))
            })
        }
    }

    return JSONObject().apply {
        put("schema", "triangle-lab.geometry-export.v1")
        put("application", "Triangle Lab")
        put("exported_at_epoch_ms", System.currentTimeMillis())
        put("coordinate_system", "2D Euclidean Cartesian")
        put("length_units", "unspecified")
        put("side_convention", "a=BC, b=CA, c=AB")
        put("current_triangle", current)
        put("comparison", comparisonData ?: JSONObject.NULL)
        put("display_options", JSONObject().apply {
            put("altitudes", options.altitudes)
            put("vertex_bisectors", options.vertexBisectors)
            put("center_radii", options.centerRadii)
            put("centers", options.centers)
            put("internal_angles", options.internalAngles)
            put("external_angles", options.externalAngles)
            put("side_extensions", options.sideExtensions)
            put("side_labels", options.sideLabels)
        })
    }
}
