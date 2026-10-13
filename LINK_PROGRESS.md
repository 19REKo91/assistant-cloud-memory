# LINK Android — Progress Memo

Last updated: 2026-10-13

## Current goal
Fix Android installation error “App not installed because package conflicts with an existing package” without asking the user to uninstall the currently installed LINK app.

## Latest build
- Repository: `19REKo91/assistant-cloud-memory`
- Branch: `anniversary-ble-proximity-prototype`
- Workflow run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38345289079
- Commit: `6b4f0765bbabe987fdac2401c02b944d25b033e9`
- APK artifact: `link-debug-apk`
- Artifact ID: `11788628000`
- Download: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38345289079/artifacts/11788628000
- Artifact ZIP SHA-256: `2559793f26ea82e4507932d559786de183356eb75599eac6c7188258d85769f2`
- Build and unit tests succeeded; APK upload succeeded.
- Crucial: step “Restore LINK debug signing key” succeeded; “Create LINK debug signing key if cache misses” was skipped, meaning the workflow restored an existing cached key. This is encouraging for signature continuity, but do not claim the installed app's signature matches unless independently verified.

## Previous failed install candidate — do not recommend again
- Experiment build run: `38341447623`
- Commit: `5af3e786ef50b5da4f72b915c342ddd97628be2b`
- SHA-256: `c64073be091ce66df5a01ce42939c6449f0e50a0f1272e3a14f1443db848c431`
- User reported package conflict when trying to install it. Do not ask user to uninstall existing app.

## Next steps
1. Give user only the GitHub artifact download link, not an APK uploaded into the chat.
2. User installs this new artifact and reports whether the package conflict is gone.
3. If conflict persists, verify package ID/applicationId and signing certificate fingerprint against the currently installed LINK build before changing more code.
4. Preserve `main`; continue on the LINK prototype branch unless a change is explicitly needed.
5. Artifact expires 2026-10-20; if it expires, rerun the workflow and provide the new artifact link.


## 2026-10-13 — BLE runtime test result
- User confirms the new APK was installed/updated and the app reports “الاقتران محفوظ”.
- User then tested the app again; the screen is unchanged from before. No live partner match or RSSI value appeared.
- Therefore pairing persistence is confirmed only; successful discovery/matching between the two phones is NOT confirmed. The previous build did not resolve the actual BLE runtime problem.
- Do not ask the user to repeat installation/pairing steps. Do not claim the issue is fixed.
- Next engineering task: inspect the source and workflow on `anniversary-ble-proximity-prototype`, trace BLE advertising/scanning callbacks and partner-ID filtering, and add visible diagnostics for scan results, advertised service/manufacturer data, permissions, and match rejection reasons. Build and test before asking for another install.
- Keep `main` untouched. Preserve the existing installed app; never suggest uninstalling it as a first-line workaround.


## 2026-10-13 — BLE diagnostics
- Added runtime diagnostic counters and recent ScanResult details to MainActivity.kt on the prototype branch only.
- The diagnostic panel now wraps content; existing scan matching and radio stop/start behavior were not intentionally changed.
- No APK was built. Next step is to build the diagnostic version, then test both phones for 30 seconds with radioStarts=1 on each and capture both diagnostic panels.

## 2026-10-13 — Diagnostic APK build completed (latest status)
- Built from branch: `anniversary-ble-proximity-prototype`.
- Commit built: `4a7a385642cba8c16e6b8320928463292d2d95f6` (`Fix diagnostic line breaks in BLE panel`).
- GitHub Actions workflow: `Build Two Hearts Android`, run #20.
- Workflow run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38351650832
- Build job: `115145177839`; conclusion: `success`.
- Unit tests and `assembleDebug`: succeeded.
- APK artifact upload: succeeded.
- Artifact name: `link-debug-apk`; artifact ID: `11791620221`.
- Artifact download: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38351650832/artifacts/11791620221
- Artifact ZIP SHA-256: `d0d6523391d90a79e26155c2dff321aa73c4759981501fd7a750f48301ab5bdd`.
- The workflow restored the existing cached LINK debug signing key; key generation and cache save were skipped.
- This supersedes the earlier note above saying no APK had been built: the diagnostic APK is now built and available. Build success does NOT prove that BLE partner discovery/RSSI works on the two phones.
- User was given the verified artifact link. Next: once the user tests this build, diagnose using the new on-screen scan events, UUIDs, counters, RSSI and error fields. Do not ask them to repeat old pairing/install steps unnecessarily.
- Keep `main` untouched. The APK artifact expires on 2026-10-20.

## 2026-10-13 — First successful proximity interaction
- User confirms the app changed to pink and played a beep automatically when the two phones approached; no manual button press was involved.
- User identified the cause of the earlier “no scan results” state: Location was turned off on both phones. After enabling Location on both devices, the proximity interaction worked.
- This is strong evidence of a successful end-to-end proximity interaction in the current two-phone test. It does not yet prove repeatability or establish that every Android device requires Location enabled.
- Next test when convenient: move the phones apart until the interaction clears, then bring them together again and confirm the pink/beep interaction repeats. If available, capture the diagnostic panel after the successful interaction (raw scan count, partner matches, last RSSI) to corroborate the BLE path.
- Do not change the matching logic or request another APK installation unless a repeatable issue is observed. Keep `main` untouched.

## 2026-10-13 — Repeatable proximity / separation behavior confirmed by user
- User reports the pink + beep interaction repeats, and the interaction clears when the phones are separated by approximately one metre.
- Combined with the prior report that enabling Location on both phones allowed discovery, this confirms repeatable user-observed proximity behavior on the current test devices.
- Treat “about one metre” as an approximate observed threshold, not a calibrated distance measurement; BLE RSSI depends on device orientation, obstructions, and surroundings.
- No new APK or code changes requested at this point. Preserve the working build and keep `main` untouched.
- Optional future validation: repeat in a few orientations/positions and, if easy, inspect raw scan/match/RSSI counters after a successful cycle. Do not disrupt the working installation for diagnostics.

## 2026-10-13 — Repeatable proximity and separation confirmed
- User reports the pink/beep proximity interaction repeats when the phones approach again.
- User estimates the separation distance at which the interaction clears/ends is about 1 metre.
- This confirms repeatability in the current two-phone setup and gives an approximate observed range; it is not a calibrated BLE distance measurement and may vary by phone, orientation, and surroundings.
- Current status: functional prototype success for approach-triggered interaction and repeat cycle. Keep the APK/source unchanged for now; no reinstall or pairing reset needed.
- Optional later validation: test a few cycles at the same positions and note whether separation consistently clears near 1 m. Capture diagnostic counters/RSSI if available, but do not interrupt the successful test just to obtain them.
- Keep `main` untouched.

## 2026-10-13 — Background operation limitation reported
- User reports LINK only works while the app is visible on-screen on BOTH phones; it does not continue working in the background.
- Confirmed source-level cause: `MainActivity.onPause()` calls `stopRadio()` whenever `active` is true, so moving the app out of the foreground intentionally stops BLE scanning/advertising. The current BLE engine is owned by the Activity rather than a background service.
- Next task: refactor BLE scanning/advertising and proximity timing into a lifecycle-independent component owned by an Android foreground service, with a persistent notification and the required foreground-service type/permissions for target SDK 34. Ensure Activity UI observes state and does not stop the radio in `onPause`; explicit user stop should still stop it. Preserve the existing successful foreground proximity behavior.
- Validate both phones with screen off/backgrounded, app visible, and after returning to the app; ensure no duplicate advertising/scanning starts and that the approach/separation cycle remains repeatable.
- Do not build or install a changed APK until the service/lifecycle changes are reviewed and the build succeeds. Keep `main` untouched.


## 2026-10-13 — Asymmetric approach response timing
- User reports that the first phone reacts to the two phones meeting sooner than the second phone.
- Treat this as an observed timing asymmetry, not yet a confirmed bug cause. Do not assume it is solely hardware-related.
- Source inspection: each Activity handles its own BLE scan callbacks and calls `proximity.onRssi(...)` when a matching scan result arrives; a separate `tickTask` evaluates proximity every 250 ms. The transition and beep are therefore driven by each phone's locally received scan timing and local proximity state, so perfectly simultaneous reactions are not guaranteed.
- During the background-service refactor, preserve diagnostics on both devices and compare first matching RSSI/result time, scan-result cadence, transition time, and any filtering/hysteresis in `ProximityEngine`. Inspect `ProximityEngine` before changing thresholds or adding synchronization. Avoid making the app wait for a network/server handshake; proximity should remain local and responsive.
- Validation goal: repeat approach/separation tests with both phones in foreground first, then background/screen-off, and distinguish detection-time asymmetry from UI/audio presentation delay. No threshold or matching changes are approved based only on this report.
- Keep `main` untouched; no new APK until the background-service implementation and timing behavior are reviewed and the build succeeds.
