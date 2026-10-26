# CHRONO CROSS GPT — free GitHub Actions command bridge

This is a workaround for environments where ChatGPT cannot attach a custom MCP server directly. It is **not** a native ChatGPT MCP connection: a commit to the command file triggers GitHub Actions, which acts as the authenticated MCP client and sends one command to the paired CHRONO workspace.

## One-time setup

1. Keep the published CHRONO workspace open and connected. Copy the pairing ID from Diagnostics.
2. In the GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Add secret `CHRONO_BROWSER_SESSION_ID` with the pairing ID as its value. Do not place it in a source file or public issue.
4. The existing `CHRONO_MCP_TOKEN` repository Actions secret must remain configured; never paste or print its value.
5. The first command file is intentionally disabled. No browser command runs until `enabled` is explicitly changed to `true`.

If browser site data/localStorage is cleared and CHRONO displays a new pairing ID, update the secret to match the new ID.

## How a command runs

The dedicated workflow only triggers when `tools/chrono-browser-command.json` changes on `main`. Its script validates the request, authenticates with the MCP endpoint, confirms the tool is available, sends one supported action, and requires a persisted matching acknowledgement. It never prints the bearer token or pairing ID.

Supported actions:
- `navigate` with a public HTTP(S) `url`
- `new_tab`
- `select_tab` with a positive integer `tabId`

The repository is public. **The command JSON and its Git history are public**, so use public URLs only and never include private pages, login links, signed URLs, secrets, tokens, or sensitive query parameters. The script blocks several common secret-like query keys, but that is not a substitute for checking the URL yourself.

A successful result means the CHRONO workspace accepted the command; it does not prove the target website finished loading. This bridge does not click/type inside third-party page DOM, access cookies, control Android Chrome, or connect the current ChatGPT conversation as a native MCP host.

## Command JSON

Edit `tools/chrono-browser-command.json` with a new `requestId` for each command. Example for a public navigation:

```json
{
  "enabled": true,
  "requestId": "nav-example-001",
  "action": "navigate",
  "url": "https://example.com/"
}
```

Use a fresh request ID and update the file through a repository commit to trigger the workflow. An action is not considered verified unless the workflow logs show `status: acknowledged`.
