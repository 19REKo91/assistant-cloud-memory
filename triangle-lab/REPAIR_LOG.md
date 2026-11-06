# Triangle Lab — Repair log

## Initial GitHub workspace

The project is isolated under `triangle-lab/` in `19REKo91/assistant-cloud-memory`. Existing archive and memory files are untouched.

## Geometry foundation reconstructed

- Corrected the side convention `a=BC, b=CA, c=AB` in coordinate construction.
- Corrected `Triangle.isDegenerate` to Boolean semantics.
- Added finite-number validation for side and angle inputs.
- Removed segment clamping from altitude projection; the foot is on the supporting line, including outside the segment for obtuse triangles.
- Implemented circumcenter and orthocenter using the vector identity `H=A+B+C-2O`.
- Added input guards for invalid reference sides and non-positive/non-finite rescaling.

## Not yet verified

This is not yet a complete Android app. UI/state/persistence sources and Gradle project configuration still need to be restored and integrated. No build or runtime test has been claimed.

## Follow-up work

- Added a minimal Android/Compose application entry point and Gradle project configuration.
- Added unit tests for side convention, invalid inputs, angle-based construction, obtuse-triangle altitude projection, triangle centers, and angle-bisector division.
- Added the active GitHub Actions workflow at the repository root: `.github/workflows/triangle-lab-android-build.yml`. (A workflow file nested under the project directory was removed because GitHub only discovers workflows in the repository-root `.github/workflows` directory.)
- Compiled the geometry source files with the available Kotlin compiler and ran independent geometry smoke checks: **passed**.
- Full Android Gradle build has not yet been confirmed in this environment. The CI workflow is configured to run unit tests and assemble the debug APK when GitHub Actions executes.

## Current limitations

The current Compose screen is an initial functional shell, not the complete agreed interface. Editing modes, automatic side/angle synchronization, the full set of center/bisector/altitude toggles, compare mode, saved-triangle management, import/export, and complete state restoration still need implementation and verification.
