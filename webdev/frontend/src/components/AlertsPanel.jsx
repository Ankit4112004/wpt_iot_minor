function ago(s) {
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

export default function AlertsPanel({ alerts }) {
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-4 flex flex-col h-56">
      <h3 className="font-semibold leading-none tracking-tight text-sm mb-3">Safety Alerts</h3>
      {(!alerts || alerts.length === 0) && (
        <div className="text-emerald-500 text-sm py-2 flex items-center gap-2">No alerts — operating normally ✓</div>
      )}
      <ul className="m-0 p-0 overflow-y-auto pr-2 flex-1">
        {alerts?.map((a, i) => (
          <li key={i} className="flex gap-3 py-3 border-b border-border last:border-0">
            <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${a.severity === 'critical' ? 'bg-red-500' : 'bg-amber-500'}`} />
            <div>
              <div className="text-sm font-medium leading-tight">{a.message}</div>
              <div className="text-xs text-muted-foreground mt-1 tracking-tight">{a.type} · {ago(a.seconds_ago)}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
