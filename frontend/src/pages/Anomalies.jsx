import { useEffect, useState } from "react";
import axios from "axios";

function Anomalies() {

  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {

    async function loadAnomalies() {

      try {

        const response = await axios.get(
          "http://127.0.0.1:8000/anomalies"
        );

        console.log("ANOMALY API RESPONSE:", response.data);

        // Backend currently returns a list
        setAnomalies(
  Array.isArray(response.data)
    ? response.data
    : response.data?.anomalies || []
);

      } catch (err) {

        console.error(err);

        setError("Unable to load anomaly data");

      } finally {

        setLoading(false);

      }

    }

    loadAnomalies();

  }, []);


  if (loading) {

    return (
      <div className="page">
        <div className="loading">
          Loading anomaly analysis...
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


  // ---------------------------------------------------
  // GROUP ANOMALIES BY TYPE
  // ---------------------------------------------------

  const grouped = {};

  anomalies.forEach((anomaly) => {

    const type =
      anomaly.type ||
      anomaly.anomaly_type ||
      anomaly.category ||
      "UNKNOWN";

    if (!grouped[type]) {
      grouped[type] = [];
    }

    grouped[type].push(anomaly);

  });


  return (

    <div className="page">

      {/* HEADER */}

      <div className="page-title">

        <h2>Anomaly Center</h2>

        <p>
          Detect and investigate manufacturing BOM inconsistencies.
        </p>

      </div>


      {/* SUMMARY */}

      <div className="anomaly-summary">

        {Object.entries(grouped).map(
          ([type, items]) => (

            <div
              className="anomaly-card"
              key={type}
            >

              <div className="anomaly-type">
                {formatType(type)}
              </div>

              <div className="anomaly-count">
                {items.length}
              </div>

            </div>

          )
        )}

      </div>


      {/* TABLE */}

      <div className="anomaly-table-container">

        <table className="anomaly-table">

          <thead>

            <tr>
              <th>TYPE</th>
              <th>MATERIAL</th>
              <th>DETAILS</th>
            </tr>

          </thead>

          <tbody>

            {anomalies.map((anomaly, index) => {

              const type =
                anomaly.type ||
                anomaly.anomaly_type ||
                anomaly.category ||
                "UNKNOWN";

              const material =
                anomaly.material ||
                anomaly.parent ||
                anomaly.child ||
                anomaly.component ||
                anomaly.node ||
                "-";

              return (

                <tr key={index}>

                  <td>

                    <span
                      className={`anomaly-badge ${type.toLowerCase()}`}
                    >
                      {formatType(type)}
                    </span>

                  </td>


                  <td className="material-cell">
                    {material}
                  </td>


                  <td>

                    <pre className="anomaly-details">
                      {JSON.stringify(
                        anomaly,
                        null,
                        2
                      )}
                    </pre>

                  </td>

                </tr>

              );

            })}

          </tbody>

        </table>

      </div>

    </div>

  );
}


/* =====================================================
   FORMAT TYPE
   ===================================================== */

function formatType(type) {

  return String(type)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());

}


export default Anomalies;