# Lemur Browser Bridge — proof of concept

This is an isolated prototype on branch `lemur-browser-command-poc`. It is not a production controller.

## Flow

1. The extension polls the public command document at `SYNC/LEMUR_COMMAND.json`.
2. It accepts only `idle` or `navigate` and only two public test destinations: `https://example.com/` and `https://www.iana.org/help/example-domains`.
3. After the page finishes loading, it submits only the command ID, requested/actual test URL, page title, completion time, and a fixed source label.
4. This Worker accepts the result only when its command ID matches the current repository command and stores the first result for that ID in a Durable Object.
5. Read a result at `/result/<command-id>`; use `/health` for a non-sensitive health check.

## Safety limits

- No arbitrary URL navigation.
- No page-body, screenshot, cookies, form values, or browsing-history collection.
- Do not use the prototype on logged-in, private, financial, medical, or otherwise sensitive pages.
- The result endpoint is public and metadata-only. A malicious party could race to submit a fabricated first result for the current public command. Therefore this prototype is for a harmless smoke test only; production would require authenticated result submissions and an explicit trusted pairing flow.
- The Worker is separate from `chatgpt-vision-bridge` and does not modify the production Vision Bridge.

## Deployment

The dedicated workflow deploys this Worker only when files under `lemur-bridge-worker/` change on this branch. It requires the repository's existing `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` Actions secrets.
