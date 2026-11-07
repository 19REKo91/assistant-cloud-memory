package com.triangleapp

import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import org.junit.Assert.*
import org.junit.Test

class ComparisonSelectionTest {
    private fun triangle(x: Double) = Triangle(
        Vec2(x, 0.0), Vec2(x + 3.0, 0.0), Vec2(x, 4.0)
    )

    @Test fun allowsThreeDistinctComparisonTriangles() {
        val result = ComparisonSelection.toggle(emptyList(), triangle(0.0))
        val second = ComparisonSelection.toggle(result.triangles, triangle(10.0))
        val third = ComparisonSelection.toggle(second.triangles, triangle(20.0))
        assertEquals(3, third.triangles.size)
        assertTrue(third.changed)
        assertFalse(third.limitReached)
    }

    @Test fun rejectsFourthWithoutChangingExistingSelection() {
        val first = triangle(0.0)
        val second = triangle(10.0)
        val third = triangle(20.0)
        val current = listOf(first, second, third)
        val result = ComparisonSelection.toggle(current, triangle(30.0))
        assertEquals(current, result.triangles)
        assertFalse(result.changed)
        assertTrue(result.limitReached)
    }

    @Test fun togglingSelectedTriangleRemovesItAndFreesSlot() {
        val first = triangle(0.0)
        val current = listOf(first, triangle(10.0), triangle(20.0))
        val removed = ComparisonSelection.toggle(current, first)
        assertEquals(2, removed.triangles.size)
        assertTrue(removed.changed)
        assertFalse(removed.limitReached)
        val added = ComparisonSelection.toggle(removed.triangles, triangle(30.0))
        assertEquals(3, added.triangles.size)
    }

    @Test fun togglingDuplicateGeometryRemovesExistingSelection() {
        val first = triangle(0.0)
        val result = ComparisonSelection.toggle(listOf(first), triangle(0.0))
        assertTrue(result.triangles.isEmpty())
        assertTrue(result.changed)
        assertFalse(result.limitReached)
    }
}
