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
  if (!enabled) return;
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
      status: "Command feed checked."
    });
    if (command.id === lastCommandId) return;

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
      throw new Error("A previous navigation is still pending; wait for its result.");
    }

    await chrome.storage.local.set({ lastCommandId: command.id });
    await statusPatch({ status: "Opening approved public test page…", commandId: command.id });
    const tab = await chrome.tabs.create({ url: target.href, active: true });
    const item = {
      commandId: command.id,
      requestedUrl: target.href,
      tabId: tab.id,
      startedAt: new Date().toISOString(),
      recording: false
    };
    await chrome.storage.local.set({ pending: item });

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

  try {
    const response = await fetch(RESULT_URL, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(result)
    });
    const responseBody = await response.json().catch(() => ({}));
    if (!response.ok && response.status !== 409) {
      throw new Error("Result endpoint HTTP " + response.status);
    }
    await chrome.storage.local.set({ lastResult: result });
    await statusPatch({
      status: response.status === 409 ? "Result already recorded for this command." : "Page result sent.",
      lastResult: result,
      resultEndpointStatus: response.status,
      resultAcknowledgement: responseBody
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.action === "start") {
    setEnabled(true).then(sendResponse);
    return true;
  }
  if (message?.action === "stop") {
    setEnabled(false).then(sendResponse);
    return true;
  }
  if (message?.action === "poll") {
    pollCommand().then(async () => {
      const result = await chrome.storage.local.get(["state", "lastResult", "enabled"]);
      sendResponse(result);
    });
    return true;
  }
  if (message?.action === "readState") {
    chrome.storage.local.get(["state", "lastResult", "enabled", "lastCommandId"]).then(sendResponse);
    return true;
  }
  return false;
});

chrome.runtime.onInstalled.addListener(async () => {
  const { enabled } = await chrome.storage.local.get(["enabled"]);
  await statusPatch({ listening: Boolean(enabled), status: "Installed. Press Start listening in the extension popup." });
  if (enabled) await chrome.alarms.create(ALARM_NAME, { periodInMinutes: 1 });
});

chrome.runtime.onStartup.addListener(async () => {
  const { enabled } = await chrome.storage.local.get(["enabled"]);
  if (enabled) await chrome.alarms.create(ALARM_NAME, { periodInMinutes: 1 });
});
