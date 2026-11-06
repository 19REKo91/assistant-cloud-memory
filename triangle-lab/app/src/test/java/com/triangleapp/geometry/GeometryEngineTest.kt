package com.triangleapp.geometry

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.abs

class GeometryEngineTest {
    @Test fun sideConventionProducesExpectedLengths() {
        val t = GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!
        assertEquals(5.0, t.a, 1e-9)
        assertEquals(4.0, t.b, 1e-9)
        assertEquals(3.0, t.c, 1e-9)
        assertEquals(6.0, t.area, 1e-9)
    }

    @Test fun rejectsInvalidSides() {
        assertNull(GeometryEngine.triangleFromSides(1.0, 2.0, 3.0))
        assertNull(GeometryEngine.triangleFromSides(0.0, 2.0, 2.0))
        assertNull(GeometryEngine.triangleFromSides(Double.NaN, 2.0, 2.0))
        assertNull(GeometryEngine.triangleFromSides(Double.POSITIVE_INFINITY, 2.0, 2.0))
    }

    @Test fun angleConstructionHonorsReferenceSide() {
        val t = GeometryEngine.triangleFromAngles(90.0, 45.0, 'c', 10.0)!!
        assertEquals(10.0, t.c, 1e-8)
        assertEquals(90.0, t.angleA, 1e-7)
        assertEquals(45.0, t.angleB, 1e-7)
        assertEquals(45.0, t.angleC, 1e-7)
    }

    @Test fun altitudeFootMayLieOutsideSegmentForObtuseTriangle() {
        val t = Triangle(Vec2(0.0, 0.0), Vec2(4.0, 0.0), Vec2(-1.0, 2.0))
        val foot = t.footFromVertex('C')!!
        assertTrue(foot.x < 0.0)
        assertEquals(0.0, foot.y, 1e-9)
    }

    @Test fun centersSatisfyKnownEquilateralCase() {
        val h = kotlin.math.sqrt(3.0)
        val t = Triangle(Vec2(0.0, 0.0), Vec2(2.0, 0.0), Vec2(1.0, h))
        assertEquals(1.0, t.centroid.x, 1e-9)
        assertEquals(h / 3.0, t.centroid.y, 1e-9)
        assertEquals(1.0, t.incenter.x, 1e-9)
        assertEquals(h / 3.0, t.incenter.y, 1e-9)
        assertEquals(1.0, t.circumcenter.x, 1e-9)
        assertEquals(h / 3.0, t.circumcenter.y, 1e-9)
        assertEquals(1.0, t.orthocenter.x, 1e-9)
        assertEquals(h / 3.0, t.orthocenter.y, 1e-9)
    }

    @Test fun bisectorFootUsesAngleBisectorTheorem() {
        val t = GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!
        val p = t.bisectorFoot('A')!!
        assertEquals(0.0, dist(t.B, p) / dist(p, t.C) - t.c / t.b, 1e-9)
    }
    @Test fun angleSumIs180AndSidesArePreserved() {
        val t = GeometryEngine.triangleFromSides(7.0, 6.0, 5.0)!!
        assertEquals(180.0, t.angleA + t.angleB + t.angleC, 1e-8)
        assertEquals(7.0, t.a, 1e-8)
        assertEquals(6.0, t.b, 1e-8)
        assertEquals(5.0, t.c, 1e-8)
    }

    @Test fun rejectsNonFiniteAnglesAndUnknownReferenceSide() {
        assertNull(GeometryEngine.triangleFromAngles(Double.NaN, 30.0, 'c', 5.0))
        assertNull(GeometryEngine.triangleFromAngles(60.0, 60.0, 'x', 5.0))
        assertNull(GeometryEngine.triangleFromAngles(60.0, 60.0, 'c', Double.POSITIVE_INFINITY))
    }

    @Test fun rescalingKeepsAnglesAndSetsSelectedSide() {
        val original = GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!
        val scaled = GeometryEngine.rescaleToReference(original, 'b', 12.0)!!
        assertEquals(12.0, scaled.b, 1e-8)
        assertEquals(original.angleA, scaled.angleA, 1e-8)
        assertEquals(original.angleB, scaled.angleB, 1e-8)
        assertEquals(original.angleC, scaled.angleC, 1e-8)
    }

    @Test fun rejectsCollinearCoordinates() {
        val t = Triangle(Vec2(0.0, 0.0), Vec2(1.0, 1.0), Vec2(2.0, 2.0))
        assertTrue(t.isDegenerate)
    }

    @Test fun allThreeBisectorFeetDivideOppositeSidesCorrectly() {
        val t = GeometryEngine.triangleFromSides(7.0, 6.0, 5.0)!!
        val a = t.bisectorFoot('A')!!
        val b = t.bisectorFoot('B')!!
        val c = t.bisectorFoot('C')!!
        assertEquals(t.c / t.b, dist(t.B, a) / dist(a, t.C), 1e-8)
        assertEquals(t.a / t.c, dist(t.C, b) / dist(b, t.A), 1e-8)
        assertEquals(t.b / t.a, dist(t.A, c) / dist(c, t.B), 1e-8)
    }

    @Test fun constructionIsScaleAwareForVerySmallTriangles() {
        val t = GeometryEngine.triangleFromSides(5e-12, 4e-12, 3e-12)!!
        assertFalse(t.isDegenerate)
        assertEquals(5e-12, t.a, 1e-22)
        assertEquals(4e-12, t.b, 1e-22)
        assertEquals(3e-12, t.c, 1e-22)
        assertEquals(90.0, t.angleA, 1e-7)
        assertEquals(1.5e-12, t.circumcenter.x, 1e-21)
        assertEquals(2.0e-12, t.circumcenter.y, 1e-21)
        assertEquals(0.0, t.orthocenter.x, 1e-21)
        assertEquals(0.0, t.orthocenter.y, 1e-21)
    }

    @Test fun centersRemainStableWhenCoordinatesAreFarFromOrigin() {
        val origin = 1e12
        val t = Triangle(
            Vec2(origin, origin),
            Vec2(origin + 3.0, origin),
            Vec2(origin, origin + 4.0)
        )
        assertEquals(origin + 1.0, t.centroid.x, 1e-3)
        assertEquals(origin + 4.0 / 3.0, t.centroid.y, 1e-3)
        assertEquals(origin + 1.0, t.incenter.x, 1e-3)
        assertEquals(origin + 1.0, t.incenter.y, 1e-3)
        assertEquals(origin + 1.5, t.circumcenter.x, 1e-3)
        assertEquals(origin + 2.0, t.circumcenter.y, 1e-3)
        assertEquals(origin, t.orthocenter.x, 1e-3)
        assertEquals(origin, t.orthocenter.y, 1e-3)
    }

    @Test fun centroidSplitsTriangleIntoThreeEqualAreaRegions() {
        val t = GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!
        val inner = t.internalTriangles()
        assertEquals(listOf("ABG", "ACG", "BCG"), inner.map { it.name })
        assertEquals(3, inner.size)
        inner.forEach { item ->
            assertEquals(t.area / 3.0, item.triangle.area, 1e-9)
            assertEquals(180.0, item.triangle.angleA + item.triangle.angleB + item.triangle.angleC, 1e-8)
        }
        assertEquals(t.area, inner.sumOf { it.triangle.area }, 1e-9)
    }

    @Test fun sixCentroidSectorsArePositiveAndSumToFullTurn() {
        val t = GeometryEngine.triangleFromSides(5.0, 4.0, 3.0)!!
        val sectors = t.centroidSectors()
        assertEquals(6, sectors.size)
        sectors.forEach {
            assertTrue(it.angleDegrees > 0.0)
            assertTrue(it.angleDegrees < 180.0)
        }
        assertEquals(360.0, sectors.sumOf { it.angleDegrees }, 1e-8)
        assertEquals(6, sectors.map { it.startRay }.toSet().size)
    }

}
