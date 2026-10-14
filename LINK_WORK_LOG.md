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


## 2026-10-14 — LINK connection-button build result
- GitHub Actions run #28 completed successfully: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38425625074
- Build/test step succeeded and APK upload succeeded.
- Artifact `link-debug-apk`, ID `11828955600`, not expired at verification time. Download: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38425625074/artifacts/11828955600
- This confirms compilation/build and artifact upload only. GATT button behavior, cross-phone connection, and screen-off response are not yet device-verified. Keep existing installed LINK 0.6.0 as baseline until both phones are updated and tested.


## 2026-10-14 — first user device test of connection button
- User reports the connection test succeeded and displayed the confirmation text: «استلمنا».
- Record this as a successful first observed receipt/confirmation, based on the user's report; do not yet generalize to screen-off reliability or both-direction operation.
- Remaining validation: repeat the test with the receiving phone screen off, then initiate the test from the other phone. Preserve installed fallback until both checks are complete.


## 2026-10-14 — confirmed screen-off receiving test
- User clarified that the successful «استلمنا» result occurred with the receiving phone's screen turned off.
- Treat as a successful user-observed test of request/response while the receiving phone screen was off.
- Still unverified: reverse-direction test, both phones screen-off simultaneously, long-duration background reliability, and behavior under Android battery restrictions.


## 2026-10-14 — bidirectional connection tests passed
- User confirms connection test succeeded in both directions between the two LINK phones.
- User also confirms the receiving phone's screen was off during the relevant test; the app displayed a receipt confirmation.
- Mark bidirectional request/response as passed in the user's tested conditions. Do not infer simultaneous both-screens-off reliability or long-duration background reliability; those remain untested.


## 2026-10-14 — short-message exchange build completed
- Added UI for composing and sending a short message to the paired phone, with a received-message display.
- Reused the paired BLE GATT connection and existing partner UUID verification before sending; remote GATT characteristic now accepts bounded writes (up to 180 bytes) and the receiver displays the message.
- GitHub Actions run #29 succeeded: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38483876774
- Build/test/assemble and APK upload succeeded. Artifact `link-debug-apk`, ID `11857528818`, is available until 2026-10-20T23:25:03Z.
- Device-level message delivery is NOT yet verified. Install this build on both phones only when ready to test; keep the current installed build until update installation is confirmed.



## 2026-10-14 — short-message exchange verified on both phones
- User confirms that sending and receiving short messages succeeded in both directions between the two LINK phones.
- Mark bidirectional short-message delivery as **user-tested and passed** for the tested setup; this is beyond the earlier CI-only build verification.
- Code commit for the feature: `3e46206599c3b9cd06143a70cac238e8d4161006`; workflow run #29 succeeded: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38483876774
- APK artifact: `link-debug-apk`, ID `11857528818`; artifact link: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38483876774/artifacts/11857528818
- Artifact SHA-256: `d38b63abaacf5066e5a8d00e3e65613a7e3296d1f8041a1ac5e534128d0f3bd4`; expires 2026-10-20T23:25:03Z.
- Not yet verified: recovery after connection loss/reconnection, repeated/long messages, simultaneous both-screens-off behavior, and sustained reliability under battery restrictions.
- Keep `main` untouched. Next engineering step should be to harden and test connection lifecycle/reconnection and message-delivery status without regressing the working two-way exchange.


## 2026-10-14 — Incoming message persistence fix
- User test found that a message sent while the receiving phone screen was off was not shown after reopening LINK.
- Source review found that the receiver only broadcast to the Activity, which unregisters its receiver when stopped; the display event could be missed.
- Commit `d0fe4df9ccdedb8dd62deecbaa74c8034dd4c319` now saves the latest incoming message before acknowledging the BLE write and restores it when the Activity opens.
- Workflow #30 is building this commit: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38486401241
- Build and real-device retest are pending. Keep `main` untouched; do not treat the fix as verified until CI and phone tests pass.


## 2026-10-14 — Automatic BLE recovery after Bluetooth toggle

- User reported that turning Bluetooth off on the second phone and turning it back on later caused LINK pairing/re-discovery to take too long.
- Source review found the proximity service had no Bluetooth adapter state receiver; a radio stop/failure could leave scanning/advertising stopped, and the service uses `START_NOT_STICKY`, so recovery was not explicitly coordinated.
- Commit `91b8b0ada5c48c1aa6edcd3959edd873aed6c896` on `anniversary-ble-proximity-prototype` adds a system Bluetooth-state receiver. When Bluetooth turns off, LINK pauses BLE radio resources without discarding the active session; when Bluetooth turns on, it restarts advertising/scanning using the saved local/partner UUIDs. Starting LINK while Bluetooth is temporarily off now waits for Bluetooth to return instead of immediately terminating the session.
- Build and two-device retest are pending. Validate by toggling Bluetooth off/on on one phone and measuring time until the partner is rediscovered; do not mark verified until build and device test succeed. `main` remains untouched.


## 2026-10-14 — One retry for transient GATT message-write error 133

- User tested the short Arabic message “جي بي تي بطل”; LINK displayed “فشل إرسال الرسالة (رمز 133)”. The diagnostics showed the GATT client connected, then the write callback failed with status 133, followed by disconnection. This locates the observed failure in the GATT write stage; status 133 is a generic Android GATT error and does not identify the underlying radio/stack cause by itself.
- Commit `41314942ad4c6076d244beae4451b67871293aa9` on `anniversary-ble-proximity-prototype` adds one bounded retry for a message write that returns status 133: close the failed GATT client, wait one second, then re-run the UUID-confirmed connection and resend the same message once. It does not retry indefinitely. Other error statuses still report failure.
- Build and two-phone retest pending. Do not treat this as a proven root-cause fix until the APK builds and the same message is tested on both phones. `main` remains untouched.


## 2026-10-14 — Message not delivered while receiving app was closed

- User-tested scenario: phone A kept LINK running and showed `NEAR`; LINK was closed on phone B. Phone A then attempted to send a new message and displayed «أرسلت الرسالة إلى الهاتف المرتبط». After the user reopened LINK on phone B, the new message was not present.
- This proves the sender-side success UI is not sufficient evidence of user-visible delivery when the receiver app UI is closed. Earlier receiver-side logs did show a different message «مساء» saved (8 bytes) while the receiver was active; that does not prove the later message arrived while its app was closed.
- Root cause is not yet confirmed. Investigate GATT server/service lifecycle and ensure the sender only reports delivery after a trustworthy receiver acknowledgement; queued/offline delivery needs explicit persistence/queue semantics if desired.
- Status: unresolved; do not mark screen-off/app-closed delivery as passed. The bounded retry for status 133 does not address this result by itself. `main` remains untouched.


## 2026-10-14 — Explicit receiver acknowledgement for message delivery

- Follow-up to the confirmed user test where the sender displayed success while the receiver app was closed, but the new message was absent after reopening.
- Commit f4f67be86c64402ef22554fcd5a7ca7dfef9916d adds a read-only GATT acknowledgement characteristic. Each outgoing message carries a short message ID; the receiver persists both the message and ID before returning GATT write success. The sender then reads the acknowledgement characteristic and reports delivery success only when the returned ID matches the pending message.
- Commit 255071c8cf0d0789e3dae91c9455d727b22dde32 limits message content to 160 UTF-8 bytes so the message ID and delimiter remain within the 180-byte GATT payload cap.
- This change is intended to prevent a plain GATT write callback from being presented as confirmed message delivery. It is not yet validated: build and two-phone tests are pending, including active receiver, receiver app closed, and receiver screen off. If the receiver service is stopped, sender should report that delivery was not confirmed rather than claim success.
- main remains untouched. Do not install or treat this protocol change as complete until the CI build succeeds.


## 2026-10-14 — Priority update: BLE stability plus media space

- User explicitly prioritizes stabilizing LINK's proximity/peer rediscovery and BLE connection behavior over message-delivery enhancements.
- Keep the planned song and image in the LINK product scope: reserve a dedicated, intentional UI area for them rather than letting diagnostics and connection controls consume the entire screen. Do not guess/commit media assets or spend any third-party generation credits without the user's established approval.
- Order of work: (1) review/build the current branch and validate proximity transitions/rediscovery and GATT reliability; (2) shape the screen layout to accommodate song + image without obscuring the proximity state or core controls; (3) implement media playback/display after stability and layout are verified.
- Current acknowledgement-protocol commits are experimental and CI validation is pending; do not ask user to install them until build status and code behavior are checked. main remains untouched.

## 2026-10-14 — User retest: delayed background pairing, message triggers visible pairing

- User reports the second phone was left paired; the first phone was paired but LINK was in the background. After approximately 650 seconds, pairing had not occurred/updated as expected, and the image changed (the exact UI element/state associated with the image change needs clarification during a later test).
- The user then opened/used LINK on phone 1 and sent a message. Phone 2 received the message, and the pairing state appeared/updated at the same time.
- Working interpretation, not yet a confirmed root cause: the background proximity/session path did not visibly complete or refresh pairing during the ~650-second interval, while initiating a message caused a GATT interaction that coincided with the pairing UI update. Do not infer that the message itself repaired proximity discovery; collect logs and repeat the scenario before deciding.
- Priority remains BLE stability and background/foreground recovery, not new features or message-delivery enhancements. Next test should capture both phones' LINK state/logs before sending any message, after the long background interval, and immediately after foregrounding LINK; compare whether NEAR/APART, peer UUID, GATT connection, and displayed image change independently.
- main remains untouched.

## 2026-10-14 — BLE background-service recovery hardening

- User's long-background test: after roughly 650 seconds, the expected proximity/pairing update had not happened; opening LINK/initiating a message coincided with the peer receiving it and the state updating. Root cause remains unconfirmed, so this is treated as a recovery-lifecycle issue to validate, not proof that messages cause pairing.
- Source inspection found that transient BLE scan failures called the fatal `fail()` path, stopping the foreground service; the service also returned `START_NOT_STICKY`, and `onDestroy()` cleared the saved active flag, preventing reliable recreation after service destruction.
- Commit `035571bffe0242dfbe51e2e82fdcef0e58c13752` changes the experiment branch to:
  - persist both service UUIDs with the active session and recover them from the previously saved pairing fields when necessary;
  - return `START_STICKY` and restore an active saved session when Android recreates the service with a null intent;
  - retry recoverable scan/advertise/start failures with a backoff from 1 second to at most 30 seconds, while keeping unsupported BLE hardware/data configuration errors fatal;
  - preserve saved session state in `onDestroy()`; explicit stop and fatal failure clear it.
- CI build and unit tests are pending. No device behavior is claimed verified. After CI succeeds, next device test should leave LINK in the background for 10–11 minutes without sending a message, then check whether NEAR/APART and the image/state update by themselves. Also test explicit Stop to ensure it does not restart.
- `main` remains untouched.

### Build verification result for BLE background-service recovery

- GitHub Actions run #34 completed successfully: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38599259240
- Verified commit: `035571bffe0242dfbe51e2e82fdcef0e58c13752`
- `testDebugUnitTest` and `assembleDebug` both succeeded; debug APK artifact uploaded.
- APK artifact: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38599259240/artifacts/11911064407
- Artifact SHA-256: `dcf0ca6069df0de78e7a9b33df47919c5b44b5ff4b9493ea640b87dff91b2023`; expires 2026-10-21T16:36:50Z.
- This is build verification only, not proof the 650-second background behavior is fixed. Next device test: install this APK on both phones (the workflow restored the existing LINK debug signing key), start LINK on both, switch phone 1 to another app while keeping LINK active, wait 10–11 minutes without sending a message or reopening LINK, then check whether the expected proximity/image transition happened. Afterward test turning Bluetooth off/on. Stop/clear-session behavior also needs a quick check.



## 2026-10-14 — False APART transition identified and hysteresis fix building

- User confirmed both phones were physically close when LINK displayed `APART`; diagnostics showed 811 partner matches, raw scan count 2297, and last RSSI `-61 dBm`.
- Source inspection confirmed a concrete proximity-engine flaw: `NEAR` required RSSI >= -56 dBm, and the same -56 dBm threshold refreshed the departure timer. Any continuous partner signal weaker than -56 dBm (for example -61 dBm) was treated like no usable in-range signal, so the engine could switch to `APART` after 10 seconds even while scans kept matching the partner.
- Fix on `anniversary-ble-proximity-prototype`: commit `7ea2077e837132ddd7271e4db23c4d610dd08557` adds RSSI hysteresis. Strong samples (>= -56 dBm) still establish `NEAR` after three samples; an established `NEAR` state is maintained by samples >= -70 dBm; `APART` requires 10 seconds without any sample meeting that more tolerant -70 dBm threshold. Very weak samples such as -80 dBm still do not reset the departure timer.
- Added unit tests for the reported -61 dBm case and for very weak readings in commit `aad9d1d00fa24577b2e866357f162ddd73fe4f15`.
- GitHub Actions run #37 is queued for the latest commit: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38635174855. Build/tests and APK artifact are not yet verified. Do not ask the user to install until the run succeeds and the artifact is confirmed.
- The -70 dBm far threshold is a deliberate hysteresis starting point, not a claim that RSSI precisely measures physical distance. Validate on both phones after a successful build; adjust only from observed diagnostics if needed.
- `main` remains untouched. Next: verify run #37, then test both phones side by side and at separation; confirm that around -61 dBm no longer forces `APART`, while sustained very weak/no partner signal still produces `APART` after the delay.


### Build verification update — 2026-10-14

- GitHub Actions run #37 completed successfully for source/test commit `aad9d1d00fa24577b2e866357f162ddd73fe4f15`: unit tests and APK assembly passed.
- Run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38635174855
- APK artifact `link-debug-apk`, artifact ID `11928550103`, verified present and not expired at the time of this check; expires `2026-10-21T20:51:05Z`.
- Artifact download page: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38635174855/artifacts/11928550103
- This confirms CI tests/build only; device behavior still needs testing on both phones. Install on both phones, keep them side by side, and confirm RSSI values around `-61 dBm` no longer cause a false `APART`. Then separate them enough for sustained weak/no signal and confirm `APART` still occurs.


## 2026-10-15 — BLE source review and hysteresis APK verification

- User reaffirmed the current goal: reliable NEAR/APART transitions, visible synchronization while LINK is open on both phones, and continued operation when LINK is in the background. Messaging remains out of scope for this phase.
- Reviewed the actual source on `anniversary-ble-proximity-prototype`. `MainActivity.kt` also contains the top-level `LinkProximityService`; it is not a separate `LinkProximityService.kt` file. `AndroidManifest.xml` declares the service as a connected-device foreground service.
- `ProximityEngine.kt` confirms the existing hysteresis policy: three RSSI samples at or above -56 dBm within a 2,500 ms window establish NEAR; once NEAR, samples at or above -70 dBm refresh the in-range timer; APART is confirmed after 10 seconds without an in-range sample. The service ticker evaluates timeouts every 250 ms. Unit tests cover moderate -61 dBm readings preserving NEAR and very weak -80 dBm readings not resetting the departure timer.
- Source review confirms BLE scan/advertising live in the foreground service; Activity `onPause()` does not stop it. The service returns `START_STICKY`, saves the pairing UUIDs, attempts to restore an active session after service recreation, and retries recoverable scan/advertising failures with bounded backoff. These code paths are not proof that TECNO/Android battery restrictions will always deliver screen-off scan results.
- Each phone still calculates its proximity state independently from its own RSSI samples. There is no shared state synchronization protocol between phones, so the design can provide near-simultaneous behavior but cannot guarantee identical transition timestamps. Since the user reports the on-screen behavior is synchronized, do not redesign this path without new device evidence.
- Verified GitHub Actions run #37 for commit `aad9d1d00fa24577b2e866357f162ddd73fe4f15`: workflow completed successfully; unit tests, `assembleDebug`, and artifact upload succeeded. The existing LINK debug signing key was restored; generating a new key was skipped.
- Artifact: `link-debug-apk`, ID `11928550103`; download page: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38635174855/artifacts/11928550103. Artifact expires `2026-10-21T20:51:05Z`. Package is `com.raeeq.link`, `versionCode=6`, `versionName=0.6.0`.
- No application source code was changed in this session and no new APK was built. The hysteresis build's behavior has **not** yet been independently confirmed on both phones.
- Remaining device validation: install the artifact APK on both phones without uninstalling first; with LINK visible, confirm the phones stay NEAR around -61 dBm and only become APART after sustained weak/missing partner signal; then test app-background operation without sending messages. Treat screen-off behavior as a separate case; previous notes record that it did not reliably pair while one screen was off.
- If Android reports a package/signing conflict, stop and report the exact error rather than uninstalling the working app automatically. Keep `main` untouched.


## 2026-10-15 — تدقيق المساحة وملفات البناء

- المستودع: قيمة GitHub API `size=22987 KB` (حوالي `22.45 MiB` بالتحويل الثنائي). لا تخلط ذلك مع حصة التخزين الكلية للحساب.
- أحدث بناء: run #37 / ID `38635174855`، مصدره commit `aad9d1d00fa24577b2e866357f162ddd73fe4f15` على `anniversary-ble-proximity-prototype`؛ النتيجة نجاح. الرابط: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38635174855
- أحدث 10 عمليات Actions التي فُحصت أظهرت 10 آثار `link-debug-apk` مجموعها `22,959,369 bytes` (حوالي `21.90 MiB`). جميع الآثار التي شملها الفحص كانت غير منتهية الصلاحية وقتها؛ مواعيد الانتهاء الظاهرة بين 2026-10-20 و2026-10-21 UTC.
- ملفات كبيرة ظاهرة على جذر `main`: فيديو العام الجديد `6.75 MiB`؛ ملفات بحثية عن فرضية رائق نحو `2.89–3.18 MiB` للملف؛ وملفات توثيق بحثية أخرى. لم يُستنتج أنها زائدة.
- لا تنظيف ولا حذف ولا تعديل للكود أو بناء APK في هذه الجلسة؛ العمل كان تدقيقًا وتوثيقًا فقط.
- حدود التحقق: لم يُثبت إجمالي استخدام مساحة Actions/Artifacts لكل المستودع أو الحساب، ولم تُفحص كل عمليات البناء؛ الأرقام تخص أحدث 10 تشغيلات وآثارها فقط.
- الحالة: تدقيق أحدث 10 آثار ومستودع مكتمل؛ فحص الحصة الشاملة والتنظيف الاختياري بانتظار التحقق/موافقة المستخدم.
- التالي: عند الحاجة، افحص إجمالي مساحة Actions من صفحة الاستخدام المتاحة، ثم قدّم قائمة تنظيف محددة وآمنة مع الأحجام والتواريخ؛ لا تحذف شيئًا قبل الموافقة.
