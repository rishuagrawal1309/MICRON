from backend.app.core.graph import BOMGraph


class BOMTraversal:

    def __init__(self, graph):
        self.graph = graph

    # ---------------------------------------------------------
    # 1. Get complete BOM tree
    # ---------------------------------------------------------
    def get_bom_tree(self, material):

        visited = set()

        def dfs(node):

            # Cycle protection
            if node in visited:
                return {
                    "material": node,
                    "cycle": True,
                    "children": []
                }

            visited.add(node)

            children = self.graph.get_children(node)

            result = {
                "material": node,
                "cycle": False,
                "children": []
            }

            for child in children:
                result["children"].append(dfs(child))

            visited.remove(node)

            return result

        return dfs(material)

    # ---------------------------------------------------------
    # 2. Forward lineage
    # ---------------------------------------------------------
    def forward_lineage(self, material):

        visited = set()
        result = []

        def dfs(node):

            if node in visited:
                return

            visited.add(node)

            result.append(node)

            for child in self.graph.get_children(node):
                dfs(child)

        dfs(material)

        return result

    # ---------------------------------------------------------
    # 3. Reverse lineage
    # ---------------------------------------------------------
    def reverse_lineage(self, material):

        visited = set()
        result = []

        def dfs(node):

            if node in visited:
                return

            visited.add(node)

            result.append(node)

            for parent in self.graph.get_parents(node):
                dfs(parent)

        dfs(material)

        return result


if __name__ == "__main__":

    graph = BOMGraph()
    graph.build_graph()

    traversal = BOMTraversal(graph)

    # Pick a material from your dataset
    material = next(iter(graph.forward_graph))

    print("\n================================")
    print("MATERIAL:", material)
    print("================================")

    print("\nFORWARD LINEAGE:")
    print(traversal.forward_lineage(material))

    print("\nREVERSE LINEAGE:")
    print(traversal.reverse_lineage(material))

    print("\nBOM TREE:")
    print(traversal.get_bom_tree(material))