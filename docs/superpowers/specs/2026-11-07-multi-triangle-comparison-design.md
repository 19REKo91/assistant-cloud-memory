# Multi-triangle comparison — design

## Intent
Allow users to keep any practical number of saved triangles while comparing no more than three saved triangles against the one active primary triangle at a time. This expands comparison without overcrowding the drawing or changing the geometry model.

## Goals
- Keep one active primary triangle.
- Retain the existing saved-triangle collection without a fixed comparison cap.
- Select up to three distinct saved triangles for simultaneous comparison.
- Add/remove a saved triangle from the comparison set without deleting or rewriting its saved geometry.
- Persist the comparison selection across app restarts.
- Give each comparison overlay a stable, distinct color and label.
- Show measurement differences for each selected comparison triangle.

## Non-goals
- More than three comparison overlays at once.
- Replacing or changing geometry formulas.
- Changing the existing JSON triangle interchange format.
- Introducing a database or cloud synchronization.

## Constraints and decisions
- Reuse the existing Compose, SharedPreferences, and JSON persistence patterns.
- Preserve the legacy single comparison preference by migrating it into the new comparison list when the new preference is absent.
- A duplicate geometry is treated as the same selected comparison item; the saved list may still contain duplicate saved entries.
- The primary triangle remains independently editable and is not counted among the three comparison slots.
- Existing saved triangles remain available even when not selected for comparison.

## Approaches
- Keep a single comparison slot: rejected because it does not meet the requested comparison workflow.
- Show all saved triangles simultaneously: rejected because it risks visual clutter.
- Keep unlimited saved triangles and select up to three for display: chosen because it separates storage from the visible comparison set and preserves screen clarity.

## Acceptance criteria
- The user can save more than three triangles.
- The user can select up to three distinct saved triangles for comparison.
- Attempting to select a fourth does not alter the existing three and gives a clear message.
- Removing one selected triangle frees a slot without deleting the saved triangle.
- Selection and saved triangles survive process/app restart.
- The canvas renders each selected triangle in a different color and includes all of them in viewport bounds.
- Differences are shown separately against the primary triangle.
- Existing single-comparison saved state is migrated safely.
