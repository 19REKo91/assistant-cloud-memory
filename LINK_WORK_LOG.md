# LINK — Work Log / Session Handoff

Last updated: 2026-10-13

## Purpose
Persistent handoff notes for future ChatGPT sessions. Update this file after each LINK work session with completed work, unfinished work, blockers, and exact next steps. Do not claim a task is complete unless verified.

## Current confirmed status
- User reports that the latest APK referred to as APK 4 was accepted by Android as an update to the older installed version.
- Treat APK 4's package identity, signing/build configuration, and branch/build path as the preferred reference for the next build, after verifying the actual repo configuration.
- User explicitly permits uninstalling the older app and installing a clean new APK if that is technically necessary. Avoid unnecessary uninstalling; warn about possible local data loss before any destructive step.
- No new implementation has been started as part of this note. Wait for the user's explicit instruction to begin implementation.

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

## Session rule
At the end of every LINK session, update this file in GitHub. If GitHub access/write fails, clearly tell the user and provide the exact note content rather than claiming it was saved.

## 2026-10-13 — BLE timing diagnosis (in progress)
- User requirement clarified: on approach and separation, both phones should react together as immediately as practical, without manual actions.
- Code inspection on `anniversary-ble-proximity-prototype` confirms each phone independently evaluates its own BLE scan RSSI in `MainActivity`/ `ProximityEngine`; this is why exact simultaneity is not guaranteed by the current architecture.
- Existing policy observed in source: enter NEAR after three readings at or above -56 dBm within 2500 ms; switch to APART only 10000 ms after the last strong reading. The departure delay is therefore not immediate by design and may contribute to perceived timing.
- Added diagnostic-only timestamps (no threshold, BLE advertising/scanning, or UI behavior changes) in commit `88964b8f20261eaf755a9d7b11032f25efe03ad4`:
  - first matching BLE result from the partner;
  - first strong partner RSSI (>= -56 dBm);
  - proximity state transition;
  - sound request and scene update;
  - local elapsed time since radio start and phone clock timestamp (phone-clock differences can affect cross-device comparison).
- Workflow run #22: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38364353379
- At this memo update, build workflow status was still `in_progress`; do not share or describe a new APK as ready until unit tests/build/artifact upload are confirmed.
- Next: verify run #22 completes successfully, confirm the workflow restored the existing cached LINK debug signing key, then provide the artifact link. User should install/test on both phones only if the build succeeds; long-press the LINK header to open diagnostics and capture both panels after one approach and one separation cycle.
- Compare the first-match / first-strong / NEAR / APART / scene timestamps on both phones. Their wall clocks may not be perfectly synchronized, so treat the absolute clock comparison as approximate; local +ms values are anchored to each phone's own radio start and should not be compared directly as a shared clock.
- After evidence is collected, decide whether the fix belongs in local RSSI sampling/hysteresis or a BLE peer-state synchronization protocol. Do not promise exact simultaneous behavior; BLE scanning and device clock/audio/UI scheduling vary.
- Keep `main` untouched. Preserve the last working APK and do not change radio thresholds or introduce an internet/server dependency without evidence.


## 2026-10-13 — Timing diagnostics APK built successfully
- Workflow run #22 completed with conclusion `success`: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38364353379
- The combined step `Run unit tests and assemble APK` succeeded; APK artifact upload also succeeded.
- The workflow restored the existing cached LINK debug signing key; generation of a new key was skipped.
- Diagnostic APK artifact: `link-debug-apk`, artifact ID `11796043306`.
- Download: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38364353379/artifacts/11796043306
- Artifact ZIP SHA-256: `d1e4c6c17c63022f347b918d8b8395ee88e3a0868692447d9c76122f4d677292`.
- Artifact created 2026-10-13 07:44:31 UTC and expires 2026-10-20 07:44:30 UTC.
- This APK adds diagnostics only; it does NOT fix or claim simultaneous response. It preserves the existing threshold/delay and BLE matching logic.
- Next practical step: user installs this diagnostic APK on both phones (existing signing key restored, but update acceptance cannot be guaranteed without testing), activates the experience, long-presses the LINK header to reveal diagnostics, then performs one approach/separation cycle. Capture the diagnostic panels on both phones.
- Compare first partner match, first strong RSSI, state transition to NEAR/APART and scene update timestamps. Use phone clock timestamps only approximately if device clocks may differ; local +ms values each start from that phone's own radio start.
- Do not ask the user to redo pairing unless the updated APK actually requires it. Do not change thresholds before collecting both phones' timing evidence. Keep `main` untouched.


## 2026-10-13 — APK rejected: version downgrade identified and corrected
- User confirmed the installer was given `app-debug.apk`, not the ZIP archive.
- Compared the failing diagnostic branch with the previously successful APK 4 branch. APK 4 used `versionCode = 4`, `versionName = "0.4.0"`; the new diagnostic APK incorrectly reverted to `versionCode = 3`, `versionName = "0.3.0"`.
- This is a strong concrete explanation for Android rejecting the install as a downgrade. Package ID remains `com.raeeq.link`, and the workflow is configured to restore the same cached debug keystore; signing identity is not yet independently proven.
- Corrected only the experiment branch `anniversary-ble-proximity-prototype` to `versionCode = 5`, `versionName = "0.5.0"` in commit `8143e4076b76bde7c0a7e4727f6d96da36a2161f`. This should permit updating APK 4 if signing identity matches.
- No new GitHub Actions run appeared after the API-created commit (latest run remains #22). The APK is not yet rebuilt. Trigger the existing workflow manually from GitHub Actions on branch `anniversary-ble-proximity-prototype`, or create a normal push that triggers it. Do not call the APK ready until the run succeeds and the artifact is present.
- Next: verify the new workflow run, send its artifact link, and ask the user to install it over the existing app without uninstalling.


## 2026-10-13 — LINK 0.6.0 background-service build candidate
- Updated experiment branch only: `anniversary-ble-proximity-prototype`; `main` was not changed.
- Commit: `daa4d79971746cd55f8a8cc4de9f8990a0a9fa15` — “Add background BLE service and prepare LINK 0.6.0”.
- Changes: `MainActivity.kt` now delegates BLE scan/advertising and proximity evaluation to a foreground service; the manifest declares `connectedDevice` service type and its foreground-service permissions; app version is `versionCode = 6`, `versionName = "0.6.0"`.
- The existing `ProximityEngine` and partner UUID matching approach were reused; the current -56 dBm threshold and 10-second departure delay were not changed.
- The Activity no longer stops BLE merely because it enters `onPause()`. The service publishes state/diagnostics and supplies an ongoing notification with an explicit Stop action.
- The approach/separation beep calls were removed, consistent with the previously recorded product requirement.
- A static source check confirmed the service declaration, manifest permissions, lifecycle wiring, current threshold usage, and version bump. This is **not** a substitute for compilation, unit tests, or real-phone verification.
- **Build/test status at memo time:** pending; do not install or present this candidate as verified until the GitHub Actions run and artifact upload succeed.
- Previously user-confirmed behavior to preserve: LINK 5 on the two test phones repeatedly reacted to approach, separation at approximately one metre, and approach again while both apps were foregrounded. The approximate distance is not calibrated.
- Next steps: (1) verify GitHub Actions on this exact commit; (2) inspect test/build steps and artifact; (3) only if successful, install 0.6.0 over the existing app without uninstalling; (4) check foreground regression, then background and screen-off on both phones; (5) record all results and any failure here.


## 2026-10-13 — CI failure diagnosed and follow-up candidate queued
- GitHub Actions run #24 for intermediate commit `38c0edbee7e66ade56142b6ec53742d3704749d0` failed during Kotlin compilation, before APK creation: the service ticker incorrectly implemented `Handler.Callback` and the service's event-list name was inconsistent.
- The ticker was simplified to a plain `Runnable` in commit `daa4d79971746cd55f8a8cc4de9f8990a0a9fa15`.
- Fixed the service event-list references and made the persisted active flag reset on service startup/stop failures in commit `03489dfb18c5d7842fa1b7c1ddd23950d931c490`.
- Run #25, which builds intermediate commit `daa4d79`, was still in progress at the last check and includes the event-list defect; do not use it even if it finishes.
- Run #26 was queued for the latest code commit `03489dfb18c5d7842fa1b7c1ddd23950d931c490`; this is the run to inspect for the next decision.
- Current build status remains **unverified**. Do not install an APK until the latest-run tests/build and artifact upload both succeed.


## 2026-10-13 — Stop-action state guard and latest build attempt
- Added a guard in `MainActivity.onStart()` to reload the persisted active flag, preventing the Activity from restarting BLE automatically after the user stops the background service from its notification while the Activity is not visible.
- Commit: `8b2b08fe8d7e9cfd49d3ef68a21f766462fa8f77`.
- GitHub Actions run #26 targets commit `03489dfb18c5d7842fa1b7c1ddd23950d931c490`; it was still running `testDebugUnitTest assembleDebug` at the last status check.
- GitHub Actions run #27 targets the newest stop-action guard commit `8b2b08fe8d7e9cfd49d3ef68a21f766462fa8f77`; it was queued at the last status check. Prefer #27 for final verification because it includes the current source.
- Run #24 failed due the ticker implementation and event-list identifier. Run #25 failed on the event-list mismatch in its older intermediate commit. Those failures are recorded for audit; neither produced an APK artifact.
- **Do not install yet:** the latest source remains unverified until the relevant current-head run passes unit tests, assembles the APK, and uploads `link-debug-apk`. Real-phone background behavior still requires testing after a successful build.


## CI status correction — 2026-10-13
- Run #26 completed successfully for commit `03489dfb18c5d7842fa1b7c1ddd23950d931c490`: the unit-test/build step and artifact upload both succeeded.
- Run #26 artifact `link-debug-apk`: artifact ID `11822396957`; ZIP size 2,287,937 bytes; created 2026-10-13 14:19:32 UTC; expires 2026-10-20 14:19:30 UTC. This artifact predates the Activity stop-action guard commit, so it is retained only as build evidence and is **not the preferred install candidate**.
- Run #27 for the latest commit `8b2b08fe8d7e9cfd49d3ef68a21f766462fa8f77` is still the preferred candidate to verify because it includes the final stop-action guard. Its unit-test/build step was in progress at this check.


## 2026-10-13 — LINK 0.6.0 build and tests verified
- **GitHub Actions run #27 succeeded** on code commit `8b2b08fe8d7e9cfd49d3ef68a21f766462fa8f77`: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38412370531
- The `Run unit tests and assemble APK` step succeeded; artifact upload succeeded.
- The existing cached LINK debug signing key was restored successfully; key generation was skipped. The new APK is configured as `applicationId=com.raeeq.link`, `versionCode=6`, `versionName=0.6.0`; real update acceptance still must be confirmed on the user's phone.
- Artifact: `link-debug-apk`, ID `11823157025`, size 2,287,983 bytes.
- Download: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38412370531/artifacts/11823157025
- Artifact ZIP digest from GitHub API: `sha256:6558a07ca044d11eb2bfdc6732ae7b1f257f680e7143f8679f15aeeaea16392a`.
- Created 2026-10-13 14:21:44 UTC; expires 2026-10-20 14:21:43 UTC.
- **What CI verifies:** Kotlin compilation, unit tests and APK assembly/upload. It does not prove that background/screen-off BLE works on the two real phones.
- **Required device validation:** update over the installed LINK 0.5.0 without uninstalling; test approach/separation/re-approach in foreground; then background the app and turn off both screens, check the ongoing LINK notification, and finally stop using the notification and confirm returning to LINK does not silently restart it.
- The `main` branch remains untouched.


## 2026-10-13 — User-reported real-phone validation of LINK 0.6.0
- User confirms LINK 0.6.0 installed successfully.
- On the two phones, approach responses were synchronized in the user's test.
- On the two phones, separation responses were synchronized in the user's test.
- The Stop button/action worked; after stopping, the user manually restarted LINK and confirmed it worked again.
- Background test passed on both phones: while LINK was running, the user opened another app on each phone and reported that LINK continued working in the background.
- These are user-observed device results, not CI-only claims. No code changes were made in this update.
- Still untested: whether LINK remains active with both phone screens turned off/locked, and behavior after device reboot. Do not claim those scenarios pass yet.
- Next test: on both phones, start LINK and confirm the ongoing service notification is present; lock/turn off the screens and test approach/separation. Then use the notification's Stop action and reopen the app to confirm it does not restart BLE by itself.
- Build reference remains LINK 0.6.0, code commit `8b2b08fe8d7e9cfd49d3ef68a21f766462fa8f77`, Actions run #27: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38412370531
- Keep `main` untouched.


## 2026-10-13 — Screen-off test (one phone)
- User reports that when the screen of one phone was turned off, the other phone continued running; when the screen was turned back on, the two phones synchronized again.
- Record as a **partial/initial pass**, not proof that BLE scanning and proximity transitions continued on the screen-off phone throughout the interval; the observed resynchronization may have happened on wake.
- Still needed: repeat with both screens off, bring the phones together/apart while locked, then wake both and check whether the state had tracked the changes. Note the ongoing service notification if visible.
- No code changes made. Keep main untouched.


## 2026-10-13 — Screen-off pairing failure confirmed
- User clarifies that the phone with its screen off does not pair/respond to the other phone; synchronization resumes when the screen is turned back on.
- Treat screen-off behavior as a confirmed defect in the current LINK 0.6.0 device test, despite successful foreground and app-background tests.
- Source inspection: BLE scanning and advertising run inside `LinkProximityService` as a connected-device foreground service; scan mode is `SCAN_MODE_LOW_LATENCY`, with local partner-UUID matching. Manifest declares `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_CONNECTED_DEVICE`. This structure alone does not guarantee OEM/OS screen-off scanning will continue.
- Likely areas to diagnose before changing thresholds: Android/TECNO battery background restrictions, BLE scan delivery under screen-off, and whether the foreground service/ongoing notification remains active. Do not assume the exact cause without diagnostics.
- Next: while screen is on, long-press LINK title to show diagnostics; note service active state, raw scan count, partner matches, and RSSI. Then lock that phone for a short interval while the other phone remains active and approaches; wake it and inspect whether raw results/matches increased and whether an error is shown. Repeat on the other phone. No code change/build has been made for this defect yet.
- Preserve version 0.6.0 as the current tested baseline; do not alter RSSI thresholds or remove foreground service without evidence. Keep main untouched.


## 2026-10-13 — LINK BLE connection confirmation button (build pending)
- User authorized autonomous implementation of a persistent connection-test button for the finished LINK app.
- Code commit: `1df3532358b3c72da80b75c874806818e95c0ef7` on `anniversary-ble-proximity-prototype`; `main` untouched.
- Added an active-session UI button labelled "اختبار الاتصال بالهاتف الآخر". It asks the foreground service to connect over BLE GATT to the latest scanned partner device, read a dedicated confirmation characteristic, and only report success when the returned device UUID matches the saved partner UUID. A toast reports success/failure.
- The service now opens a GATT server with a read-only confirmation characteristic, and BLE advertising is configured as connectable to permit GATT connections. Existing UUID-based discovery and proximity thresholds remain unchanged.
- GitHub Actions build run #28 started and was still in progress at the time of this note: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38425625074
- **Not yet verified:** compilation/build result, APK artifact, GATT compatibility across the two actual phones, and successful response while the receiving phone screen is off. Do not ask the user to install an APK until the build succeeds and the artifact is confirmed.
- Next: verify Actions run #28; fix any compile errors, then provide the APK only after successful build. Device testing must be done on both phones with the new build, since the button requires the new GATT protocol on both ends. Keep the current installed 0.6.0 baseline intact until a tested update is available.
