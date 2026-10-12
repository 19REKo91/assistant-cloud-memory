# Two Hearts — GitHub Working Memo for ChatGPT

Last updated: 2026-10-12

## Purpose
This is the handoff note for continuing the Two Hearts anniversary Android app work. Read this note before touching the repository so work can resume without asking the user to repeat the setup.

## Repository and safe working area
- Repository: https://github.com/19REKo91/assistant-cloud-memory
- Work only on branch: `anniversary-ble-proximity-prototype`
- Android project: `two-hearts-android/`
- Main activity: `two-hearts-android/app/src/main/java/com/raeeq/link/MainActivity.kt`
- Build workflow: `.github/workflows/build-two-hearts-android.yml`
- Branch page: https://github.com/19REKo91/assistant-cloud-memory/tree/anniversary-ble-proximity-prototype
- Workflow runs: https://github.com/19REKo91/assistant-cloud-memory/actions/workflows/build-two-hearts-android.yml
- Do not change or merge into `main` unless there is a clear, separately approved reason. Keep the prototype isolated on its own branch.

## How ChatGPT should operate GitHub
Use the connected GitHub MCP tools through `functions.exec` (discover exact current tool names/schemas from `ALL_TOOLS`; do not assume old tool IDs or run IDs remain current).
1. Read first: use `mcp__GitHub__fetch_file` with repository `19REKo91/assistant-cloud-memory`, exact path, and ref `anniversary-ble-proximity-prototype`. For workflow/API status, use `mcp__GitHub__fetch` on approved GitHub URLs.
2. Before edits, inspect the relevant source and current branch head. Make the smallest focused change; do not overwrite unrelated work.
3. Write files with `mcp__GitHub__create_file` only for a path that does not exist; use `mcp__GitHub__update_file` for an existing file after retrieving its current blob SHA. Follow the tool schema and pass the correct SHA when required.
4. If a branch-ref update or compare-and-swap is needed, inspect the latest ref/commit first and use the expected current SHA. If a lease/compare check fails, reread the branch head and reconcile; never force through blindly.
5. After every source/workflow change, verify the resulting commit and query Actions for the newest run on this branch. Match `head_sha` to the latest commit before declaring the build result.
6. For the matching run, inspect job steps using `mcp__GitHub__fetch_workflow_run_jobs`; if failed, inspect logs using `mcp__GitHub__fetch_workflow_job_logs` and fix the actual error, then rebuild.
7. On success, inspect artifacts with `mcp__GitHub__fetch_workflow_run_artifacts`. Give the user the real Actions/artifact page and explain that Actions artifacts expire (the current workflow retains them for 7 days). Do not invent a direct APK URL if only an artifact page is available.
8. Do not claim the app is proven to work between phones merely because CI passed. CI can establish that unit tests and APK assembly pass; real BLE discovery/proximity still requires a deliberate test on the two target phones.
9. The user is Android/mobile-only and dislikes repeated manual steps. Prefer doing repository work directly through the connected tools, report concise factual status, and only ask the user to do a phone action when it is genuinely necessary.

## Current app requirements
- Two equivalent phones; neither is permanently leader/follower.
- First-time pairing can use a QR code or pairing code, then each phone should recognize the other.
- Local/offline operation; BLE is the intended proximity mechanism.
- App is expected to remain open during the experience to avoid unreliable background restrictions.
- Separation must be continuous for 10 seconds before the separation/sad reaction; brief pauses must not reset that timer.
- BLE RSSI estimates proximity and does not prove physical contact or exact distance.
- Keep the emotional interaction as the priority; don't spend time on decorative media before the core flow works.

## Known build fixes already made
- Android SDK setup action is `android-actions/setup-android@v4` (v3 attempted to install an unavailable old package).
- `QRCodeWriter` import was added: `com.google.zxing.qrcode.QRCodeWriter`.
- `onPause()` no longer resets the proximity state, so a temporary pause does not clear the separation timer.
- Keep screen-on behavior cleaned up when the experiment stops or BLE callbacks fail.

## Last verified build (2026-10-12)
- Workflow: **Build Two Hearts Android**, run **#4**
- Run ID: `38299707464`
- Commit: `ef6100ee442149711f4c06e507c6b1f06aac66c0`
- Result: **success**
- Verified steps: `testDebugUnitTest assembleDebug` and `Upload debug APK` succeeded.
- Artifact: `link-debug-apk`, artifact ID `11769818451`, SHA-256 digest `cd1640a1df879eae56346e88b7b167cd7570ddcabe2c456a206b238b9717551f`
- Artifact expires: 2026-10-19 (7-day retention).
- Run page: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38299707464
- Artifact listing: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38299707464
- This is a successful **debug APK build**, not yet proof of real two-phone BLE behavior. Before asking for installation, inspect the app logic and ensure the build corresponds to the latest commit.

## Next steps
1. Review `MainActivity.kt` end-to-end for pairing, BLE advertising/scanning, permissions, proximity thresholds, and the uninterrupted 10-second separation timer.
2. Fix only confirmed issues and rerun the workflow.
3. Verify the latest matching run and artifact again.
4. Then give the user one clear installation/test step and a truthful distinction between CI verification and real-phone verification.
