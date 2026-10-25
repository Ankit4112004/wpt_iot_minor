export default function TempGauge({ temp, limit = 38 }) {
  const t = temp ?? 0;
  const pct = Math.max(0, Math.min(100, (t / (limit + 8)) * 100));
  const color = t >= limit ? "#ef4444" : t >= limit - 5 ? "#f59e0b" : "#10b981";
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="font-semibold leading-none tracking-tight text-sm">Battery Temperature</h3>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md uppercase tracking-wider bg-zinc-800 text-zinc-300 border border-zinc-700">ML soft-sensor</span>
      </div>
      <div className="text-4xl font-semibold tracking-tight" style={{ color }}>
        {temp != null ? temp.toFixed(1) : "—"}<span className="text-base ml-1 opacity-70">°C</span>
      </div>
      <div className="relative h-2 rounded-full bg-zinc-800 my-4 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700 ease-in-out" style={{ width: `${pct}%`, background: color }} />
        <div className="absolute top-0 w-[2px] h-full bg-red-500" style={{ left: `${(limit / (limit + 8)) * 100}%` }} />
      </div>
      <div className="text-xs text-muted-foreground tracking-tight">predicted from voltage & current · limit {limit}°C</div>
    </div>
  );
}
