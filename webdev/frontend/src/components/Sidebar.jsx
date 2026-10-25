import { useState } from "react";
import { NavLink } from "react-router-dom";

const I = {
  panel: "M9 3v18M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  home: "M3 11l9-8 9 8M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10",
  sliders: "M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6",
  cpu: "M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2M5 5h14v14H5zM9 9h6v6H9z",
  network: "M12 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM5 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM12 9v3M12 12L6 15M12 12l6 3",
};

function Icon({ d }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
      <path d={d} />
    </svg>
  );
}

const NAV = [
  { to: "/", label: "Dashboard", icon: I.home, end: true },
  { to: "/models", label: "Models", icon: I.cpu },
];

export default function Sidebar() {
  const [open, setOpen] = useState(true);

  return (
    <aside
      className={`sticky top-0 h-screen z-50 shrink-0 border-r bg-card flex flex-col transition-all duration-300 ${open ? "w-60" : "w-16"}`}
    >
      
      <div className="flex items-center gap-3 h-16 px-3 border-b">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border bg-secondary/50 text-foreground font-bold text-sm shrink-0 shadow-sm">
          EV
        </div>
        {open && (
          <div className="min-w-0">
            <div className="text-sm font-semibold truncate">WPT Monitor</div>
            <div className="text-[10px] text-muted-foreground truncate">Battery Intelligence</div>
          </div>
        )}
      </div>

      <button
        onClick={() => setOpen((o) => !o)}
        title={open ? "Collapse" : "Expand"}
        className="flex items-center gap-3 px-4 h-11 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors cursor-pointer"
      >
        <Icon d={I.panel} />
        {open && <span className="text-xs">Collapse</span>}
      </button>

      
      <nav className="flex-1 py-2">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            title={n.label}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 h-11 text-sm transition-colors ${
                isActive
                  ? "text-foreground bg-accent border-l-2 border-blue-500"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent border-l-2 border-transparent"
              }`
            }
          >
            <Icon d={n.icon} />
            {open && <span className="truncate">{n.label}</span>}
          </NavLink>
        ))}
      </nav>

      
      <NavLink
        to="/architecture"
        title="Architecture"
        className={({ isActive }) =>
          `flex items-center gap-3 px-4 h-11 transition-colors border-t ${
            isActive
              ? "text-foreground bg-accent border-l-2 border-blue-500"
              : "text-muted-foreground hover:text-foreground hover:bg-accent border-l-2 border-transparent"
          }`
        }
      >
        <Icon d={I.network} />
        {open && <span className="text-xs">Architecture</span>}
      </NavLink>
    </aside>
  );
}
