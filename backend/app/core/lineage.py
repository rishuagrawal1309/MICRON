class BOMLineage:

    def __init__(self, graph):
        self.graph = graph

    # ---------------------------------------------------------
    # Forward Lineage
    # ---------------------------------------------------------
    def forward_lineage(self, material):

        results = []

        def dfs(node, quantity, path, visited):

            if node in visited:
                return

            visited.add(node)

            children = self.graph.get_children(node)

            # Reached a leaf
            if not children:
                results.append({
                    "material": node,
                    "quantity": quantity,
                    "path": path
                })
                return

            for child in children:

                edge = self.graph.edge_data.get(
                    (node, child),
                    {}
                )

                comp_qty = edge.get("COMP_QTY", 1)

                dfs(
                    child,
                    quantity * comp_qty,
                    path + [child],
                    visited.copy()
                )

        dfs(
            material,
            1,
            [material],
            set()
        )

        return results

    # ---------------------------------------------------------
    # Reverse Lineage
    # ---------------------------------------------------------
    def reverse_lineage(self, material):

        results = []

        def dfs(node, path, visited):

            if node in visited:
                return

            visited.add(node)

            parents = self.graph.get_parents(node)

            for parent in parents:

                results.append({
                    "material": parent,
                    "child": node,
                    "path": [parent] + path
                })

                dfs(
                    parent,
                    [parent] + path,
                    visited.copy()
                )

        dfs(
            material,
            [material],
            set()
        )

        return results