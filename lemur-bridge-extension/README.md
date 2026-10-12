# Lemur Command Bridge (Prototype)

## What it does

- Polls the repository's public command JSON once per minute after the user presses **Start listening**.
- Navigates only to `https://example.com/` or `https://www.iana.org/help/example-domains`.
- Sends back only the command ID, test URL, title, and completion timestamp.
- Shows the last result in the extension popup; **Stop** cancels polling.

## Install

1. Download the `lemur-command-bridge.crx` file from the latest successful **Package Lemur Extension** GitHub Actions run.
2. Open Lemur's extension manager and use its local CRX import feature.
3. Open the extension popup and press **Start listening**.
4. To test the channel, the command document must be changed on the `lemur-browser-command-poc` branch. The assistant can change that JSON through the connected GitHub tool. The extension reads only this repository/branch.
5. Result retrieval is through the separate Worker endpoint configured in `background.js`.

## Important

This is a one-purpose proof of concept, not a remote desktop or general-purpose phone controller. It cannot click arbitrary pages, read private content, access cookies, or type into forms. Commands are public. Test only on the two allowlisted public pages. If the browser does not support Manifest V3 alarms/service workers reliably, the poller may need adaptation.
