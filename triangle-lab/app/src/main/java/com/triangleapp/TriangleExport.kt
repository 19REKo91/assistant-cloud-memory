package com.triangleapp

import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import com.triangleapp.geometry.centroidSectors
import com.triangleapp.geometry.internalTriangles
import org.json.JSONArray
import org.json.JSONObject

/** Creates a machine-readable snapshot of the displayed geometry. */
internal fun triangleExportJson(triangle: Triangle, comparison: Triangle?, options: DrawOptions): JSONObject {
    fun number(value: Double): Any = if (value.isFinite()) value else JSONObject.NULL
    fun point(p: Vec2) = JSONObject().apply { put("x", number(p.x)); put("y", number(p.y)) }

    fun triangleData(t: Triangle): JSONObject {
        val angles = listOf(t.angleA, t.angleB, t.angleC)
        val maxSide = maxOf(t.a, t.b, t.c)
        val tolerance = maxSide * 1e-8
        val sideType = when {
            !maxSide.isFinite() || maxSide <= 0.0 -> "unknown"
            maxOf(kotlin.math.abs(t.a - t.b), kotlin.math.abs(t.b - t.c), kotlin.math.abs(t.c - t.a)) <= tolerance -> "equilateral"
            kotlin.math.abs(t.a - t.b) <= tolerance || kotlin.math.abs(t.b - t.c) <= tolerance || kotlin.math.abs(t.c - t.a) <= tolerance -> "isosceles"
            else -> "scalene"
        }
        val angleType = when {
            angles.any { !it.isFinite() } -> "unknown"
            angles.any { kotlin.math.abs(it - 90.0) <= 1e-7 } -> "right"
            angles.all { it < 90.0 } -> "acute"
            else -> "obtuse"
        }
        return JSONObject().apply {
            put("vertices", JSONObject().apply { put("A", point(t.A)); put("B", point(t.B)); put("C", point(t.C)) })
            put("sides", JSONObject().apply { put("a_BC", number(t.a)); put("b_CA", number(t.b)); put("c_AB", number(t.c)) })
            put("internal_angles_degrees", JSONObject().apply { put("A", number(t.angleA)); put("B", number(t.angleB)); put("C", number(t.angleC)) })
            put("external_angles_degrees", JSONObject().apply { put("A", number(180.0 - t.angleA)); put("B", number(180.0 - t.angleB)); put("C", number(180.0 - t.angleC)) })
            put("angle_sum_degrees", number(angles.sum()))
            put("perimeter", number(t.perimeter))
            put("area", number(t.area))
            put("centers", JSONObject().apply {
                put("G_centroid", point(t.centroid)); put("I_incenter", point(t.incenter))
                put("O_circumcenter", point(t.circumcenter)); put("H_orthocenter", point(t.orthocenter))
            })
            put("classification", JSONObject().apply { put("by_sides", sideType); put("by_angles", angleType) })
        }
    }

    fun innerData(name: String, t: Triangle, labels: List<String>) = JSONObject().apply {
        put("name", name)
        put("vertices", JSONObject().apply { put(labels[0], point(t.A)); put(labels[1], point(t.B)); put(labels[2], point(t.C)) })
        put("side_lengths", JSONObject().apply {
            put(labels[0] + labels[1], number(t.c))
            put(labels[1] + labels[2], number(t.a))
            put(labels[2] + labels[0], number(t.b))
        })
        put("internal_angles_degrees", JSONObject().apply {
            put(labels[0], number(t.angleA)); put(labels[1], number(t.angleB)); put(labels[2], number(t.angleC))
        })
        put("angle_sum_degrees", number(t.angleA + t.angleB + t.angleC))
        put("area", number(t.area))
        put("perimeter", number(t.perimeter))
    }

    val inner = triangle.internalTriangles()
    val sectors = triangle.centroidSectors()
    val comparisonData = comparison?.let { other ->
        JSONObject().apply {
            put("triangle", triangleData(other))
            put("differences_comparison_minus_current", JSONObject().apply {
                put("a", number(other.a - triangle.a)); put("b", number(other.b - triangle.b)); put("c", number(other.c - triangle.c))
                put("area", number(other.area - triangle.area)); put("perimeter", number(other.perimeter - triangle.perimeter))
            })
        }
    }
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
            put("internal_triangles", JSONArray().apply { inner.forEach { put(innerData(it.name, it.triangle, it.vertexLabels)) } })
            put("six_sectors_around_G", JSONObject().apply {
                put("sectors", JSONArray().apply {
                    sectors.forEach { sector -> put(JSONObject().apply {
                        put("start_ray", sector.startRay); put("end_ray", sector.endRay); put("angle_degrees", number(sector.angleDegrees))
                    }) }
                })
                put("angle_sum_degrees", number(sectors.sumOf { it.angleDegrees }))
            })
        })
        put("comparison", comparisonData ?: JSONObject.NULL)
        put("display_options", JSONObject().apply {
            put("altitudes", options.altitudes); put("vertex_bisectors", options.vertexBisectors)
            put("center_radii", options.centerRadii); put("centers", options.centers)
            put("internal_angles", options.internalAngles); put("centroid_angles", options.centroidAngles)
            put("external_angles", options.externalAngles); put("side_extensions", options.sideExtensions)
            put("side_labels", options.sideLabels)
        })
    }
}
