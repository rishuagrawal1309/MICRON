class BOMAnalytics:

    def __init__(self, graph):
        self.graph = graph

    def get_path_statistics(self):

        path_lengths = []

        def dfs(node, depth, visited):

            if node in visited:
                return

            visited.add(node)

            children = self.graph.get_children(node)

            # Leaf reached
            if not children:
                path_lengths.append(depth)
                return

            for child in children:
                dfs(
                    child,
                    depth + 1,
                    visited.copy()
                )

        # Start from top-level materials
        all_children = set(self.graph.reverse_graph.keys())
        all_parents = set(self.graph.forward_graph.keys())

        roots = all_parents - all_children

        for root in roots:
            dfs(root, 1, set())

        if not path_lengths:
            return {
                "shortest_path": 0,
                "longest_path": 0,
                "average_path": 0,
                "distribution": {}
            }

        distribution = {}

        for length in path_lengths:
            distribution[length] = (
                distribution.get(length, 0) + 1
            )

        return {
            "shortest_path": min(path_lengths),
            "longest_path": max(path_lengths),
            "average_path": sum(path_lengths) / len(path_lengths),
            "distribution": distribution
        }