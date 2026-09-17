from backend.app.core.graph import BOMGraph
from backend.app.core.analytics import BOMAnalytics


graph = BOMGraph()
graph.build_graph()

analytics = BOMAnalytics(graph)

result = analytics.get_path_statistics()

print("\n=== PATH STATISTICS ===")

print("Shortest path:", result["shortest_path"])
print("Longest path:", result["longest_path"])
print("Average path:", result["average_path"])

print("\nDistribution:")

for length, count in result["distribution"].items():
    print(length, "->", count)