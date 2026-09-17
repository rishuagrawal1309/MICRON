from backend.app.core.graph import BOMGraph
from backend.app.core.flatten import BOMFlattener


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
# Reconstruct all BOM paths
# ---------------------------------------------------------

records = flattener.reconstruct_all()


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\n=== RECONSTRUCTED BOM_FLAT ===")

print("Total reconstructed paths:", len(records))

for i, record in enumerate(records[:10], start=1):

    print(f"\nRecord {i}")

    for column, value in record.items():
        print(f"{column}: {value}")