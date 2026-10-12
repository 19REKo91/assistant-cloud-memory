const COMMAND_URL = "https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/lemur-browser-command-poc/SYNC/LEMUR_COMMAND.json";
const RESULT_URL = "https://lemur-browser-bridge-poc.flourish-gerbil.workers.dev/result";
const ALARM_NAME = "lemur-command-poll";
const ALLOWED_HOSTS = new Set(["example.com", "www.iana.org"]);

function jsonSafeUrl(value) {
  try {
    const u = new URL(value);
    if (u.protocol !== "https:" || !ALLOWED_HOSTS.has(u.hostname)) return null;
    if (u.hostname === "example.com" && u.pathname !== "/") return null;
    if (u.hostname === "www.iana.org" && u.pathname !== "/help/example-domains") return null;
    return u;
  } catch {
    return null;
  }
}

async function statusPatch(patch) {
  const old = await chrome.storage.local.get(["state"]);
  await chrome.storage.local.set({
    state: { ...(old.state || {}), ...patch, updatedAt: new Date().toISOString() }
  });
}

async function setEnabled(enabled) {
  await chrome.storage.local.set({ enabled });
  if (enabled) {
    await chrome.alarms.create(ALARM_NAME, { periodInMinutes: 1 });
    await pollCommand();
  } else {
    await chrome.alarms.clear(ALARM_NAME);
    await statusPatch({ listening: false, status: "Stopped by user." });
  }
  return { ok: true, enabled };
}

async function pollCommand() {
  const { enabled = false } = await chrome.storage.local.get(["enabled"]);
  if (!enabled) {
    await statusPatch({ status: "Listening is OFF. Tap Start listening in diagnostics." });
    return;
  }
  try {
    const response = await fetch(COMMAND_URL + "?_=" + Date.now(), {
      cache: "no-store",
      headers: { Accept: "application/json" }
    });
    if (!response.ok) throw new Error("Command feed HTTP " + response.status);
    const command = await response.json();
    if (command?.version !== 1 || typeof command.id !== "string" || command.id.length < 8 || command.id.length > 100) {
      throw new Error("Invalid command format.");
    }

    const { lastCommandId = "" } = await chrome.storage.local.get(["lastCommandId"]);
    await statusPatch({
      listening: true,
      feed: "connected",
      lastPollAt: new Date().toISOString(),
      commandId: command.id,
      status: "Command feed checked."
    });
    if (command.id === lastCommandId) {
      // Recovery path: mobile service workers can miss the one-shot tab update
      // while suspended. Re-check the pending tab even when the command ID is unchanged.
      const { pending } = await chrome.storage.local.get(["pending"]);
      if (pending && !pending.recording && typeof pending.tabId === "number") {
        try {
          const pendingTab = await chrome.tabs.get(pending.tabId);
          if (pendingTab.status === "complete") {
            await finishNavigation(pending.tabId, pendingTab);
          }
        } catch {
          // Keep pending state for diagnosis; do not silently discard a possible result.
          await statusPatch({
            status: "Pending navigation tab could not be rechecked; pending state retained."
          });
        }
      }
      return;
    }

    if (command.action === "idle") {
      await chrome.storage.local.set({ lastCommandId: command.id });
      await statusPatch({ status: "Idle command acknowledged.", commandId: command.id });
      return;
    }

    if (command.action !== "navigate") throw new Error("Unsupported action: " + String(command.action));
    const target = jsonSafeUrl(command.url);
    if (!target) throw new Error("Blocked: URL is outside the public test allowlist.");

    const { pending } = await chrome.storage.local.get(["pending"]);
    if (pending && pending.commandId !== command.id) {
      // Recover a stale completed navigation left behind by a suspended mobile worker.
      if (pending.recording) {
        await chrome.storage.local.remove("pending");
      } else if (typeof pending.tabId === "number") {
        try {
          const previousTab = await chrome.tabs.get(pending.tabId);
          if (previousTab.status === "complete") {
            await finishNavigation(pending.tabId, previousTab);
          }
        } catch {
          // The previous tab no longer exists; no result can be completed from it.
          await chrome.storage.local.remove("pending");
        }
      }
      const afterRecovery = await chrome.storage.local.get(["pending"]);
      if (afterRecovery.pending && afterRecovery.pending.commandId !== command.id) {
        throw new Error("A previous navigation is still pending; close or finish that public test tab, then check again.");
      }
    }

    await statusPatch({ status: "Opening approved public test page…", commandId: command.id });
    const tab = await chrome.tabs.create({ url: target.href, active: true });
    const item = {
      commandId: command.id,
      requestedUrl: target.href,
      tabId: tab.id,
      startedAt: new Date().toISOString(),
      recording: false
    };
    // Only mark a command handled after the browser confirms a tab was created.
    await chrome.storage.local.set({ lastCommandId: command.id, pending: item });

    // In case the page completed before pending was saved.
    if (typeof tab.id === "number") {
      const current = await chrome.tabs.get(tab.id);
      if (current.status === "complete") await finishNavigation(tab.id, current);
    }
  } catch (error) {
    await statusPatch({
      listening: true,
      feed: "error",
      status: error instanceof Error ? error.message : String(error),
      lastPollAt: new Date().toISOString()
    });
  }
}

async function postResult(result) {
  const response = await fetch(RESULT_URL, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(result)
  });
  const body = await response.json().catch(() => ({}));
  if (response.status === 409 && body.error === "result_already_recorded") {
    return { alreadyRecorded: true, status: response.status, body };
  }
  if (!response.ok || body.ok !== true) {
    throw new Error("Result endpoint HTTP " + response.status + ": " + String(body.error || "unexpected_response"));
  }
  return { alreadyRecorded: false, status: response.status, body };
}

async function retryLastResult() {
  const { lastResult } = await chrome.storage.local.get(["lastResult"]);
  if (!lastResult || typeof lastResult.id !== "string") {
    return { ok: false, error: "No saved local result is available to retry." };
  }
  const outcome = await postResult(lastResult);
  await statusPatch({
    status: outcome.alreadyRecorded ? "Result was already recorded by the server." : "Saved result successfully sent.",
    lastResult,
    resultEndpointStatus: outcome.status,
    resultAcknowledgement: outcome.body
  });
  return { ok: true, alreadyRecorded: outcome.alreadyRecorded };
}

async function finishNavigation(tabId, tab) {
  const { pending } = await chrome.storage.local.get(["pending"]);
  if (!pending || pending.tabId !== tabId || pending.recording) return;
  const actual = jsonSafeUrl(tab.url || "");
  if (!actual) {
    await chrome.storage.local.remove("pending");
    await statusPatch({ status: "Navigation ended outside the test allowlist; result was not shared." });
    return;
  }

  await chrome.storage.local.set({ pending: { ...pending, recording: true } });
  const result = {
    id: pending.commandId,
    action: "navigate",
    requestedUrl: pending.requestedUrl,
    actualUrl: actual.origin + actual.pathname,
    title: String(tab.title || "").slice(0, 180),
    completedAt: new Date().toISOString(),
    source: "lemur-extension-poc"
  };

  await chrome.storage.local.set({ lastResult: result });
  try {
    const outcome = await postResult(result);
    await statusPatch({
      status: outcome.alreadyRecorded ? "Result was already recorded by the server." : "Page result sent and acknowledged.",
      lastResult: result,
      resultEndpointStatus: outcome.status,
      resultAcknowledgement: outcome.body
    });
  } catch (error) {
    // Keep the local result so it can still be inspected even if the network path fails.
    await chrome.storage.local.set({ lastResult: result });
    await statusPatch({
      status: "Page opened; result stayed local because the return path failed: " +
        (error instanceof Error ? error.message : String(error)),
      lastResult: result
    });
  } finally {
    await chrome.storage.local.remove("pending");
  }
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) void pollCommand();
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") void finishNavigation(tabId, tab);
});

// Without a popup configured in the manifest, tapping the extension icon opens
// a full diagnostics tab. This works around mobile browsers that do not show
// extension popups reliably.
if (chrome.action?.onClicked) {
  chrome.action.onClicked.addListener(async () => {
    const diagnosticsUrl = chrome.runtime.getURL("diagnostics.html");
    try {
      const matches = await chrome.tabs.query({ url: diagnosticsUrl });
      const existing = matches.find((tab) => typeof tab.id === "number");
      if (existing && typeof existing.id === "number") {
        await chrome.tabs.update(existing.id, { active: true });
        return;
      }
      await chrome.tabs.create({ url: diagnosticsUrl, active: true });
    } catch (error) {
      await statusPatch({
        status: "Could not open diagnostics page: " +
          (error instanceof Error ? error.message : String(error))
      });
    }
  });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.action === "start") {
    setEnabled(true).then(sendResponse).catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  if (message?.action === "stop") {
    setEnabled(false).then(sendResponse).catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  if (message?.action === "poll") {
    pollCommand().then(async () => {
      const result = await chrome.storage.local.get(["state", "lastResult", "enabled", "lastCommandId", "pending"]);
      sendResponse(result);
    }).catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  if (message?.action === "retryResult") {
    retryLastResult().then(sendResponse).catch(async (error) => {
      await statusPatch({ status: "Result retry failed: " + (error instanceof Error ? error.message : String(error)) });
      sendResponse({ ok: false, error: error instanceof Error ? error.message : String(error) });
    });
    return true;
  }
  if (message?.action === "readState") {
    chrome.storage.local.get(["state", "lastResult", "enabled", "lastCommandId", "pending"]).then(sendResponse);
    return true;
  }
  return false;
});

chrome.runtime.onInstalled.addListener(async () => {
  await statusPatch({
    listening: true,
    status: "Auto-listening enabled. Checking the approved public test command."
  });
  await setEnabled(true);
});

chrome.runtime.onStartup.addListener(async () => {
  const { enabled } = await chrome.storage.local.get(["enabled"]);
  if (enabled) await chrome.alarms.create(ALARM_NAME, { periodInMinutes: 1 });
});
