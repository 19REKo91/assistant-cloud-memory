# TriangleApp — testing workspace

This folder is reserved for the Android Kotlin + Jetpack Compose TriangleApp project.

## Current contents
- `tests/current/TriangleSolverBaselineTest.kt`: baseline tests for the previously shared
  TriangleSolver API.
- `tests/current/TriangleSolverKnownDefectsTest.kt`: characterization tests that reproduce
  known defects in the current solver. A passing test in this group means the defect is
  reproduced, not that the product behavior is acceptable.
- `tests/future/FUTURE_ACCEPTANCE_TESTS.md`: acceptance criteria for the agreed redesigned
  engine and data model.

## Important source completeness note
The source shared in the conversation was not a complete buildable project snapshot:
the supplied TriangleScreen.kt content ended inside a drawing helper. The complete original
screen source and a verified Gradle wrapper/build setup are not present here yet.
Therefore this commit adds only the test/specification scaffold. It does not claim that the
full Android app has been imported, built, or tested.

## Test dependency
When the complete Android project is assembled, add this dependency to app/build.gradle.kts
if JUnit 4 is not already present:

```kotlin
testImplementation("junit:junit:4.13.2")
```

Run from the project root:

```bash
./gradlew test
```

Do not interpret the known-defect characterization group as a passing product test suite.
After the engine is corrected, replace those tests with assertions that invalid/non-finite
inputs are rejected and all valid outputs remain finite and geometrically consistent.

## Current release policy
No experimental APK is to be installed. The target remains one final release after the
available automated and device-compatibility checks have been completed. Absolute 100%
bug-freedom cannot be proven; test results and untested areas must be reported honestly.
