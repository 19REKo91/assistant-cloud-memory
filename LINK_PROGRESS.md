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
