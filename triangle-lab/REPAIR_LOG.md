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

- 15 geometry regression tests are present, covering side convention, triangle inequality, invalid/non-finite values, angle construction, rescaling, altitude projection, centers, angle-bisector ratios, tiny triangles and large coordinate offsets.
- GitHub Actions workflow: `.github/workflows/triangle-lab-android-build.yml`.
- Latest completed run before this log update: run 39, commit `f590a785cf4775e771815ee26d00973e3d3b98e5`.
- In that run, `testDebugUnitTest` passed, `assembleDebug` passed, and the APK artifact uploaded successfully.
- Artifact name: `triangle-lab-debug-apk` (GitHub Actions artifact; debug-signed APK).
- Build artifact is not a substitute for physical-device interaction testing. No claim is made that the app has been exercised on the user's phone.

## Remaining verification boundary

- Automated tests and Android debug assembly have passed.
- Physical-device verification of touch gestures, layout on the target screen, clipboard behavior and persistence across an actual process restart remains unperformed. The user has asked not to install interim builds, so no test APK installation has been requested.
- A release-signed APK would require a stable signing key; the current CI artifact is debug-signed.

## Complete JSON export enhancement

- The JSON clipboard action now exports a structured snapshot rather than only the six vertex coordinates.
- Export schema: `triangle-lab.geometry-export.v1`.
- Included: vertices, side lengths with the established side convention, internal and external angles, angle sum, perimeter, area, centers G/I/O/H, side/angle classification, comparison-triangle measurements and differences, and active drawing options.
- Length units are explicitly marked as unspecified; the export does not invent a unit.
- The Import action accepts both the previous coordinate-only JSON and the new complete export format.
- Changes are isolated on branch `feature/triangle-lab-complete-json-export`; the stable `main` branch has not been changed.
- Build and unit-test verification is pending for this enhancement.


## Centroid subdivision and six G-sectors

- Added geometric construction of the three internal triangles ABG, ACG and BCG using the actual centroid G.
- Each internal triangle exports its labeled vertices, three side lengths, three internal angles, angle sum, area and perimeter.
- Added the six consecutive sectors formed by the rays G→A, G→B, G→C and G→the three opposite-side midpoints. Each sector exports its start ray, end ray and angle; the total is checked against 360°.
- Added a separate drawing toggle for the six arcs, degree labels, median rays and opposite-side midpoint labels.
- Added regression tests for the one-third area property, 180° angle sums, six positive sectors and 360° total.
- Export schema advanced to `triangle-lab.geometry-export.v2`; previous coordinate-only and v1 imports remain supported because the import reads the vertex object.
- Automated verification for this addition is pending; no physical-device test is claimed.
