package com.triangleapp

import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs

/**
 * Serializes the same geometry values used by the measurements panel.
 * Coordinates remain at current_triangle.vertices.A/B/C so existing structured
 * and legacy import paths do not need to change.
 */
internal fun triangleExportJson(
    triangle: Triangle,
    comparisons: List<Triangle>,
    options: DrawOptions
): JSONObject {
    fun number(value: Double): Any =
        if (value.isFinite()) value else JSONObject.NULL

    fun point(value: Vec2): JSONObject = JSONObject().apply {
        put("x", number(value.x))
        put("y", number(value.y))
    }

    fun classification(value: Triangle): JSONObject {
        val scale = maxOf(value.a, value.b, value.c)
        val tolerance = scale * 1e-8
        val sidesEqual = listOf(
            abs(value.a - value.b) <= tolerance,
            abs(value.b - value.c) <= tolerance,
            abs(value.c - value.a) <= tolerance
        )
        val sideType = when {
            sidesEqual.all { it } -> "equilateral"
            sidesEqual.any { it } -> "isosceles"
            else -> "scalene"
        }
        val angles = listOf(value.angleA, value.angleB, value.angleC)
        val angleType = when {
            angles.any { !it.isFinite() } -> "unknown"
            abs((angles.maxOrNull() ?: Double.NaN) - 90.0) <= 1e-7 -> "right"
            angles.all { it < 90.0 } -> "acute"
            else -> "obtuse"
        }
        return JSONObject().apply {
            put("by_sides", sideType)
            put("by_angles", angleType)
        }
    }

    fun triangleData(value: Triangle): JSONObject {
        return JSONObject().apply {
            put("vertices", JSONObject().apply {
                put("A", point(value.A))
                put("B", point(value.B))
                put("C", point(value.C))
            })
            put("sides", JSONObject().apply {
                put("a", number(value.a))
                put("b", number(value.b))
                put("c", number(value.c))
                put("a_segment", "BC")
                put("b_segment", "CA")
                put("c_segment", "AB")
            })
            put("internal_angles_degrees", JSONObject().apply {
                put("A", number(value.angleA))
                put("B", number(value.angleB))
                put("C", number(value.angleC))
            })
            put("external_angles_degrees", JSONObject().apply {
                put("A", number(value.externalAngleA))
                put("B", number(value.externalAngleB))
                put("C", number(value.externalAngleC))
            })
            put("angle_sum_degrees", number(value.angleA + value.angleB + value.angleC))
            put("perimeter", number(value.perimeter))
            put("area", number(value.area))
            put("centers", JSONObject().apply {
                put("G_centroid", point(value.centroid))
                put("I_incenter", point(value.incenter))
                put("O_circumcenter", point(value.circumcenter))
                put("H_orthocenter", point(value.orthocenter))
            })
            put("classification", classification(value))
        }
    }

    val innerParts = triangle.centroidSubtriangles()
    val innerArray = JSONArray()
    innerParts.forEach { (name, part) ->
        val labels = listOf(name.substring(0, 1), name.substring(1, 2), "G")
        innerArray.put(JSONObject().apply {
            put("name", name)
            put("vertices", JSONObject().apply {
                put(labels[0], point(part.A))
                put(labels[1], point(part.B))
                put(labels[2], point(part.C))
            })
            // A/B/C here are the first, second and third vertices of this
            // subtriangle; vertex_labels maps them back to the original A/B/C/G.
            put("vertex_labels", JSONArray(labels))
            put("side_lengths", JSONObject().apply {
                put("a", number(part.a))
                put("b", number(part.b))
                put("c", number(part.c))
            })
            put("side_segments", JSONObject().apply {
                put("a", labels[1] + labels[2])
                put("b", labels[2] + labels[0])
                put("c", labels[0] + labels[1])
            })
            put("internal_angles_degrees", JSONObject().apply {
                put("A", number(part.angleA))
                put("B", number(part.angleB))
                put("C", number(part.angleC))
            })
            put("angle_vertex_labels", JSONObject().apply {
                put("A", labels[0])
                put("B", labels[1])
                put("C", labels[2])
            })
            put("angle_sum_degrees", number(part.angleA + part.angleB + part.angleC))
            put("area", number(part.area))
            put("perimeter", number(part.perimeter))
            put("classification", classification(part))
        })
    }

    val innerArea = innerParts.sumOf { it.second.area }
    val areaTolerance = maxOf(1.0, triangle.area) * 1e-9
    val areaDifference = abs(innerArea - triangle.area)

    val comparisonArray = JSONArray()
    val comparisonObjects = comparisons.take(ComparisonSelection.MAX_COMPARISONS).mapIndexed { index, other ->
        JSONObject().apply {
            put("index", index + 1)
            put("label", "Compare ${index + 1}")
            put("triangle", triangleData(other))
            put("differences_comparison_minus_primary", JSONObject().apply {
                put("a", number(other.a - triangle.a))
                put("b", number(other.b - triangle.b))
                put("c", number(other.c - triangle.c))
                put("area", number(other.area - triangle.area))
                put("perimeter", number(other.perimeter - triangle.perimeter))
            })
        }
    }
    comparisonObjects.forEach { comparisonArray.put(it) }

    return JSONObject().apply {
        put("schema", "triangle-lab.geometry-export.v2")
        put("application", "Triangle Lab")
        put("exported_at_epoch_ms", System.currentTimeMillis())
        put("coordinate_system", "2D Euclidean Cartesian")
        put("length_units", "unspecified")
        put("side_convention", "a=BC, b=CA, c=AB")
        put("current_triangle", triangleData(triangle))
        put("centroid_G_analysis", JSONObject().apply {
            put("G", point(triangle.centroid))
            put("internal_triangles", innerArray)
            put("area_check", JSONObject().apply {
                put("sum_of_internal_areas", number(innerArea))
                put("original_area", number(triangle.area))
                put("absolute_difference", number(areaDifference))
                put("tolerance", number(areaTolerance))
                put("passed", areaDifference <= areaTolerance)
            })
        })
        // Keep a single-comparison alias for consumers of the earlier v2 draft,
        // while exporting every visible comparison in the full array.
        put("comparison", comparisonObjects.firstOrNull() ?: JSONObject.NULL)
        put("comparisons", comparisonArray)
        put("display_options", JSONObject().apply {
            put("altitudes", options.altitudes)
            put("vertex_bisectors", options.vertexBisectors)
            put("center_radii", options.centerRadii)
            put("centers", options.centers)
            put("centroid_divisions", options.centroidDivisions)
            put("internal_angles", options.internalAngles)
            put("external_angles", options.externalAngles)
            put("angle_labels", options.angleLabels)
            put("side_extensions", options.sideExtensions)
            put("side_labels", options.sideLabels)
        })
    }
}
