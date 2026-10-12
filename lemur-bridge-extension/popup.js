const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");

function show(data) {
  const state = data.state || {};
  statusEl.textContent = [
    data.enabled ? "Listening: ON" : "Listening: OFF",
    state.status || "No status yet",
    state.lastPollAt ? "Last poll: " + state.lastPollAt : ""
  ].filter(Boolean).join("\n");
  const result = data.lastResult || state.lastResult;
  resultEl.textContent = result ? JSON.stringify(result, null, 2) : "No result yet.";
}

async function refresh() {
  chrome.runtime.sendMessage({ action: "readState" }, (data) => {
    if (chrome.runtime.lastError) {
      statusEl.textContent = chrome.runtime.lastError.message;
      return;
    }
    show(data || {});
  });
}

document.getElementById("start").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "start" }, () => refresh());
});
document.getElementById("stop").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "stop" }, () => refresh());
});
document.getElementById("check").addEventListener("click", () => {
  statusEl.textContent = "Checking command feed…";
  chrome.runtime.sendMessage({ action: "poll" }, show);
});
refresh();
