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

## Work session — 2026-10-13: application-first iteration (pending build)
- Branch: `link-ble-recovery-2026-10-13`, branched from the APK 4 experiment line. The known APK 4 reference branch is preserved; `main` is untouched.
- Changes committed in this iteration: remove proximity transition tones entirely; add bounded BLE scan recovery (retry once with partner Service UUID filter after 8 seconds without a partner match, then retry once with unfiltered scanning after another 8 seconds); show recovery mode and attempt count in diagnostics.
- Version: `versionCode=4`, `versionName=0.4.0`; `applicationId=com.raeeq.link` and existing `linkDebug` signing configuration/cache key are unchanged.
- Added a ProximityEngine test for a strong reading cancelling an impending departure by resetting the 10-second no-strong-sample timer.
- **Not yet verified:** GitHub Actions build, tests, APK artifact, update-install compatibility, and actual two-phone BLE/RSSI behavior. Final visual assets/scenes remain for the later image stage.
- Update this pending entry with the actual run/artifact results after Actions finishes.

## Session rule
At the end of every LINK session, update this file in GitHub. If GitHub access/write fails, clearly tell the user and provide the exact note content rather than claiming it was saved.