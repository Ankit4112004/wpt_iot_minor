const MODELS = [
  {
    name: "Temperature Soft-Sensor",
    type: "Supervised regression · Physics-constrained gradient boosting",
    accent: "#ef4444",
    metric: "MAE 0.58 °C · unseen cells",
    what: "Estimates battery temperature during charging from the charging current (as C-rate), ambient temperature and two filtered I² heat terms that model thermal lag.",
    why: "The real charging circuit has no temperature sensor. Trained on 1,183 real NASA charge cycles at 4, 24 and 43 °C ambient, with monotonic constraints so less current always means a lower predicted temperature — safe to use for closed-loop control.",
    use: "Drives the temperature gauge and the over-temp safety alert on the dashboard.",
  },
  {
    name: "Anomaly Detector",
    type: "Unsupervised · One-Class SVM",
    accent: "#8b5cf6",
    metric: "0% false alarms · 71/71 glitches",
    what: "Flags readings outside the charger's normal voltage–current–power operating envelope, such as coupling loss from a misaligned pad, overcurrent, pack voltage sag or corrupted telemetry.",
    why: "Unsupervised — it learns 'normal' from 526 readings of our own Simulink WPT system logged to ThingSpeak, needing no fault labels. Tested on held-out normal data and on 71 real glitch readings from the channel.",
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
          Two models — a temperature soft-sensor trained on real NASA Li-ion charge cycles, and an anomaly detector trained on our own WPT telemetry.
        </p>
      </header>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {MODELS.map((m) => <ModelCard key={m.name} m={m} />)}
      </div>
    </div>
  );
}
