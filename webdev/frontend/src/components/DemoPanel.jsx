import { useEffect, useState } from "react";
import { api } from "../api";

export default function DemoPanel({ active, onChange }) {
  const [available, setAvailable] = useState([]);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.scenarios().then((d) => setAvailable(d.available)).catch(() => {});
  }, []);

  const run = async (name) => {
    setBusy(name ?? "stop");
    setError(null);
    try {
      if (name) await api.startScenario(name);
      else await api.stopScenario();
      onChange();
    } catch {
      setError("Could not reach the backend. Try again in a few seconds.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold leading-none tracking-tight text-sm">Demo scenarios</h3>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md uppercase tracking-wider bg-zinc-800 text-zinc-300 border border-zinc-700">Simulated</span>
        </div>
        <span className="text-xs text-muted-foreground">
          {active
            ? `${active.label} · ${Math.round(active.progress * 100)}% applied · ends in ${Math.floor(active.seconds_left / 60)}m ${active.seconds_left % 60}s`
            : "Inject a situation into the recorded telemetry and watch the models react"}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {available.map((s) => (
          <button
            key={s.name}
            title={s.description}
            onClick={() => run(s.name)}
            disabled={busy !== null}
            className={`rounded-full border px-4 py-2 text-xs font-medium shadow-sm transition-colors cursor-pointer disabled:opacity-50 ${
              active?.name === s.name ? "bg-amber-500/15 text-amber-500 border-amber-500/30" : "bg-card text-foreground hover:bg-zinc-800"
            }`}
          >
            {busy === s.name ? "Starting..." : s.label}
          </button>
        ))}
        <button
          onClick={() => run(null)}
          disabled={busy !== null || !active}
          className="rounded-full border px-4 py-2 text-xs font-medium shadow-sm bg-card text-emerald-500 border-emerald-500/30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:opacity-40"
        >
          {busy === "stop" ? "Stopping..." : "Back to normal"}
        </button>
      </div>
      {error && <div className="text-xs text-red-500 mt-2">{error}</div>}
    </div>
  );
}
