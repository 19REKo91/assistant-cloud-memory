# Triangle Lab

Android-only Kotlin + Jetpack Compose geometry application.

This directory isolates the Triangle Lab project from the repository's existing memory/archive content.

## Current implemented features

- Side-length input with triangle-inequality validation.
- Angle input with selectable fixed reference side.
- Cartesian coordinate input for A, B and C.
- Separate comparison-triangle input and dashed overlay.
- Distinct colors for the three sides.
- Optional altitudes, vertex angle bisectors, incenter-to-side radii, centers G/I/O/H, internal/external angle indicators, and side labels.
- Measurements for sides, angles, perimeter, area and triangle centers.
- Pinch zoom, drag pan and view reset.
- Save/load/delete triangles using on-device preferences.
- JSON clipboard import/export.
- Arabic-first interface with an English/Arabic text toggle.
- Geometry regression tests and a GitHub Actions Android build workflow.

## Build verification

The GitHub Actions workflow is `.github/workflows/triangle-lab-android-build.yml`. It runs unit tests and assembles a debug APK. A successful workflow run is required before the project can be called build-verified.

## Package root

`com.triangleapp`

Geometry package: `com.triangleapp.geometry`

## Known work remaining

- Complete end-to-end UI verification on a physical Android device.
- Confirm the final CI build and inspect the produced APK artifact.
- Review coordinate editing, comparison visualization and all display controls against the agreed original specification.
