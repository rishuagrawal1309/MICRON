import { useState } from "react";
import { getBomTree } from "../services/api";
import BOMGraph from "../components/bom/BOMGraph";

const STAGES = [
    { name: "FPN", color: "#e3f2fd", border: "#1976d2" },
    { name: "PKGD", color: "#e8f5e9", border: "#388e3c" },
    { name: "TSTD", color: "#fff3e0", border: "#f57c00" },
    { name: "ASMBLD", color: "#f3e5f5", border: "#7b1fa2" },
    { name: "MODULE", color: "#ede7f6", border: "#5e35b1" },
    { name: "CHIP", color: "#fce4ec", border: "#c2185b" },
    { name: "DIE", color: "#fff8e1", border: "#f9a825" },
    { name: "WAFER", color: "#e0f7fa", border: "#00838f" },
    { name: "FAB_OUT", color: "#e8eaf6", border: "#3949ab" },
    { name: "RAW", color: "#f5f5f5", border: "#616161" },
];

function BomExplorer() {

    const [material, setMaterial] = useState("");
    const [bomTree, setBomTree] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const searchBom = async () => {

        if (!material.trim()) {
            setError("Please enter a material ID.");
            return;
        }

        try {

            setLoading(true);
            setError("");

            const data = await getBomTree(material.trim());

            setBomTree(data);

        } catch (err) {

            console.error(err);
            setError("Unable to fetch BOM structure. Please check the material ID.");

        } finally {

            setLoading(false);

        }
    };

    const clearSearch = () => {
        setMaterial("");
        setBomTree(null);
        setError("");
    };

    return (
        <div className="bom-explorer-page">

            {/* ================================================= */}
            {/* HEADER */}
            {/* ================================================= */}

            <section className="bom-hero">

                <div className="bom-hero-content">

                    <div className="bom-eyebrow">
                        <span className="bom-eyebrow-dot"></span>
                        BOM STRUCTURE ANALYSIS
                    </div>

                    <h1>BOM Explorer</h1>

                    <p>
                        Explore multi-level manufacturing BOM structures,
                        material relationships, and production dependencies.
                    </p>

                </div>

                <div className="bom-hero-badge">

                    <span className="hero-badge-icon">⌘</span>

                    <div>
                        <strong>Interactive Graph</strong>
                        <span>Multi-level visualization</span>
                    </div>

                </div>

            </section>


            {/* ================================================= */}
            {/* SEARCH */}
            {/* ================================================= */}

            <section className="bom-search-section">

                <div className="bom-section-heading">

                    <div>
                        <h3>Find Material</h3>
                        <p>
                            Enter a material ID to reconstruct its BOM hierarchy.
                        </p>
                    </div>

                </div>

                <div className="bom-search-box">

                    <div className="bom-input-wrapper">

                        <span className="bom-input-icon">
                            ⌕
                        </span>

                        <input
                            type="text"
                            placeholder="Enter FPN or Material ID, e.g. FPN-0001"
                            value={material}
                            onChange={(e) => {
                                setMaterial(e.target.value);
                                setError("");
                            }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    searchBom();
                                }
                            }}
                        />

                        {material && (
                            <button
                                className="clear-input"
                                onClick={clearSearch}
                                type="button"
                            >
                                ×
                            </button>
                        )}

                    </div>

                    <button
                        className="bom-search-button"
                        onClick={searchBom}
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <span className="button-spinner"></span>
                                Searching
                            </>
                        ) : (
                            <>
                                Search BOM
                                <span>→</span>
                            </>
                        )}
                    </button>

                </div>

                <div className="search-hint">
                    Press <kbd>Enter</kbd> to search
                </div>

            </section>


            {/* ================================================= */}
            {/* ERROR */}
            {/* ================================================= */}

            {error && (
                <div className="bom-error">

                    <div className="bom-error-icon">
                        !
                    </div>

                    <div>
                        <strong>Unable to load BOM</strong>
                        <span>{error}</span>
                    </div>

                </div>
            )}


            {/* ================================================= */}
            {/* STAGE LEGEND */}
            {/* ================================================= */}

            <section className="bom-legend-card">

                <div className="bom-legend-header">

                    <div>
                        <h3>Manufacturing Stages</h3>
                        <p>
                            Material classification used in the BOM graph
                        </p>
                    </div>

                    <span className="stage-count">
                        {STAGES.length} stages
                    </span>

                </div>

                <div className="bom-stage-grid">

                    {STAGES.map((stage) => (

                        <div
                            key={stage.name}
                            className="bom-stage-item"
                        >

                            <span
                                className="bom-stage-dot"
                                style={{
                                    background: stage.color,
                                    border: `2px solid ${stage.border}`,
                                }}
                            />

                            <span className="bom-stage-name">
                                {stage.name}
                            </span>

                        </div>

                    ))}

                </div>

            </section>


            {/* ================================================= */}
            {/* GRAPH */}
            {/* ================================================= */}

            <section className="bom-graph-section">

                <div className="bom-graph-header">

                    <div>

                        <div className="bom-graph-title">

                            <span className="graph-status-dot"></span>

                            <h3>
                                {bomTree
                                    ? `${material.toUpperCase()} BOM Structure`
                                    : "BOM Structure Visualization"
                                }
                            </h3>

                        </div>

                        <p>
                            {bomTree
                                ? "Interactive manufacturing hierarchy"
                                : "Search for a material to visualize its hierarchy"
                            }
                        </p>

                    </div>

                    {bomTree && (
                        <div className="graph-live-badge">
                            ● LIVE
                        </div>
                    )}

                </div>


                {loading && (
                    <div className="bom-loading">

                        <div className="loading-spinner"></div>

                        <strong>Building BOM graph</strong>

                        <span>
                            Traversing material relationships...
                        </span>

                    </div>
                )}


                {!bomTree && !loading && !error && (
                    <div className="bom-empty-state">

                        <div className="empty-graph-icon">
                            ⌘
                        </div>

                        <h3>No BOM selected</h3>

                        <p>
                            Enter a material ID above to explore its
                            complete manufacturing structure.
                        </p>

                    </div>
                )}


                {bomTree && !loading && (
                    <div className="bom-graph-container">

                        <BOMGraph data={bomTree} />

                    </div>
                )}

            </section>

        </div>
    );
}

export default BomExplorer;