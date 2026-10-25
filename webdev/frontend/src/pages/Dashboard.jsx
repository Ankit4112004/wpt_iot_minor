import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { api } from "../api";
import MetricCard from "../components/MetricCard.jsx";
import TempGauge from "../components/TempGauge.jsx";
import AlertsPanel from "../components/AlertsPanel.jsx";
import TimeChart from "../components/TimeChart.jsx";

const POLL_MS = 3000;

function ago(s) {
  if (s == null) return "—";
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}
const hhmmss = (iso) => new Date(iso).toLocaleTimeString();

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.12, delayChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 70, damping: 20, mass: 1 } },
};

export default function Dashboard() {
  const [latest, setLatest] = useState(null);
  const [series, setSeries] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [online, setOnline] = useState(true);

  const [autoFetch, setAutoFetch] = useState(true);
  const [isFetching, setIsFetching] = useState(false);

  const [baseAgo, setBaseAgo] = useState(0);
  const [localFetchTime, setLocalFetchTime] = useState(Date.now());
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const fetchData = useCallback(async (isManual = false) => {
    if (isManual) setIsFetching(true);
    try {
      const [latestResult, seriesResult, alertsResult, summaryResult] =
        await Promise.allSettled([
          api.latest(),
          api.series(120),
          api.alerts(),
          api.summary(),
        ]);

      if (latestResult.status === "fulfilled") {
        const l = latestResult.value;
        setLatest(l);
        setOnline(true);
        setBaseAgo(l?.last_updated_seconds || 0);
        setLocalFetchTime(Date.now());
      } else {
        setOnline(false);
      }

      if (seriesResult.status === "fulfilled") {
        setSeries(seriesResult.value.map((r) => ({ ...r, t: hhmmss(r.ts) })));
      }
      if (alertsResult.status === "fulfilled") setAlerts(alertsResult.value);
      if (summaryResult.status === "fulfilled") setSummary(summaryResult.value);
    } catch {
      setOnline(false);
    } finally {
      if (isManual) setIsFetching(false);
    }
  }, []);

  useEffect(() => { fetchData(true); }, [fetchData]);

  useEffect(() => {
    if (!autoFetch) return;
    const id = setInterval(() => fetchData(false), POLL_MS);
    return () => clearInterval(id);
  }, [autoFetch, fetchData]);

  const totalSecondsAgo = latest != null ? Math.max(0, baseAgo + Math.floor((now - localFetchTime) / 1000)) : null;

  let badgeColor = "text-emerald-500 border-emerald-500/20";
  let dotColor = "bg-emerald-500";
  let badgeText = "Live (ThingSpeak)";
  let dotPulse = false;

  if (latest == null) {
    badgeColor = "text-amber-500 border-amber-500/20";
    dotColor = "bg-amber-500";
    badgeText = online ? "Connecting…" : "Waking up server… (~50s on first load)";
    dotPulse = true;
  } else if (!online) {
    badgeColor = "text-red-500 border-red-500/20";
    dotColor = "bg-red-500";
    badgeText = "Offline";
  } else if (totalSecondsAgo > 10) {
    badgeColor = "text-red-500 border-red-500/20";
    dotColor = "bg-red-500";
    badgeText = `Last updated ${ago(totalSecondsAgo)}`;
  } else if (latest?.source === "replay") {
    badgeColor = "text-amber-500 border-amber-500/20";
    dotColor = "bg-amber-500";
    badgeText = "Replay";
  } else {
    badgeColor = "text-emerald-500 border-emerald-500/20";
    dotColor = "bg-emerald-500";
    badgeText = "Live (ThingSpeak)";
  }

  return (
    <div className="space-y-8 pb-16">
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Live Dashboard</h1>
          <p className="text-sm text-muted-foreground">Real-time battery telemetry · ML predictions</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className={`flex items-center gap-2 rounded-full border bg-card px-4 py-2 text-xs font-medium shadow-sm ${badgeColor}`}>
            <span className={`w-2 h-2 rounded-full ${dotColor} ${dotPulse ? "animate-pulse" : ""}`} />
            {badgeText}
          </div>
          <button
            onClick={() => fetchData(true)}
            disabled={isFetching}
            className="rounded-full border bg-card px-4 py-2 text-xs font-medium text-foreground shadow-sm hover:bg-zinc-800 transition-colors disabled:opacity-50 cursor-pointer"
          >
            {isFetching ? "Refreshing..." : "Refresh"}
          </button>
          <label className="flex items-center gap-2 rounded-full border bg-card px-4 py-2 text-xs font-medium text-foreground shadow-sm cursor-pointer hover:bg-zinc-800 transition-colors">
            <input type="checkbox" checked={autoFetch} onChange={(e) => setAutoFetch(e.target.checked)} className="accent-emerald-500 cursor-pointer" />
            Auto
          </label>
        </div>
      </header>

      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
        <motion.section className="flex flex-wrap gap-3" variants={item}>
          <div className={`rounded-full border px-4 py-1.5 text-xs font-medium shadow-sm bg-card ${latest?.is_anomaly ? "text-amber-500 border-amber-500/20" : "text-emerald-500 border-emerald-500/20"}`}>
            {latest?.is_anomaly ? "Anomaly detected" : "No anomaly"}
          </div>
          <div className={`rounded-full border px-4 py-1.5 text-xs font-medium shadow-sm bg-card ${summary?.has_active_alert ? "text-red-500 border-red-500/20" : "text-emerald-500 border-emerald-500/20"}`}>
            {summary?.has_active_alert ? "Active alert" : "All clear"}
          </div>
          <div className="rounded-full border px-4 py-1.5 text-xs font-medium shadow-sm bg-card text-muted-foreground">
            Avg power: <b className="text-foreground">{summary?.avg_power_recent ?? "—"} W</b>
          </div>
        </motion.section>

        <motion.section className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4" variants={item}>
          <MetricCard label="Voltage" value={latest?.voltage} unit="Volts (V)" accent="#3b82f6" />
          <MetricCard label="Current" value={latest?.current} unit="Amperes (A)" accent="#06b6d4" />
          <MetricCard label="Power" value={latest?.power} unit="Watts (W)" accent="#da7756" />
          <MetricCard label="State of Charge" value={latest?.soc} unit="%" accent="#8b5cf6" />
        </motion.section>

        <motion.section className="grid grid-cols-1 gap-4 lg:grid-cols-2" variants={item}>
          <TempGauge temp={latest?.predicted_temp} limit={38} />
          <AlertsPanel alerts={alerts} />
        </motion.section>

        <motion.section className="grid grid-cols-1 gap-4 lg:grid-cols-2" variants={item}>
          <TimeChart title="Predicted Temperature" tag="ML" data={series} dataKey="predicted_temp" color="#ef4444" unit="°C" />
          <TimeChart title="Power" data={series} dataKey="power" color="#da7756" unit="W" />
          <TimeChart title="State of Charge" data={series} dataKey="soc" color="#8b5cf6" unit="%" />
          <TimeChart title="Voltage" data={series} dataKey="voltage" color="#3b82f6" unit="V" />
          <TimeChart title="Current" data={series} dataKey="current" color="#06b6d4" unit="A" />
        </motion.section>
      </motion.div>
    </div>
  );
}
