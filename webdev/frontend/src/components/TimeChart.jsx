import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";

export default function TimeChart({ title, data, dataKey, color, unit, tag }) {
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="font-semibold leading-none tracking-tight text-sm">{title}</h3>
        {tag && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md uppercase tracking-wider bg-zinc-800 text-zinc-300 border border-zinc-700">{tag}</span>}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data} margin={{ top: 6, right: 10, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id={`g-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis dataKey="t" tick={{ fill: "var(--muted-foreground)", fontSize: 11, fontWeight: 500 }} minTickGap={40} />
          <YAxis tick={{ fill: "var(--muted-foreground)", fontSize: 11, fontWeight: 500 }} width={44} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: "0.5rem", color: "var(--foreground)", boxShadow: "none", padding: "12px 16px" }}
            labelFormatter={(label, payload) => {
              const ts = payload && payload[0] && payload[0].payload.ts;
              if (!ts) return label;
              return new Date(ts).toLocaleString([], {
                day: "2-digit", month: "short", year: "numeric",
                hour: "2-digit", minute: "2-digit", second: "2-digit",
              });
            }}
            formatter={(v) => [`${v} ${unit}`, title]}
          />
          <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#g-${dataKey})`} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
