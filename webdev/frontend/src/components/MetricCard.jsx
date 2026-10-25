export default function MetricCard({ label, value, unit, accent }) {
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm flex flex-col p-6 border-t-[3px]" style={{ borderTopColor: accent }}>
      <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">{label}</div>
      <div className="text-3xl font-semibold tracking-tight">{value ?? "—"}</div>
      <div className="text-xs text-muted-foreground mt-1">{unit}</div>
    </div>
  );
}
