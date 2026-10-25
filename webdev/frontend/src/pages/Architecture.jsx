const STACK = [
  ["Frontend", "React + Vite + Tailwind", "Dashboard, charts (Recharts)"],
  ["Backend", "FastAPI (Python)", "REST API + ingestion worker + auto /docs"],
  ["Database", "PostgreSQL (Neon)", "Source of truth: readings, predictions, alerts"],
  ["ML", "scikit-learn", "2 models trained on real NASA battery data"],
  ["Data source", "ThingSpeak / MATLAB", "Live telemetry (optional) + recorded replay"],
  ["Hosting", "Vercel · Render · Neon", "Frontend · backend · database"],
];

export default function Architecture() {
  return (
    <div className="space-y-8 pb-16 mx-auto max-w-5xl">
      <header className="border-b pb-6">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">System Architecture</h1>
        <p className="mt-2 text-muted-foreground">Data pipeline from the battery telemetry to the monitoring dashboard.</p>
      </header>

      <div className="rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-muted/40">
          <h3 className="font-semibold text-sm">Data Pipeline</h3>
        </div>
        <div className="p-4 overflow-x-auto">
          <pre className="text-xs leading-relaxed text-muted-foreground font-mono bg-secondary/30 p-4 rounded border">
{`ThingSpeak (Live Telemetry) ──┐
                              ▼
              Ingestion Worker (every 3s)
              Fallback: LIVE → REPLAY → last-known
                              │  Evaluates 2 ML models
                              ▼
         PostgreSQL  ◄── readings, predictions, alerts
              ▲
              │  REST API
         FastAPI  ──►  React Dashboard (Database-driven)`}
          </pre>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm flex flex-col">
          <div className="p-4 border-b bg-muted/40">
            <h3 className="font-semibold text-sm">Design Decisions</h3>
          </div>
          <div className="p-5 flex-1">
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li className="flex gap-3"><span className="text-muted-foreground mt-0.5">•</span><div><b className="text-foreground font-medium">Backend as Source of Truth:</b> Frontend only reads the database, avoiding direct hardware dependencies and degrading gracefully during outages.</div></li>
              <li className="flex gap-3"><span className="text-muted-foreground mt-0.5">•</span><div><b className="text-foreground font-medium">Live & Replay Modes:</b> In the absence of live data, the worker falls back to pre-recorded cycles for continuous visualization.</div></li>
              <li className="flex gap-3"><span className="text-muted-foreground mt-0.5">•</span><div><b className="text-foreground font-medium">Synchronous Worker:</b> A lightweight scheduled task suitable for low-frequency telemetry.</div></li>
              <li className="flex gap-3"><span className="text-muted-foreground mt-0.5">•</span><div><b className="text-foreground font-medium">ML Integrity:</b> All metrics reflect cross-validated performance on held-out data to prevent leakage.</div></li>
            </ul>
          </div>
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm flex flex-col">
          <div className="p-4 border-b bg-muted/40">
            <h3 className="font-semibold text-sm">Technology Stack</h3>
          </div>
          <div className="p-0 flex-1">
            <table className="w-full text-sm">
              <tbody className="divide-y">
                {STACK.map(([layer, tech, role]) => (
                  <tr key={layer} className="hover:bg-muted/30">
                    <td className="py-3 px-5 font-medium whitespace-nowrap">{layer}</td>
                    <td className="py-3 px-5 text-foreground">{tech}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
