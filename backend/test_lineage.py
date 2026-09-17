from backend.app.core.graph import BOMGraph
from backend.app.core.lineage import BOMLineage


graph = BOMGraph()
graph.build_graph()

lineage = BOMLineage(graph)


print("\n=== FORWARD LINEAGE ===")

result = lineage.forward_lineage("FPN-0001")

for item in result:
    print(item)


print("\n=== REVERSE LINEAGE ===")

result = lineage.reverse_lineage("RAW-0001")

for item in result:
    print(item)