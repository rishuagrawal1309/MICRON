import { useEffect, useState } from "react";
import axios from "axios";

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [analyticsResponse, anomaliesResponse] =
          await Promise.all([
            axios.get("http://127.0.0.1:8000/analytics"),
            axios.get("http://127.0.0.1:8000/anomalies"),
          ]);

        setAnalytics(analyticsResponse.data);
        setAnomalies(anomaliesResponse.data.anomalies || []);
      } catch (error) {
        console.error("Dashboard API error:", error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const statCards = [
    {
      label: "Materials",
      value: analytics?.materials ?? 0,
      icon: "◈",
      description: "Total materials in BOM",
    },
    {
      label: "Finished Products",
      value: analytics?.finished_products ?? 0,
      icon: "▣",
      description: "Finished product nodes",
    },
    {
      label: "Manufacturing Paths",
      value: analytics?.manufacturing_paths ?? 0,
      icon: "⌁",
      description: "Detected production paths",
    },
    {
      label: "Anomalies",
      value: anomalies.length,
      icon: "⚠",
      description:
        anomalies.length === 0
          ? "No issues detected"
          : "Issues requiring attention",
    },
  ];

  return (
    <div className="dashboard-page">

      {/* ================================================= */}
      {/* HERO */}
      {/* ================================================= */}

      <section className="dashboard-hero">

        <div>
          <div className="eyebrow">
            <span className="eyebrow-dot"></span>
            BOM INTELLIGENCE PLATFORM
          </div>

          <h1>Manufacturing Overview</h1>

          <p>
            Monitor your bill of materials, manufacturing paths,
            and structural anomalies from a single workspace.
          </p>
        </div>

        <div className="system-status">
          <span className="system-status-dot"></span>

          <div>
            <strong>System Operational</strong>
            <span>Backend connected</span>
          </div>
        </div>

      </section>

      {/* ================================================= */}
      {/* PRIMARY KPIs */}
      {/* ================================================= */}

      <section className="dashboard-section">

        <div className="section-heading">
          <div>
            <h3>System Overview</h3>
            <p>Current BOM network statistics</p>
          </div>
        </div>

        <div className="dashboard-stat-grid">

          {statCards.map((card, index) => (
            <div
              className={`dashboard-stat-card card-${index}`}
              key={card.label}
            >

              <div className="stat-card-top">

                <div className="stat-icon">
                  {card.icon}
                </div>

                <span className="stat-indicator">
                  LIVE
                </span>

              </div>

              <div className="stat-card-content">

                <span className="stat-label">
                  {card.label}
                </span>

                <strong className="stat-value">
                  {loading ? "—" : card.value}
                </strong>

                <span className="stat-description">
                  {card.description}
                </span>

              </div>

            </div>
          ))}

        </div>

      </section>

      {/* ================================================= */}
      {/* PATH ANALYTICS */}
      {/* ================================================= */}

      <section className="dashboard-section">

        <div className="section-heading">

          <div>
            <h3>Manufacturing Path Analytics</h3>
            <p>
              Depth and complexity across reconstructed BOM paths
            </p>
          </div>

          <div className="section-badge">
            PATH ANALYSIS
          </div>

        </div>

        <div className="path-analytics-grid">

          <div className="path-card">

            <div className="path-card-header">
              <span className="path-icon">↓</span>

              <span>Shortest Path</span>
            </div>

            <div className="path-value">
              {loading
                ? "—"
                : analytics?.shortest_path ?? 0}
            </div>

            <div className="path-description">
              Minimum manufacturing stages
            </div>

          </div>

          <div className="path-card">

            <div className="path-card-header">
              <span className="path-icon">↑</span>

              <span>Longest Path</span>
            </div>

            <div className="path-value">
              {loading
                ? "—"
                : analytics?.longest_path ?? 0}
            </div>

            <div className="path-description">
              Maximum manufacturing stages
            </div>

          </div>

          <div className="path-card">

            <div className="path-card-header">
              <span className="path-icon">≈</span>

              <span>Average Path</span>
            </div>

            <div className="path-value">
              {loading
                ? "—"
                : Number(analytics?.average_path ?? 0).toFixed(2)}
            </div>

            <div className="path-description">
              Average number of stages
            </div>

          </div>

        </div>

      </section>

      {/* ================================================= */}
      {/* ANOMALY STATUS */}
      {/* ================================================= */}

      <section className="dashboard-section">

        <div className="section-heading">

          <div>
            <h3>Data Quality</h3>
            <p>Current BOM anomaly status</p>
          </div>

        </div>

        <div
          className={
            anomalies.length === 0
              ? "anomaly-panel healthy"
              : "anomaly-panel warning"
          }
        >

          <div className="anomaly-icon">
            {anomalies.length === 0 ? "✓" : "!"}
          </div>

          <div className="anomaly-content">

            <strong>
              {loading
                ? "Checking BOM integrity..."
                : anomalies.length === 0
                ? "BOM structure looks healthy"
                : `${anomalies.length} anomalies detected`}
            </strong>

            <span>
              {loading
                ? "Analyzing your manufacturing data."
                : anomalies.length === 0
                ? "No structural anomalies were reported by the anomaly detector."
                : "Review the Anomalies section to inspect the detected issues."}
            </span>

          </div>

          <div className="anomaly-count">
            {loading ? "—" : anomalies.length}
            <span>issues</span>
          </div>

        </div>

      </section>

    </div>
  );
}

export default Dashboard;