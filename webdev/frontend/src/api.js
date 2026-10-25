const BASE = import.meta.env.VITE_API_BASE || "";
const REQUEST_TIMEOUT_MS = 8000;

async function getJSON(path, method = "GET") {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(BASE + path, {
      method,
      cache: "no-store",
      headers: { "Cache-Control": "no-cache" },
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  latest: () => getJSON("/api/readings/latest"),
  series: (n = 120) => getJSON(`/api/readings?limit=${n}`),
  alerts: () => getJSON("/api/alerts?limit=10"),
  summary: () => getJSON("/api/analytics/summary"),
  scenarios: () => getJSON("/api/demo/scenarios"),
  startScenario: (name) => getJSON(`/api/demo/scenarios/${name}`, "POST"),
  stopScenario: () => getJSON("/api/demo/stop", "POST"),
};
