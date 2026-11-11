# Triangle Lab

Android-only Kotlin + Jetpack Compose geometry application.

The project is isolated in `triangle-lab/` inside `19REKo91/assistant-cloud-memory`. Existing archive and memory files outside this directory remain untouched.

## Implemented features

- Side-length, angle/reference-side, Cartesian-coordinate and comparison input modes.
- Live validity feedback and automatic field synchronization when changing modes.
- Direct dragging of vertices A, B and C, with synchronized side, angle and coordinate values.
- Pinch zoom, drag pan, zoom buttons and view reset.
- Three distinct side colors, optional side extensions, altitudes, colored vertex bisectors, incenter-to-side radii, centers G/I/O/H, internal and external angle arcs, and side labels.
- Dashed comparison-triangle overlay and numerical differences for sides, area and perimeter.
- Measurements for sides, angles, perimeter, area and triangle centers.
- Save/load/delete triangles; current and comparison triangles restore after relaunch.
- Geometry JSON clipboard export/import: vertex coordinates, side lengths, internal/external angles, perimeter, area, centers G/I/O/H, comparison results, the three centroid regions ABG/ACG/BCG, and all six sectors around G. Length units are explicitly marked as unspecified.
- Arabic/English interface text, RTL/LTR layout, and Arabic-Indic/Persian numeric input support.

## Geometry and tests

The geometry layer includes scale-aware validation and coordinate construction, altitude projection to the supporting line, corrected angle-bisector points, and numerically stable triangle centers.

There are 15 geometry regression tests. The GitHub Actions workflow runs unit tests and assembles a debug APK:

`.github/workflows/triangle-lab-android-build.yml`

## Latest verified build

- Workflow run 39: [view GitHub Actions run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/42142407696)
- Commit tested: `f590a785cf4775e771815ee26d00973e3d3b98e5`
- Unit tests: passed.
- Android debug APK assembly: passed.
- Artifact: `triangle-lab-debug-apk` (debug-signed APK).

## Verification limitation

Automated build and geometry tests passed. The app has not been installed or exercised on the target physical phone. Touch behavior, screen layout, clipboard integration and persistence after a real process restart therefore remain unverified. A release-signed APK requires a stable signing key; the current CI artifact is debug-signed.


## Centroid subdivision and G-angle analysis

- The centroid G divides the original triangle into ABG, ACG and BCG; each is calculated as a real triangle with its own side lengths, three angles, area and perimeter.
- The six sectors around G are formed by the six rays toward A, B, C and the three opposite-side midpoints. Their individual measures and their 360° total are exported.
- The drawing has a separate “Angles around G” switch for the six arcs and labels.
- Regression tests verify equal one-third areas, 180° sums in each inner triangle, six positive sectors and a 360° total.
- These additions are on `feature/triangle-lab-complete-json-export`; verification is pending until the workflow completes.
