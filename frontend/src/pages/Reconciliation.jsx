import { useEffect, useState } from "react";
import axios from "axios";

function Reconciliation() {

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReconciliation = async () => {

    try {

      setLoading(true);
      setError("");

      const response = await axios.get(
        "http://127.0.0.1:8000/reconciliation"
      );

      console.log("RECONCILIATION:", response.data);

      const results = response.data?.results || [];

const missing = results
  .filter((item) => item.type === "RECONSTRUCTION_ONLY")
  .map((item) => item.record);

const extra = results
  .filter((item) => item.type === "FLAT_ONLY")
  .map((item) => item.record);

const phantoms = results
  .filter((item) => item.type === "PHANTOM_ENTRY");

const mismatches = results
  .filter((item) => item.type === "MATERIAL_MISMATCH");

setResult({
  reconstructed_count: 0,
  flat_count: 0,

  missing_count: missing.length,
  extra_count: extra.length,
  phantom_count: phantoms.length,
  mismatch_count: mismatches.length,

  missing,
  extra,
  phantoms,
  mismatches,
});

    } catch (err) {

      console.error(err);

      setError("Unable to load reconciliation results");

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {
    loadReconciliation();
  }, []);


  if (loading) {

    return (
      <div className="page">
        <div className="loading">
          Running BOM reconciliation...
        </div>
      </div>
    );

  }


  if (error) {

    return (
      <div className="page">
        <div className="error">
          {error}
        </div>
      </div>
    );

  }


  const passed =
    result &&
    result.missing_count === 0 &&
    result.extra_count === 0 &&
    result.phantom_count === 0 &&
    result.mismatch_count === 0;


  return (

    <div className="page">

      {/* HEADER */}

      <div className="page-title">

        <h2>BOM Reconciliation</h2>

        <p>
          Independently reconstructed BOM paths compared
          against BOM_FLAT.
        </p>

      </div>


      {/* STATUS */}

      <div
        className={
          passed
            ? "reconciliation-status success"
            : "reconciliation-status failure"
        }
      >

        <div className="status-icon">
          {passed ? "✓" : "!"}
        </div>

        <div>

          <strong>
            {passed
              ? "BOM RECONCILIATION PASSED"
              : "BOM RECONCILIATION FAILED"}
          </strong>

          <p>
            {passed
              ? "All reconstructed manufacturing paths are consistent with BOM_FLAT."
              : "Differences were detected between the reconstructed BOM and BOM_FLAT."}
          </p>

        </div>

      </div>


      {/* SUMMARY CARDS */}

      <div className="reconciliation-grid">

        <MetricCard
          title="Reconstructed Paths"
          value={result.reconstructed_count}
        />

        <MetricCard
          title="BOM_FLAT Paths"
          value={result.flat_count}
        />

        <MetricCard
          title="Missing Paths"
          value={result.missing_count}
          danger={result.missing_count > 0}
        />

        <MetricCard
          title="Extra Paths"
          value={result.extra_count}
          danger={result.extra_count > 0}
        />

        <MetricCard
          title="Phantom Materials"
          value={result.phantom_count}
          danger={result.phantom_count > 0}
        />

        <MetricCard
          title="Mismatched Paths"
          value={result.mismatch_count}
          danger={result.mismatch_count > 0}
        />

      </div>


      {/* DETAILS */}

      <div className="reconciliation-sections">

        <DifferenceSection
          title="Missing Paths"
          data={result.missing}
          emptyText="No missing paths detected."
        />

        <DifferenceSection
          title="Extra Paths"
          data={result.extra}
          emptyText="No extra paths detected."
        />

        <DifferenceSection
          title="Phantom Materials"
          data={result.phantoms}
          emptyText="No phantom materials detected."
        />

        <DifferenceSection
          title="Intermediate Mismatches"
          data={result.mismatches}
          emptyText="No intermediate mismatches detected."
        />

      </div>

    </div>

  );
}


/* =====================================================
   METRIC CARD
   ===================================================== */

function MetricCard({
  title,
  value,
  danger = false
}) {

  return (

    <div
      className={
        danger
          ? "reconciliation-card danger"
          : "reconciliation-card"
      }
    >

      <div className="metric-title">
        {title}
      </div>

      <div className="metric-value">
        {value}
      </div>

    </div>

  );
}


/* =====================================================
   DIFFERENCE SECTION
   ===================================================== */

function DifferenceSection({
  title,
  data,
  emptyText
}) {

  const hasData =
    Array.isArray(data) && data.length > 0;


  return (

    <div className="difference-section">

      <div className="difference-header">

        <h3>{title}</h3>

        <span>
          {hasData ? data.length : 0}
        </span>

      </div>


      {!hasData && (

        <div className="difference-empty">
          ✓ {emptyText}
        </div>

      )}


      {hasData && (

        <div className="difference-list">

          {data.map((item, index) => (

            <ReconciliationItem
              key={index}
              type={title}
              item={item}
            />

          ))}

        </div>

      )}

    </div>

  );
}

function ReconciliationItem({ type, item }) {

  // -----------------------------------------------
  // MISMATCH
  // -----------------------------------------------

  if (
    type === "Intermediate Mismatches" &&
    item.reconstructed_path &&
    item.flat_path
  ) {

    return (

      <div className="reconciliation-item">

        <div className="item-title">
          {item.fpn}
        </div>

        <div className="mismatch-comparison">

          <div>

            <div className="comparison-label">
              RECONSTRUCTED
            </div>

            <PathDisplay
              path={item.reconstructed_path}
              highlight={item.stage}
            />

          </div>


          <div>

            <div className="comparison-label">
              BOM_FLAT
            </div>

            <PathDisplay
              path={item.flat_path}
              highlight={item.stage}
            />

          </div>

        </div>

        <div className="mismatch-message">

          Stage <strong>{item.stage}</strong> differs:

          <strong>
            {" "}
            {item.reconstructed}
          </strong>

          {" → "}

          <strong>
            {item.flat}
          </strong>

        </div>

      </div>

    );
  }


  // -----------------------------------------------
  // NORMAL PATH
  // -----------------------------------------------

  if (Array.isArray(item)) {

    return (

      <div className="reconciliation-item">

        <PathDisplay path={item} />

      </div>

    );

  }


  // -----------------------------------------------
  // PHANTOM
  // -----------------------------------------------

  if (typeof item === "string") {

    return (

      <div className="reconciliation-item">

        <span className="phantom-material">
          {item}
        </span>

      </div>

    );

  }


  // -----------------------------------------------
  // FALLBACK
  // -----------------------------------------------

  return (

    <div className="reconciliation-item">

      <pre>
        {JSON.stringify(item, null, 2)}
      </pre>

    </div>

  );
}

function PathDisplay({ path, highlight }) {

  const stages = [
    "FPN",
    "PKGD",
    "TSTD",
    "ASMBLD",
    "MOD_A",
    "MOD_B",
    "MOD_C",
    "CHIP",
    "DIE",
    "WAFER",
    "FAB_OUT",
    "RAW"
  ];


  return (

    <div className="path-display">

      {path.map((material, index) => {

        if (!material) return null;

        const isHighlighted =
          highlight === stages[index];

        return (

          <div
            className={
              isHighlighted
                ? "path-node highlighted"
                : "path-node"
            }
            key={`${material}-${index}`}
          >

            <span className="path-stage">
              {stages[index]}
            </span>

            <span className="path-material">
              {material}
            </span>

          </div>

        );

      })}

    </div>

  );
}

export default Reconciliation;