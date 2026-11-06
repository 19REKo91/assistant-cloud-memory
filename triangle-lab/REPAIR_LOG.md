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
