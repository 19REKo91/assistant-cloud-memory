package com.triangleapp

import com.triangleapp.geometry.Triangle

data class ComparisonSelectionResult(
    val triangles: List<Triangle>,
    val changed: Boolean,
    val limitReached: Boolean
)

/** Keeps the visible comparison set bounded independently of the saved-triangle library. */
object ComparisonSelection {
    const val MAX_COMPARISONS = 3

    fun toggle(current: List<Triangle>, candidate: Triangle): ComparisonSelectionResult {
        if (candidate in current) {
            return ComparisonSelectionResult(current.filterNot { it == candidate }, changed = true, limitReached = false)
        }
        if (current.size >= MAX_COMPARISONS) {
            return ComparisonSelectionResult(current, changed = false, limitReached = true)
        }
        return ComparisonSelectionResult(current + candidate, changed = true, limitReached = false)
    }
}
