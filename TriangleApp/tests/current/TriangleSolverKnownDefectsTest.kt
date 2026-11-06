package com.example.triangleapp

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs

/**
 * Group B: characterization tests for known defects in the CURRENT implementation.
 *
 * A passing test here means the defect was reproduced. These are not product acceptance
 * tests. After a solver fix, replace each characterization with a test that expects
 * rejection or finite, consistent geometry.
 */
class TriangleSolverKnownDefectsTest {

    @Test
    fun currentSolverAcceptsNaNSideAndProducesNonFiniteAngles() {
        val t = TriangleSolver.fromSides(Float.NaN, 2f, 2f)
        assertNotNull(t)
        t!!
        assertTrue(!t.A.isFinite() || !t.B.isFinite() || !t.C.isFinite())
    }

    @Test
    fun currentSolverAcceptsNaNReferenceSideAndProducesNonFiniteLengths() {
        val t = TriangleSolver.fromAngles(60f, 60f, 60f, Float.NaN)
        assertNotNull(t)
        t!!
        assertTrue(!t.a.isFinite() || !t.b.isFinite() || !t.c.isFinite())
    }

    @Test
    fun currentSolverRejectsPositiveInfinitySideThroughTriangleInequality() {
        // This documents current behavior only. It does NOT prove that finite-value
        // validation exists; rejection happens as a side-effect of the inequality check.
        assertNull(TriangleSolver.fromSides(2f, 2f, Float.POSITIVE_INFINITY))
    }

    @Test
    fun currentAngleSolverAcceptsInconsistentAngleSumWithinHalfDegree() {
        val t = TriangleSolver.fromAngles(60f, 60f, 60.4f, 5f)
        assertNotNull(t)
        t!!
        assertTrue(abs(t.A + t.B + t.C - 180f) > 0.1f)
    }

    @Test
    fun currentFloatSolverProducesNonFiniteAnglesAtExtremeScales() {
        val large = TriangleSolver.fromSides(1e20f, 1e20f, 1e20f)
        val tiny = TriangleSolver.fromSides(1e-25f, 1e-25f, 1e-25f)
        assertNotNull(large)
        assertNotNull(tiny)
        large!!
        tiny!!
        val largeBroken = !large.A.isFinite() || !large.B.isFinite() || !large.C.isFinite()
        val tinyBroken = !tiny.A.isFinite() || !tiny.B.isFinite() || !tiny.C.isFinite()
        assertTrue("Expected an extreme-scale Float precision failure", largeBroken || tinyBroken)
    }
}
