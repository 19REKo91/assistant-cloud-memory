package com.triangleapp

import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class TriangleExportTest {
    private fun sampleTriangle() = Triangle(
        Vec2(2.0, 3.0),
        Vec2(14.0, 3.0),
        Vec2(8.0, 11.0)
    )

    @Test fun exportsPrimaryMeasurementsCentersAndCentroidPartition() {
        val exported = triangleExportJson(sampleTriangle(), emptyList(), DrawOptions())
        assertEquals("triangle-lab.geometry-export.v2", exported.getString("schema"))

        val primary = exported.getJSONObject("current_triangle")
        assertEquals(10.0, primary.getJSONObject("sides").getDouble("a"), 1e-9)
        assertEquals(10.0, primary.getJSONObject("sides").getDouble("b"), 1e-9)
        assertEquals(12.0, primary.getJSONObject("sides").getDouble("c"), 1e-9)
        assertEquals(48.0, primary.getDouble("area"), 1e-9)
        assertEquals(32.0, primary.getDouble("perimeter"), 1e-9)
        assertEquals(180.0, primary.getDouble("angle_sum_degrees"), 1e-8)
        assertTrue(primary.has("external_angles_degrees"))
        assertEquals(8.0, primary.getJSONObject("centers").getJSONObject("G_centroid").getDouble("x"), 1e-9)

        val centroid = exported.getJSONObject("centroid_G_analysis")
        val parts = centroid.getJSONArray("internal_triangles")
        assertEquals(3, parts.length())

        val abg = parts.getJSONObject(0)
        assertEquals("ABG", abg.getString("name"))
        assertEquals(6.565905201197403, abg.getJSONObject("side_lengths").getDouble("a"), 1e-8)
        assertEquals(6.565905201197403, abg.getJSONObject("side_lengths").getDouble("b"), 1e-8)
        assertEquals(12.0, abg.getJSONObject("side_lengths").getDouble("c"), 1e-9)
        assertEquals("G", abg.getJSONObject("angle_vertex_labels").getString("C"))
        assertEquals("isosceles", abg.getJSONObject("classification").getString("by_sides"))
        assertEquals("obtuse", abg.getJSONObject("classification").getString("by_angles"))

        val check = centroid.getJSONObject("area_check")
        assertEquals(16.0, parts.getJSONObject(0).getDouble("area"), 1e-9)
        assertEquals(16.0, parts.getJSONObject(1).getDouble("area"), 1e-9)
        assertEquals(16.0, parts.getJSONObject(2).getDouble("area"), 1e-9)
        assertEquals(48.0, check.getDouble("sum_of_internal_areas"), 1e-9)
        assertEquals(48.0, check.getDouble("original_area"), 1e-9)
        assertTrue(check.getBoolean("passed"))
    }

    @Test fun exportsEverySelectedComparisonAndItsDifferences() {
        val primary = sampleTriangle()
        val compareOne = Triangle(Vec2(0.0, 0.0), Vec2(8.0, 0.0), Vec2(4.0, 6.0))
        val compareTwo = Triangle(Vec2(1.0, 1.0), Vec2(11.0, 1.0), Vec2(6.0, 9.0))
        val exported = triangleExportJson(primary, listOf(compareOne, compareTwo), DrawOptions())
        val comparisons = exported.getJSONArray("comparisons")

        assertEquals(2, comparisons.length())
        assertEquals("Compare 1", comparisons.getJSONObject(0).getString("label"))
        assertEquals("Compare 2", comparisons.getJSONObject(1).getString("label"))
        assertTrue(comparisons.getJSONObject(0).getJSONObject("triangle").has("centers"))
        assertTrue(comparisons.getJSONObject(1).getJSONObject("differences_comparison_minus_primary").has("area"))
    }

    @Test fun exportedStructuredJsonStillImportsThroughExistingImporter() {
        val original = sampleTriangle()
        val exported = triangleExportJson(original, emptyList(), DrawOptions())
        val restored = triangleFromJson(JSONObject(exported.toString()))

        assertEquals(original.A.x, restored.A.x, 1e-9)
        assertEquals(original.A.y, restored.A.y, 1e-9)
        assertEquals(original.B.x, restored.B.x, 1e-9)
        assertEquals(original.B.y, restored.B.y, 1e-9)
        assertEquals(original.C.x, restored.C.x, 1e-9)
        assertEquals(original.C.y, restored.C.y, 1e-9)
    }
}
