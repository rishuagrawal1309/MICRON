import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">

      <div className="logo">
        <div className="logo-title">MICRON</div>
        <div className="logo-subtitle">BOM INTELLIGENCE</div>
      </div>

      <nav className="navigation">

        <NavLink
          to="/"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <span>▦</span>
          Dashboard
        </NavLink>

        <NavLink
          to="/bom"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <span>⌘</span>
          BOM Explorer
        </NavLink>

        <NavLink
          to="/anomalies"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <span>⚠</span>
          Anomalies
        </NavLink>

        <NavLink
          to="/reconciliation"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <span>⇄</span>
          Reconciliation
        </NavLink>

        <NavLink
          to="/impact"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <span>◉</span>
          Impact Analysis
        </NavLink>

        <NavLink
  to="/lineage"
  className={({ isActive }) =>
    isActive ? "nav-item active" : "nav-item"
  }
>
  <span>↔</span>
  Lineage
</NavLink>

        <NavLink
          to="/copilot"
          className={({ isActive }) =>
            isActive ? "nav-item active" : "nav-item"
          }
        >
          <span>✦</span>
          AI Copilot
        </NavLink>

      </nav>

      <div className="sidebar-footer">
        <div className="status-dot"></div>
        Backend Connected
      </div>

    </aside>
  );
}

export default Sidebar;