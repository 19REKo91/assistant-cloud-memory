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
}
