from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.graph import BOMGraph
from backend.app.core.traversal import BOMTraversal
from backend.app.core.anomalies import BOMAnomalyDetector
from backend.app.core.flatten import BOMFlattener
from backend.app.core.reconciliation import BOMReconciler
from backend.app.core.impact import BOMImpact
from backend.app.core.analytics import BOMAnalytics
from backend.app.core.lineage import BOMLineage


app = FastAPI(
    title="BOM Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------
# Initialize BOM graph
# ---------------------------------------------------------

graph = BOMGraph()
graph.build_graph()

traversal = BOMTraversal(graph)
anomaly_detector = BOMAnomalyDetector(graph)
flattener = BOMFlattener(graph)
reconciler = BOMReconciler(graph, flattener)
impact_analyzer = BOMImpact(graph)
lineage_analyzer = BOMLineage(graph)
analytics = BOMAnalytics(graph)

# ---------------------------------------------------------
# Copilot
# ---------------------------------------------------------

class CopilotRequest(BaseModel):
    prompt: str

# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "BOM Intelligence Platform API is running"
    }


# ---------------------------------------------------------
# BOM Tree
# ---------------------------------------------------------

@app.get("/api/bom/{material}/tree")
def get_bom_tree(material: str):

    return traversal.get_bom_tree(material)

# ---------------------------------------------------------
# Anomaly Detection
# ---------------------------------------------------------

@app.get("/anomalies")
def get_anomalies():

    return {
        "anomalies": anomaly_detector.detect_all_anomalies()
    }

# ---------------------------------------------------------
# BOM Reconciliation
# ---------------------------------------------------------

@app.get("/reconciliation")
def get_reconciliation():

    reconstructed = reconciler.get_reconstructed_records()
    provided = reconciler.get_flat_records()

    results = reconciler.reconcile()

    missing = [
        item["record"]
        for item in results
        if item["type"] == "RECONSTRUCTION_ONLY"
    ]

    extra = [
        item["record"]
        for item in results
        if item["type"] == "FLAT_ONLY"
    ]

    phantoms = [
        item
        for item in results
        if item["type"] == "PHANTOM_ENTRY"
    ]

    mismatches = [
        item
        for item in results
        if item["type"] == "MATERIAL_MISMATCH"
    ]

    return {
        "reconstructed_count": len(reconstructed),
        "flat_count": len(provided),

        "missing_count": len(missing),
        "extra_count": len(extra),
        "phantom_count": len(phantoms),
        "mismatch_count": len(mismatches),

        "missing": missing,
        "extra": extra,
        "phantoms": phantoms,
        "mismatches": mismatches,

        "results": results
    }

# ---------------------------------------------------------
# Impact Analysis
# ---------------------------------------------------------

@app.get("/impact/{material}")
def get_impact(material: str):

    affected = impact_analyzer.shortage_impact(material)

    ancestors = graph.get_all_parents(material)

    descendants = graph.get_children(material)

    affected_fpns = [
        item["fpn"]
        for item in affected
    ]

    return {
        "material": material,
        "affected_fpns": affected_fpns,
        "ancestors": ancestors,
        "descendants": descendants,
        "affected": affected
    }

# ---------------------------------------------------------
# Shortage Impact Simulation
# ---------------------------------------------------------

@app.get("/impact/{material}/shortage/{available_quantity}")
def simulate_shortage(
    material: str,
    available_quantity: float
):

    affected = impact_analyzer.shortage_impact(material)

    affected_fpns = []

    for item in affected:

        affected_fpns.append({
            "fpn": item["fpn"],
            "quantity_impact": item["quantity_impact"],
            "path": item["path"]
        })

    return {
        "material": material,
        "available_quantity": available_quantity,
        "impact": {
            "affected_fpns": affected_fpns,
            "max_fpn_supported": available_quantity
        }
    }


@app.post("/copilot")
def copilot(request: CopilotRequest):

    prompt = request.prompt.lower()

    # =====================================================
    # ANOMALY QUESTIONS
    # =====================================================

    if "anomal" in prompt:

        anomalies = anomaly_detector.detect_all_anomalies()

        return {
            "type": "anomalies",
            "answer": f"I found {len(anomalies)} BOM anomalies.",
            "data": anomalies
        }

    # =====================================================
    # IMPACT / SHORTAGE QUESTIONS
    # =====================================================

    if "shortage" in prompt or "impact" in prompt:

        words = request.prompt.split()

        material = next(
            (
                word.strip(".,?!")
                for word in words
                if any(
                    word.upper().startswith(prefix)
                    for prefix in [
                        "FPN-",
                        "PKGD-",
                        "TSTD-",
                        "ASMBLD-",
                        "MOD-",
                        "CHP-",
                        "CHIP-",
                        "DIE-",
                        "WAFER-",
                        "FAB_OUT-",
                        "RAW-"
                    ]
                )
            ),
            None
        )

        if material:

            material = material.upper()

            try:

                affected = impact_analyzer.shortage_impact(
                    material
                )

                return {
                    "type": "impact",
                    "answer": (
                        f"Shortage impact analysis for {material} "
                        f"found {len(affected)} affected top-level materials."
                    ),
                    "material": material,
                    "data": affected
                }

            except Exception as e:

                return {
                    "type": "error",
                    "answer": f"Unable to analyze impact for {material}.",
                    "error": str(e)
                }

        return {
            "type": "info",
            "answer": (
                "Please provide a material ID, for example "
                "CHP-0001-01, to perform shortage impact analysis."
            )
        }

    # =====================================================
    # BOM STRUCTURE QUESTIONS
    # =====================================================

    if (
    "bom" in prompt
    or "structure" in prompt
    or "path" in prompt
    or "hierarchy" in prompt
    or "component" in prompt
    or "components" in prompt
    or "inside" in prompt
    or "contains" in prompt
    or "contain" in prompt
    or "tree" in prompt
):

        words = request.prompt.split()

        material = next(
            (
                word.strip(".,?!")
                for word in words
                if "-" in word
            ),
            None
        )

        if material:

            material = material.upper()

            try:

                tree = traversal.get_bom_tree(material)

                return {
                    "type": "bom_structure",
                    "answer": (
                        f"Here is the complete BOM structure for {material}."
                    ),
                    "material": material,
                    "data": tree
                }

            except Exception as e:

                return {
                    "type": "error",
                    "answer": (
                        f"Unable to find BOM structure for {material}."
                    ),
                    "error": str(e)
                }

    # =====================================================
    # DEFAULT RESPONSE
    # =====================================================

    return {
        "type": "info",
        "answer": (
            "I can help analyze BOM structures, material shortages, "
            "impact analysis, and BOM anomalies. "
            "Try asking about a specific material such as CHP-0001-01."
        )
    }

# ---------------------------------------------------------
# Dashboard Analytics
# ---------------------------------------------------------

@app.get("/analytics")
def get_analytics():

    all_materials = set(graph.forward_graph.keys())

    for children in graph.forward_graph.values():
        all_materials.update(children)

    finished_products = {
        material
        for material in all_materials
        if material.startswith("FPN-")
    }

    path_statistics = analytics.get_path_statistics()

    return {
        "materials": len(all_materials),
        "finished_products": len(finished_products),
        "manufacturing_paths": sum(
            path_statistics["distribution"].values()
        ),
        "shortest_path": path_statistics["shortest_path"],
        "longest_path": path_statistics["longest_path"],
        "average_path": path_statistics["average_path"],
    }

# ---------------------------------------------------------
# BOM Lineage
# ---------------------------------------------------------

@app.get("/api/lineage/{direction}/{material}")
def get_lineage(
    direction: str,
    material: str
):

    material = material.upper()

    if direction == "forward":

        return {
            "material": material,
            "direction": "forward",
            "results": lineage_analyzer.forward_lineage(material)
        }

    elif direction == "reverse":

        return {
            "material": material,
            "direction": "reverse",
            "results": lineage_analyzer.reverse_lineage(material)
        }

    return {
        "error": "Invalid lineage direction. Use 'forward' or 'reverse'."
    }