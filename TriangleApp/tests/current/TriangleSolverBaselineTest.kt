package com.example.triangleapp

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs
import kotlin.math.sqrt

/**
 * Group A: baseline tests for the CURRENT TriangleSolver API.
 * These cover ordinary supported behavior only.
 */
class TriangleSolverBaselineTest {
    private fun distance(p: Vec, q: Vec): Double {
        val dx = p.x.toDouble() - q.x.toDouble()
        val dy = p.y.toDouble() - q.y.toDouble()
        return sqrt(dx * dx + dy * dy)
    }

    private fun assertNear(expected: Double, actual: Double, tolerance: Double = 1e-4) {
        assertTrue("Expected finite value, got $actual", actual.isFinite())
        assertTrue("Expected $expected ± $tolerance, got $actual",
            abs(expected - actual) <= tolerance)
    }

    private fun assertGeometryMatchesSideLengths(t: Triangle, tolerance: Double = 2e-4) {
        assertNear(t.a.toDouble(), distance(t.vB, t.vC), tolerance)
        assertNear(t.b.toDouble(), distance(t.vC, t.vA), tolerance)
        assertNear(t.c.toDouble(), distance(t.vA, t.vB), tolerance)
    }

    @Test
    fun equilateralTriangleHasThreeSixtyDegreeAngles() {
        val t = TriangleSolver.fromSides(5f, 5f, 5f)
        assertNotNull(t)
        t!!
        assertNear(60.0, t.A.toDouble())
        assertNear(60.0, t.B.toDouble())
        assertNear(60.0, t.C.toDouble())
        assertGeometryMatchesSideLengths(t)
    }

    @Test
    fun threeFourFiveTriangleHasOneRightAngle() {
        val t = TriangleSolver.fromSides(3f, 4f, 5f)
        assertNotNull(t)
        t!!
        assertNear(36.8698976, t.A.toDouble(), 2e-4)
        assertNear(53.1301024, t.B.toDouble(), 2e-4)
        assertNear(90.0, t.C.toDouble(), 2e-4)
        assertGeometryMatchesSideLengths(t)
    }

    @Test
    fun acuteAndObtuseTrianglesHaveConsistentCoordinates() {
        val acute = TriangleSolver.fromSides(5f, 6f, 7f)
        val obtuse = TriangleSolver.fromSides(2f, 3f, 4f)
        assertNotNull(acute)
        assertNotNull(obtuse)
        acute!!
        obtuse!!
        assertTrue(acute.A < 90f && acute.B < 90f && acute.C < 90f)
        assertTrue(obtuse.C > 90f)
        assertGeometryMatchesSideLengths(acute)
        assertGeometryMatchesSideLengths(obtuse)
    }

    @Test
    fun triangleInequalityRejectsDegenerateAndImpossibleSides() {
        assertNull(TriangleSolver.fromSides(1f, 2f, 3f))
        assertNull(TriangleSolver.fromSides(1f, 1f, 2f))
        assertNull(TriangleSolver.fromSides(1f, 2f, 4f))
        assertNull(TriangleSolver.fromSides(0f, 2f, 2f))
        assertNull(TriangleSolver.fromSides(-1f, 2f, 2f))
    }

    @Test
    fun angleSolverBuildsKnownTriangleForValidAnglesAndPositiveSideA() {
        val t = TriangleSolver.fromAngles(90f, 60f, 30f, 2f)
        assertNotNull(t)
        t!!
        assertNear(2.0, t.a.toDouble())
        assertNear(sqrt(3.0), t.b.toDouble())
        assertNear(1.0, t.c.toDouble())
        assertGeometryMatchesSideLengths(t)
    }

    @Test
    fun angleSolverRejectsClearlyInvalidInputs() {
        assertNull(TriangleSolver.fromAngles(90f, 90f, 1f, 2f))
        assertNull(TriangleSolver.fromAngles(90f, 90f, 0f, 2f))
        assertNull(TriangleSolver.fromAngles(-10f, 100f, 90f, 2f))
        assertNull(TriangleSolver.fromAngles(60f, 60f, 60f, 0f))
        assertNull(TriangleSolver.fromAngles(60f, 60f, 60f, -1f))
    }

    @Test
    fun currentApiRoundTripsSidesThroughAnglesUsingSideAAsReference() {
        val original = TriangleSolver.fromSides(3f, 4f, 5f)
        assertNotNull(original)
        original!!
        val rebuilt = TriangleSolver.fromAngles(
            original.A, original.B, original.C, original.a
        )
        assertNotNull(rebuilt)
        rebuilt!!
        assertNear(original.a.toDouble(), rebuilt.a.toDouble())
        assertNear(original.b.toDouble(), rebuilt.b.toDouble())
        assertNear(original.c.toDouble(), rebuilt.c.toDouble())
    }

    @Test
    fun incenterHasEqualPerpendicularDistanceToAllThreeSides() {
        val t = TriangleSolver.fromSides(3f, 4f, 5f)
        assertNotNull(t)
        t!!
        val i = t.incenter
        val ab = t.vB - t.vA
        val bc = t.vC - t.vB
        val ca = t.vA - t.vC

        fun distanceToLine(p: Vec, start: Vec, direction: Vec): Double {
            val relative = p - start
            return kotlin.math.abs(cross(direction, relative).toDouble()) /
                direction.length().toDouble()
        }

        val d1 = distanceToLine(i, t.vA, ab)
        val d2 = distanceToLine(i, t.vB, bc)
        val d3 = distanceToLine(i, t.vC, ca)
        assertTrue(abs(d1 - d2) < 1e-4)
        assertTrue(abs(d2 - d3) < 1e-4)
    }

    @Test
    fun raySegmentIntersectionFindsForwardHitAndRejectsBehindRay() {
        val origin = Vec(0f, 0f)
        val direction = Vec(1f, 0f)
        val hit = raySegmentIntersect(origin, direction, Vec(2f, -1f), Vec(2f, 1f))
        assertNotNull(hit)
        hit!!
        assertNear(2.0, hit.x.toDouble())
        assertNear(0.0, hit.y.toDouble())
        assertNull(raySegmentIntersect(origin, direction, Vec(-2f, -1f), Vec(-2f, 1f)))
    }
}
