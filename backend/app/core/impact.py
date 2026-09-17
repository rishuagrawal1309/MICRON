class BOMImpact:

    def __init__(self, graph):
        self.graph = graph

    def shortage_impact(self, material):

        affected = []

        def dfs(node, quantity, path, visited):

            if node in visited:
                return

            visited.add(node)

            parents = self.graph.get_parents(node)

            # Reached a top-level material
            if not parents:
                affected.append({
                    "fpn": node,
                    "quantity_impact": quantity,
                    "path": path
                })
                return

            for parent in parents:

                edge = self.graph.edge_data.get(
                    (parent, node),
                    {}
                )

                comp_qty = edge.get("COMP_QTY", 1)

                dfs(
                    parent,
                    quantity * comp_qty,
                    [parent] + path,
                    visited.copy()
                )

        dfs(
            material,
            1,
            [material],
            set()
        )

        return affected