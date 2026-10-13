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
