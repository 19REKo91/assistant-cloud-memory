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

function isMatchingCompletedTab(tab, requestedUrl) {
  if (!tab || tab.status !== "complete" || typeof tab.id !== "number") return false;
  const expected = jsonSafeUrl(requestedUrl);
  const actual = jsonSafeUrl(tab.url || "");
  return Boolean(expected && actual &&
    actual.origin + actual.pathname === expected.origin + expected.pathname);
}

async function findCompletedMatchingTab(pending) {
  // Query the full tab list even if tabs.get(pending.tabId) succeeds:
  // on some mobile builds that ID can resolve to a different tab after suspension.
  const tabs = await chrome.tabs.query({});
  return tabs.find((tab) => isMatchingCompletedTab(tab, pending.requestedUrl)) || null;
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

async function recoverPendingNavigation(pending) {
  const match = await findCompletedMatchingTab(pending);
  if (!match) {
    const ageMs = Date.now() - Date.parse(pending.startedAt || "");
    const retryCount = Number(pending.retryCount || 0);

    // Lemur on Android can occasionally return a tab ID without exposing the
    // created tab in a subsequent query. Retry exactly once after a timeout.
    // The URL still passes the same strict public-test allowlist.
    if (Number.isFinite(ageMs) && ageMs >= 60000 && retryCount < 1) {
      const target = jsonSafeUrl(pending.requestedUrl);
      if (target) {
        try {
          const retryTab = await chrome.tabs.create({ url: target.href, active: true });
          const retried = {
            ...pending,
            tabId: retryTab.id,
            retryCount: retryCount + 1,
            startedAt: new Date().toISOString()
          };
          await chrome.storage.local.set({ pending: retried });
          await statusPatch({
            status: "First tab was not found; automatically retried the approved navigation once."
          });
          if (typeof retryTab.id === "number") {
            const current = await chrome.tabs.get(retryTab.id);
            if (isMatchingCompletedTab(current, target.href)) {
              await finishNavigation(retryTab.id, current);
              return true;
            }
          }
          return false;
        } catch (error) {
          await statusPatch({
            status: "Automatic navigation retry failed: " +
              (error instanceof Error ? error.message : String(error))
          });
          return false;
        }
      }
    }
    await statusPatch({
      status: retryCount >= 1
        ? "Pending navigation remains after one automatic retry; no completed matching approved test tab was found."
        : "Pending navigation remains; no completed matching approved test tab was found."
    });
    return false;
  }
  if (match.id !== pending.tabId) {
    pending = { ...pending, tabId: match.id };
    await chrome.storage.local.set({ pending });
  }
  await finishNavigation(match.id, match);
  return true;
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
      const { pending } = await chrome.storage.local.get(["pending"]);
      if (pending && !pending.recording) {
        await recoverPendingNavigation(pending);
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
      if (pending.recording) {
        await chrome.storage.local.remove("pending");
      } else {
        await recoverPendingNavigation(pending);
      }
      const afterRecovery = await chrome.storage.local.get(["pending"]);
      if (afterRecovery.pending && afterRecovery.pending.commandId !== command.id) {
        // If the new approved command targets a different allowlisted page,
        // retire the stale pending record. The old tab cannot be mistaken for
        // the new result because finishNavigation validates the requested URL.
        if (afterRecovery.pending.requestedUrl !== target.href) {
          await chrome.storage.local.remove("pending");
          await statusPatch({
            status: "Discarded stale pending navigation for a different approved test URL."
          });
        } else {
          throw new Error("A previous navigation to the same test URL is still pending; refusing to associate an ambiguous tab with a new command.");
        }
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
    await chrome.storage.local.set({ lastCommandId: command.id, pending: item });

    if (typeof tab.id === "number") {
      const current = await chrome.tabs.get(tab.id);
      if (isMatchingCompletedTab(current, target.href)) await finishNavigation(tab.id, current);
      else await recoverPendingNavigation(item);
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
  let { pending } = await chrome.storage.local.get(["pending"]);
  if (!pending || pending.recording || typeof tabId !== "number") return;

  const requested = jsonSafeUrl(pending.requestedUrl);
  const actual = jsonSafeUrl(tab.url || "");
  if (!actual) {
    if (pending.tabId === tabId) {
      await chrome.storage.local.remove("pending");
      await statusPatch({ status: "Navigation ended outside the test allowlist; result was not shared." });
    }
    return;
  }

  const requestedPath = requested && requested.origin + requested.pathname;
  const actualPath = actual.origin + actual.pathname;
  if (!requestedPath || actualPath !== requestedPath || tab.status !== "complete") return;

  if (pending.tabId !== tabId) {
    pending = { ...pending, tabId };
    await chrome.storage.local.set({ pending });
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
