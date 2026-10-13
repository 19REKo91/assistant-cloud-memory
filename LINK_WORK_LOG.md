# LINK — Work Log / Session Handoff

Last updated: 2026-10-13

## Purpose
Persistent handoff notes for future ChatGPT sessions. Update this file after each LINK work session with completed work, unfinished work, blockers, and exact next steps. Do not claim a task is complete unless verified.

## Current confirmed status
- User reports that the latest APK referred to as APK 4 was accepted by Android as an update to the older installed version.
- Treat APK 4's package identity, signing/build configuration, and branch/build path as the preferred reference for the next build, after verifying the actual repo configuration.
- User explicitly permits uninstalling the older app and installing a clean new APK if that is technically necessary. Avoid unnecessary uninstalling; warn about possible local data loss before any destructive step.
- The user has now explicitly authorized implementation. Work is proceeding on a separate experiment branch; no changes are being made to `main`.

## Agreed product behavior / design
- Device A: original dark/smoky scene. On approach/proximity, transition away from the original scene into its effect. When devices move apart, smoothly return toward the original dark scene, increasing darkness and restoring smoke.
- Device B: original girl/nature/sunshine scene; no smoke. When devices move apart, smoothly return to its original bright scene.
- Approach again should restart/reverse the transition in sync with the shared proximity/connection state.
- Remove the beep sound entirely; do not replace it with another annoying notification.
- Make BLE behavior robust against brief RSSI fluctuations: use a short separation confirmation/grace period before treating devices as truly apart. If proximity/connection returns during the transition, cancel or reverse the return animation.
- RSSI-driven progressive visual change is a design option to assess during implementation, not yet implemented or verified.

## Not yet verified / unfinished
- Inspect the repository and identify the exact APK 4 source branch, commit, workflow run, artifact, version code/name, application ID, and signing configuration.
- Confirm whether APK 4's successful update behavior came from matching signing identity, package identity, versioning, or another factor.
- Diagnose and test BLE partner discovery, RSSI updates, proximity/separation transitions, and transient signal loss on two real phones.
- Implement the agreed visual transitions and remove beep sound only after the user authorizes implementation.
- Run tests/build; verify the resulting APK can update the currently installed LINK build (or document if a clean install is required).
- Keep main untouched unless the user explicitly authorizes a change to it; use a suitable experiment branch.

## Next steps when user authorizes implementation
1. Inspect current repo branches, recent commits, APK 4 workflow run/artifact, and relevant Android package/signing/version settings.
2. Record exact verified APK 4 provenance before editing.
3. Create/use an experiment branch from the correct base.
4. Diagnose current BLE lifecycle and RSSI handling before changing code.
5. Implement robust proximity state handling and reversible smooth scene transitions; remove beep.
6. Run available tests and APK build, then provide the artifact and honest test status.
7. Update this work log with commit SHA, branch, workflow run, APK link/checksum, verified behavior, failures, and remaining work.

## Work session — 2026-10-13: application-first iteration (verified build)
- Work branch: `link-ble-recovery-2026-10-13`; `main` and the earlier source commit for APK 4 were not rewritten.
- Source commit: `05d9d67c45c6de2d81a90e45049af8f64480ec3e` — [view commit](https://github.com/19REKo91/assistant-cloud-memory/commit/05d9d67c45c6de2d81a90e45049af8f64480ec3e).
- Implemented: removed all proximity transition tone generation; added a bounded scan retry after 8 seconds without a partner match (first filtered by the partner Service UUID, then one unfiltered retry after another 8 seconds); added mode/attempt counts to diagnostics.
- Version set to `versionCode=4`, `versionName=0.4.0`; `applicationId=com.raeeq.link` remains unchanged.
- Added a unit test covering a new strong RSSI sample resetting the 10-second separation timer.
- GitHub Actions run [#38362715497](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38362715497) completed successfully. The `Run unit tests and assemble APK` step and `Upload debug APK` step succeeded.
- Artifact: `link-debug-apk`, artifact ID `11796000576`, containing `app-debug.apk` (6,190,282 bytes). APK SHA-256: `5eeea40b3563fdb1992e76b73de7b44b66d1573aad03819399901291dd9d57b2`.
- **Signing caveat:** the run log confirms `Cache not found for input keys: link-debug-signing-key-v1`; this branch generated and cached a new debug signing key. Do not assume this APK can update the existing installation signed by the APK 4 key. A clean install may be required; uninstalling clears local pairing preferences.
- **Still not verified:** whether partner discovery/RSSI works on the actual two phones; whether scan recovery cures the zero-results symptom; install behavior on both devices; final photos/scenes and smooth visual transitions. The APK built, but real-device BLE success is not claimed.

## Next steps
1. If using this new-key APK, install it cleanly on both phones only when ready, then repeat QR pairing because uninstalling clears locally saved pairing data.
2. Activate LINK on both phones, wait through the scan retry sequence, and inspect the diagnostics: advertising status, scan status/mode, recovery attempts, raw results, partner matches, and RSSI.
3. If partner matches/RSSI remain at zero after both retries, record the diagnostics and investigate the Android BLE advertising/scanning path before adding visual assets.
4. Once the connection/proximity layer is proven on-device, implement the agreed per-phone scenes and reversible smooth transitions, then update this log again.
5. Keep this log updated at the end of every LINK work session; do not report device behavior as confirmed until the user tests it.
 
## Session rule
At the end of every LINK session, update this file in GitHub. If GitHub access/write fails, clearly tell the user and provide the exact note content rather than claiming it was saved.