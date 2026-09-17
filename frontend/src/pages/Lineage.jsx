import { useState } from "react";

const Lineage = () => {
  const [material, setMaterial] = useState("");
  const [direction, setDirection] = useState("forward");
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
  if (!material.trim()) {
    return;
  }

  try {
    const response = await fetch(
      `http://localhost:8000/api/lineage/${direction}/${material.trim()}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const data = await response.json();

    console.log("Lineage API response:", data);

    setResults(data.results || []);

  } catch (error) {
    console.error("Lineage fetch failed:", error);
    setResults([]);
  }
};

  return (
    <div style={{ padding: "30px" }}>
      <h1>BOM Lineage</h1>

      <p>
        Trace the complete material lineage through the Bill of Materials.
      </p>

      {/* Search Section */}
      <div
        style={{
          display: "flex",
          gap: "10px",
          marginTop: "25px",
          marginBottom: "30px",
        }}
      >
        <input
          type="text"
          placeholder="Enter material"
          value={material}
          onChange={(e) => setMaterial(e.target.value)}
          style={{
            padding: "10px",
            width: "300px",
            border: "1px solid #ccc",
            borderRadius: "5px",
          }}
        />

        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
          style={{
            padding: "10px",
            borderRadius: "5px",
          }}
        >
          <option value="forward">Forward Lineage</option>
          <option value="reverse">Reverse Lineage</option>
        </select>

        <button
          onClick={handleSearch}
          style={{
            padding: "10px 20px",
            background: "#1976d2",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          Trace Lineage
        </button>
      </div>

      {/* Results */}
      <div>
        {results.length === 0 ? (
          <p>No lineage results.</p>
        ) : (
          results.map((item, index) => (
            <div
              key={index}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "15px",
                marginBottom: "15px",
                background: "#fafafa",
              }}
            >
              <h3>
                {direction === "forward"
                  ? item.material
                  : `${item.material} → ${item.child}`}
              </h3>

              {direction === "forward" && (
                <p>
                  <strong>Quantity:</strong> {item.quantity}
                </p>
              )}

              <p>
                <strong>Path:</strong>
              </p>

              <div>
                {item.path.map((node, i) => (
                  <span key={i}>
                    <span
                      style={{
                        display: "inline-block",
                        padding: "6px 10px",
                        background: "#e3f2fd",
                        borderRadius: "5px",
                        margin: "3px",
                      }}
                    >
                      {node}
                    </span>

                    {i < item.path.length - 1 && " → "}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Lineage;