from backend.app.core.graph import BOMGraph
from backend.app.core.impact import BOMImpact


graph = BOMGraph()
graph.build_graph()

impact = BOMImpact(graph)

result = impact.shortage_impact("RAW-0001")

print("\n=== SHORTAGE IMPACT ===")

for item in result:
    print(item)