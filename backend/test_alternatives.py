from backend.app.core.graph import BOMGraph
from backend.app.core.alternatives import BOMAlternatives


graph = BOMGraph()
graph.build_graph()

alternatives = BOMAlternatives(graph)

result = alternatives.find_alternative_paths("RAW-0001")

print("\n=== ALTERNATIVE PATHS ===")

for item in result:
    print(item)