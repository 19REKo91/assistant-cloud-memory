# Triangle Lab — Repair and verification log

## Workspace

- Project root: `triangle-lab/` in `19REKo91/assistant-cloud-memory`.
- Existing archive and memory files outside this directory were not modified.
- Android package/application ID: `com.triangleapp`.
- Stack: Kotlin, Jetpack Compose, Material 3, Android SDK 35, Java 17.

## Implemented application features

- Four input modes: side lengths, two angles plus a selectable fixed reference side, Cartesian coordinates, and comparison triangle.
- Live validation while editing; explicit Apply and Reset actions.
- Switching input modes repopulates the fields from the current triangle.
- Drag A/B/C to reshape the triangle; side, angle and coordinate fields synchronize after each valid move. Degenerate moves are rejected.
- Pinch zoom and drag pan, plus zoom buttons and view reset.
- Three distinct side colors; optional side extensions.
- Optional altitudes with unbounded perpendicular projection, vertex angle bisectors with distinct colors, incenter-to-side perpendicular radii, centers G/I/O/H, internal-angle arcs, external-angle arcs, and side labels.
- Comparison triangle drawn as a dashed overlay with side, area and perimeter differences.
- Measurements for side lengths, angles, perimeter, area, centroid, incenter, circumcenter and orthocenter.
- Save/load/delete triangles on-device; current triangle and comparison triangle restore after relaunch.
- JSON clipboard export/import.
- Arabic and English interface text, with RTL/LTR layout switching.
- Arabic-Indic/Persian digit and decimal-separator parsing; locale-stable numeric formatting.

## Geometry corrections

- Enforced the side convention `a=BC, b=CA, c=AB` in side-based coordinate construction.
- Corrected the `isDegenerate` property type and made its area test scale-relative.
- Normalized side lengths before cosine-law coordinate construction to reduce overflow/underflow.
- Made angle, centroid, incenter, circumcenter and orthocenter calculations more stable for very small triangles and for coordinates far from the origin.
- Corrected circumcenter determinant threshold to be relative to triangle scale.
- Removed segment clamping from altitude projection; the foot may lie outside the side segment in an obtuse triangle.
- Corrected and verified angle-bisector division points.
- Added finite-number and reference-side validation.

## Automated verification

- 13 geometry regression tests are present, covering side convention, triangle inequality, invalid/non-finite values, angle construction, rescaling, altitude projection, centers, angle-bisector ratios, tiny triangles and large coordinate offsets.
- GitHub Actions workflow: `.github/workflows/triangle-lab-android-build.yml`.
- Latest completed run before this log update: run 39, commit `f590a785cf4775e771815ee26d00973e3d3b98e5`.
- In that run, `testDebugUnitTest` passed, `assembleDebug` passed, and the APK artifact uploaded successfully.
- Artifact name: `triangle-lab-debug-apk` (GitHub Actions artifact; debug-signed APK).
- Build artifact is not a substitute for physical-device interaction testing. No claim is made that the app has been exercised on the user's phone.

## Remaining verification boundary

- Automated tests and Android debug assembly have passed.
- Physical-device verification of touch gestures, layout on the target screen, clipboard behavior and persistence across an actual process restart remains unperformed. The user has asked not to install interim builds, so no test APK installation has been requested.
- A release-signed APK would require a stable signing key; the current CI artifact is debug-signed.
