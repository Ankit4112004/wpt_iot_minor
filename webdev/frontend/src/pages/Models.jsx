const MODELS = [
  {
    name: "Temperature Soft-Sensor",
    type: "Supervised regression · Random Forest",
    accent: "#ef4444",
    metric: "R² 0.98 · ± 0.41 °C",
    what: "Estimates battery temperature from electrical signals (voltage, current, power, time).",
    why: "The real charging circuit has no temperature sensor. Instead of faking it, the model infers temperature from the data we do have — a 'virtual sensor'.",
    use: "Drives the temperature gauge and the over-temp safety alert on the dashboard.",
  },
  {
    name: "Anomaly Detector",
    type: "Unsupervised · Isolation Forest",
    accent: "#8b5cf6",
    metric: "flags ~2% outliers",
    what: "Flags abnormal operating points (unusual voltage/current/power/temperature combos).",
    why: "Unsupervised — it learns what 'normal' charging looks like and flags deviations, needing no labels. Useful for catching faults or foreign objects.",
    use: "Raises anomaly alerts and the anomaly status chip.",
  },
];

function ModelCard({ m }) {
  return (
    <div className="flex flex-col rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-5 border-b flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: m.accent }} />
          <div>
            <h3 className="font-semibold text-base">{m.name}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">{m.type}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium px-2.5 py-1 rounded bg-secondary text-secondary-foreground border">
            {m.metric}
          </span>
        </div>
      </div>
      <div className="p-5 flex-1">
        <dl className="space-y-4 text-sm">
          <div>
            <dt className="text-xs font-medium text-muted-foreground mb-1">Function</dt>
            <dd className="text-foreground leading-relaxed">{m.what}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-muted-foreground mb-1">Rationale</dt>
            <dd className="text-muted-foreground leading-relaxed">{m.why}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-muted-foreground mb-1">Application</dt>
            <dd className="text-muted-foreground leading-relaxed">{m.use}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

export default function Models() {
  return (
    <div className="space-y-8 pb-16">
      <header>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">ML Models</h1>
        <p className="text-sm text-muted-foreground">
          Two models — regression and unsupervised — trained on the real NASA Li-ion battery dataset.
        </p>
      </header>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {MODELS.map((m) => <ModelCard key={m.name} m={m} />)}
      </div>
    </div>
  );
}
