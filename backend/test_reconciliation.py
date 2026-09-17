from backend.app.core.graph import BOMGraph
from backend.app.core.flatten import BOMFlattener
from backend.app.core.reconciliation import BOMReconciler


# ---------------------------------------------------------
# Build graph
# ---------------------------------------------------------

graph = BOMGraph()
graph.build_graph()


# ---------------------------------------------------------
# Create flattener
# ---------------------------------------------------------

flattener = BOMFlattener(graph)


# ---------------------------------------------------------
# Create reconciler
# ---------------------------------------------------------

reconciler = BOMReconciler(
    graph,
    flattener
)


# ---------------------------------------------------------
# Run reconciliation
# ---------------------------------------------------------

results = reconciler.reconcile()


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\n=== RECONCILIATION RESULTS ===")

print("Total discrepancies:", len(results))

for i, result in enumerate(results[:20], start=1):

    print(f"\n--- Discrepancy {i} ---")

    print("Type:", result["type"])

    if result["type"] == "MATERIAL_MISMATCH":

        print("FPN:", result["fpn"])

        print("Differences:")

        for column, difference in result["differences"].items():

            print(
                f"  {column}: "
                f"{difference['reconstructed']} "
                f"-> "
                f"{difference['provided']}"
            )

    else:

        print("Record:", result["record"])