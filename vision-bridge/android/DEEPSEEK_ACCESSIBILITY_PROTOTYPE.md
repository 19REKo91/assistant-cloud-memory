# DeepSeek Accessibility Prototype — Review Plan

Status: design-only checkpoint. Nothing is enabled in the main branch.

## Goal
Test whether the existing Android app "جسر رائق" can capture a reply from the official DeepSeek Android app and write it to `SYNC/DEEPSEEK_REPLY.md`, without calling a paid model API.

## Proposed opt-in flow
1. User installs a separately built test APK.
2. User manually opens Android Accessibility settings and explicitly enables a clearly named service.
3. The service observes text only while package `com.deepseek.chat` is in the foreground.
4. A reply candidate is debounced and checked for duplicates before it is sent to the existing server-side `/api/sync` endpoint.
5. The endpoint validates `x-sync-write-key` and writes only to `SYNC/DEEPSEEK_REPLY.md`.
6. The service shows a visible status message for success or failure.

## Security constraints
- Do not request or store a GitHub personal access token in the APK.
- Never embed `GITHUB_SYNC_TOKEN` or `SYNC_WRITE_KEY` in source code.
- If the app stores a relay key, encrypt it using Android Keystore and provide a clear delete/disable control.
- Restrict accessibility observation to the official DeepSeek package; do not collect text from other apps.
- Keep the prototype on this branch until a debug APK is built and reviewed.
- Do not merge or enable any paid API workflow.

## Known limitations
- Android accessibility trees vary by app version. The service may fail to identify the newest assistant message or may capture an incomplete/old message.
- This does not automatically submit ChatGPT's prompt into DeepSeek. Sending the prompt remains a separate integration problem.
- Android may pause background work or the user may revoke accessibility permission.
- The current server endpoint must be checked for deployment health and configured secrets before live testing.

## Acceptance tests
- Build a debug APK successfully in GitHub Actions.
- Confirm the service is disabled by default and appears in Android Accessibility settings with a clear description.
- Confirm no text is collected unless the DeepSeek package is foregrounded.
- Confirm the service writes only to `SYNC/DEEPSEEK_REPLY.md`.
- Confirm missing/invalid relay key fails closed and no secret appears in logs.
- Test with a short and a long reply; inspect the actual saved file and check for duplicate writes.
- Do not claim full automation unless both prompt delivery and reply capture are tested.

## Current repository baseline

On this experimental branch, the Android app now declares `DeepSeekReplyAccessibilityService` in `app/src/main/AndroidManifest.xml`, with its event filter in `app/src/main/res/xml/deepseek_reply_accessibility.xml`. The service is opt-in: Android Accessibility must be enabled manually by the device owner; it is not silently enabled by the app.

The manual path previews the full shared/pasted response before archiving it through `/api/archive`. The experimental accessibility path uses `/api/sync` to update `SYNC/DEEPSEEK_REPLY.md`. These are separate workflows and are not interchangeable.

The accessibility candidate is still heuristic (last long text leaf after a debounce). The state machine bounds retries and avoids concurrent writes, but it cannot prove that the captured text is the final assistant reply. A successful CI build does not replace manual device testing. No merge into `main` is implied by this branch.
