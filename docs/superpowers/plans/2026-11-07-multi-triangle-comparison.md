# Multi-triangle comparison Implementation Plan

> **For agentic workers:** Use the execution plan task-by-task.

**Goal:** Add unlimited saved triangles and a clear comparison workspace with at most three comparison overlays.

**Architecture:** Keep the active triangle separate from the saved collection. Store the selected comparison geometries in a dedicated list, persist them separately, and pass a list of colored comparison entries to the canvas.

**Tech Stack:** Kotlin, Jetpack Compose, SharedPreferences, org.json, existing Android Gradle test workflow.

**Spec:** docs/superpowers/specs/2026-11-07-multi-triangle-comparison-design.md

## Global Constraints
- Preserve current triangle geometry and JSON interchange behavior.
- Preserve legacy single-comparison data during migration.
- Limit simultaneous comparison overlays to three.
- Do not discard saved triangles when deselected from comparison.

## Review Focus
- Fourth selection attempt leaves the existing three unchanged.
- Duplicate saved geometry does not consume multiple comparison slots.
- Deleting a saved triangle removes it from the active comparison selection.
- Old single-comparison preference is migrated only when the new preference is absent.
- Extreme or differently oriented triangles remain visible in the canvas viewport.

---

### Task 1: Comparison selection rules

**Files:**
- Create: `triangle-lab/app/src/main/java/com/triangleapp/ComparisonSelection.kt`
- Test: `triangle-lab/app/src/test/java/com/triangleapp/ComparisonSelectionTest.kt`

- [ ] Add tests for add, remove, duplicate, three-item cap, and fourth-item rejection.
- [ ] Implement the smallest pure Kotlin selection helper.
- [ ] Run unit tests.

### Task 2: UI, persistence, and canvas

**Files:**
- Modify: `triangle-lab/app/src/main/java/com/triangleapp/MainActivity.kt`
- Modify: `triangle-lab/app/src/main/java/com/triangleapp/TriangleCanvas.kt`
- Modify: `triangle-lab/README.md`

- [ ] Replace the single comparison state with a list of up to three selected triangles.
- [ ] Add/remove comparison controls to each saved-triangle row.
- [ ] Preserve unlimited save/load/delete behavior.
- [ ] Persist selected comparison triangles and migrate the legacy single comparison preference.
- [ ] Render up to three overlays with separate colors and per-triangle measurement deltas.
- [ ] Include every comparison overlay in canvas viewport calculation.
- [ ] Run all unit tests and the Android debug APK build.

### Task 3: Documentation and review

**Files:**
- Update: `triangle-lab/README.md`
- Update: this implementation record.

- [ ] Document the saved-versus-selected distinction and three-overlay limit.
- [ ] Review the full diff and verify the final workflow result.


---

## Follow-up: comparison centroid visibility (2026-11-07)

- Updated `TriangleCanvas.kt` so each comparison overlay also displays its own centroid marker and label (`G1`, `G2`, `G3`) in that overlay's color.
- When centroid divisions are enabled, dashed segments connect that comparison triangle's vertices to its own centroid.
- The comparison centroid is shown whenever either the Centers or Centroid divisions display option is enabled.
- Primary triangle rendering and comparison selection behavior remain unchanged.
- Commit: `00cefab858d6839b3e1e404cfb03314a6f15de86`.
- Android CI verification is pending; no physical-device test has been performed yet.
