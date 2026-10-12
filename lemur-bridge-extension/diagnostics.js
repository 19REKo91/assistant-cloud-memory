const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const rawEl = document.getElementById("raw");
const refreshEl = document.getElementById("refresh");

function send(action) {
  return new Promise((resolve) => {
    try {
      chrome.runtime.sendMessage({ action }, (response) => {
        if (chrome.runtime.lastError) {
          resolve({ error: chrome.runtime.lastError.message });
          return;
        }
        resolve(response || {});
      });
    } catch (error) {
      resolve({ error: error instanceof Error ? error.message : String(error) });
    }
  });
}

function render(data) {
  if (data?.error) {
    statusEl.textContent = "Extension message error: " + data.error;
    rawEl.textContent = JSON.stringify(data, null, 2);
    refreshEl.textContent = "Last refresh attempt: " + new Date().toLocaleString();
    return;
  }

  const state = data.state || {};
  const statusLines = [
    "Listening: " + (data.enabled ? "ON" : "OFF"),
    "Service status: " + (state.status || "No status message recorded"),
    "Feed: " + (state.feed || "not yet confirmed"),
    "Last poll: " + (state.lastPollAt || "not recorded"),
    "Current command ID: " + (state.commandId || "not recorded"),
    "Last handled command ID: " + (data.lastCommandId || "not recorded"),
    "Pending navigation: " + (data.pending ? JSON.stringify(data.pending) : "none"),
    "Status updated: " + (state.updatedAt || "not recorded")
  ];
  statusEl.textContent = statusLines.join("\n");

  const result = data.lastResult || state.lastResult;
  resultEl.textContent = result ? JSON.stringify(result, null, 2) : "No result recorded locally yet.";
  rawEl.textContent = JSON.stringify({
    enabled: Boolean(data.enabled),
    state: state,
    lastCommandId: data.lastCommandId || null,
    pending: data.pending || null,
    lastResult: result || null
  }, null, 2);
  refreshEl.textContent = "Last refreshed: " + new Date().toLocaleString();
}

async function refresh() {
  render(await send("readState"));
}

document.getElementById("check").addEventListener("click", async () => {
  statusEl.textContent = "Checking the command feed…";
  render(await send("poll"));
});

document.getElementById("start").addEventListener("click", async () => {
  statusEl.textContent = "Starting listener and checking the feed…";
  const response = await send("start");
  if (response.error) render(response);
  else await refresh();
});

document.getElementById("stop").addEventListener("click", async () => {
  statusEl.textContent = "Stopping listener…";
  const response = await send("stop");
  if (response.error) render(response);
  else await refresh();
});

void refresh();
setInterval(() => { void refresh(); }, 3000);
