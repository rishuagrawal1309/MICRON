import { useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

function ImpactAnalysis() {

  const [material, setMaterial] = useState("CHP-0001-01");

  const [impact, setImpact] = useState(null);
  const [available, setAvailable] = useState("");
  const [shortage, setShortage] = useState(null);

  const [loading, setLoading] = useState(false);
  const [shortageLoading, setShortageLoading] = useState(false);
  const [error, setError] = useState("");


  // =====================================================
  // ANALYZE COMPONENT
  // =====================================================

  const analyzeImpact = async () => {

    if (!material.trim()) {
      return;
    }

    try {

      setLoading(true);
      setError("");
      setImpact(null);
      setShortage(null);

      const response = await axios.get(
        `${API}/impact/${material.trim()}`
      );

      console.log("IMPACT:", response.data);

      setImpact(response.data);

    } catch (err) {

      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Unable to analyze component impact"
      );

    } finally {

      setLoading(false);

    }
  };


  // =====================================================
  // SHORTAGE SIMULATION
  // =====================================================

  const simulateShortage = async () => {

    if (!available || Number(available) < 0) {
      return;
    }

    try {

      setShortageLoading(true);
      setError("");

      const response = await axios.get(
        `${API}/impact/${material.trim()}/shortage/${Number(available)}`
      );

      console.log("SHORTAGE:", response.data);

      setShortage(response.data);

    } catch (err) {

      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Unable to calculate shortage impact"
      );

    } finally {

      setShortageLoading(false);

    }
  };


  return (

    <div className="page impact-page">

      {/* =================================================
          HEADER
          ================================================= */}

      <div className="page-title">

        <h2>Impact Analysis</h2>

        <p>
          Trace component dependencies and simulate
          manufacturing shortages.
        </p>

      </div>


      {/* =================================================
          SEARCH
          ================================================= */}

      <div className="impact-search">

        <div className="impact-input">

          <label>
            Component Material
          </label>

          <input
            value={material}
            onChange={(e) =>
              setMaterial(e.target.value)
            }
            onKeyDown={(e) => {

              if (e.key === "Enter") {
                analyzeImpact();
              }

            }}
            placeholder="Example: CHP-0001-01"
          />

        </div>

        <button
          onClick={analyzeImpact}
          disabled={loading}
        >
          {loading
            ? "Analyzing..."
            : "Analyze Impact"}
        </button>

      </div>


      {/* =================================================
          ERROR
          ================================================= */}

      {error && (

        <div className="error impact-error">
          {error}
        </div>

      )}


      {/* =================================================
          EMPTY STATE
          ================================================= */}

      {!impact && !loading && !error && (

        <div className="impact-empty">

          <div className="impact-empty-icon">
            ◉
          </div>

          <h3>
            Analyze a BOM Component
          </h3>

          <p>
            Enter a component to discover affected
            finished products, upstream dependencies,
            and downstream raw materials.
          </p>

        </div>

      )}


      {/* =================================================
          RESULTS
          ================================================= */}

      {impact && (

        <>

          {/* COMPONENT */}

          <div className="selected-component">

            <div>

              <span>
                SELECTED COMPONENT
              </span>

              <strong>
                {impact.material}
              </strong>

            </div>

            <div className="component-badge">
              Component
            </div>

          </div>


          {/* THREE COLUMNS */}

          <div className="impact-grid">

            {/* AFFECTED FPNS */}

            <div className="impact-card">

              <div className="impact-card-header">

                <h3>
                  Affected FPNs
                </h3>

                <span>
                  {impact.affected_fpns?.length || 0}
                </span>

              </div>

              <div className="impact-list">

                {impact.affected_fpns?.length ? (

                  impact.affected_fpns.map(
                    (fpn) => (

                      <div
                        className="impact-list-item"
                        key={fpn}
                      >
                        <span>▸</span>
                        {fpn}
                      </div>

                    )
                  )

                ) : (

                  <div className="no-data">
                    No affected FPNs
                  </div>

                )}

              </div>

            </div>


            {/* ANCESTORS */}

            <div className="impact-card">

              <div className="impact-card-header">

                <h3>
                  Upstream / Parents
                </h3>

                <span>
                  {impact.ancestors?.length || 0}
                </span>

              </div>

              <div className="impact-list">

                {impact.ancestors?.length ? (

                  impact.ancestors.map(
                    (node) => (

                      <div
                        className="impact-list-item"
                        key={node}
                      >
                        <span>↑</span>
                        {node}
                      </div>

                    )
                  )

                ) : (

                  <div className="no-data">
                    No ancestors
                  </div>

                )}

              </div>

            </div>


            {/* DESCENDANTS */}

            <div className="impact-card">

              <div className="impact-card-header">

                <h3>
                  Downstream
                </h3>

                <span>
                  {impact.descendants?.length || 0}
                </span>

              </div>

              <div className="impact-list">

                {impact.descendants?.length ? (

                  impact.descendants.map(
                    (node) => (

                      <div
                        className="impact-list-item"
                        key={node}
                      >
                        <span>↓</span>
                        {node}
                      </div>

                    )
                  )

                ) : (

                  <div className="no-data">
                    No descendants
                  </div>

                )}

              </div>

            </div>

          </div>


          {/* =================================================
              SHORTAGE SIMULATOR
              ================================================= */}

          <div className="shortage-panel">

            <div className="shortage-header">

              <div>

                <h3>
                  Shortage Impact Simulator
                </h3>

                <p>
                  What happens if this component is
                  available only in a limited quantity?
                </p>

              </div>

            </div>


            <div className="shortage-input-row">

              <div>

                <label>
                  Available Quantity
                </label>

                <input
                  type="number"
                  min="0"
                  value={available}
                  onChange={(e) =>
                    setAvailable(e.target.value)
                  }
                  placeholder="Example: 10"
                />

              </div>

              <button
                onClick={simulateShortage}
                disabled={
                  shortageLoading ||
                  !available
                }
              >
                {shortageLoading
                  ? "Calculating..."
                  : "Simulate Shortage"}
              </button>

            </div>


            {/* SHORTAGE RESULT */}

            {shortage && (

              <ShortageResult
                data={shortage}
              />

            )}

          </div>

        </>

      )}

    </div>

  );
}


/* =====================================================
   SHORTAGE RESULT
   ===================================================== */

function ShortageResult({ data }) {

  const impact = data.impact || {};

  const affected =
    impact.affected_fpns || [];

  return (

    <div className="shortage-result">

      <div className="shortage-stat">

        <span>
          AVAILABLE
        </span>

        <strong>
          {data.available_quantity}
        </strong>

      </div>


      <div className="shortage-stat">

        <span>
          AFFECTED FPNs
        </span>

        <strong>
          {affected.length}
        </strong>

      </div>


      <div className="shortage-stat">

        <span>
          PRODUCTION IMPACT
        </span>

        <strong>
          {impact.max_fpn_supported ??
            impact.max_production ??
            "-"}
        </strong>

      </div>


      <div className="shortage-fpns">

        <h4>
          Impacted Finished Products
        </h4>

        {affected.length === 0 ? (

          <p>
            No affected finished products.
          </p>

        ) : (

          affected.map((item, index) => {

            const fpn =
              typeof item === "string"
                ? item
                : item.fpn || item.material;

            return (
              <div
                key={index}
                className="shortage-fpn"
              >
                {fpn}
              </div>
            );

          })

        )}

      </div>

    </div>

  );
}


export default ImpactAnalysis;