from collections import defaultdict
from platform import node

from backend.app.db.database import get_connection


class BOMGraph:

    def __init__(self):
        self.forward_graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
        self.edge_data = {}

    def build_graph(self):
        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
            HDR_MATERIAL,
        HDR_MATL_GROUP,
        COMP_MATERIAL,
        COMP_MATL_GROUP,
        COMP_QTY,
        HEADER_QTY,
        PLANT,
        BOM_ALT,
        BOM_STATUS,
        VALID_FROM,
        VALID_TO
    FROM bom_single_level
    WHERE DEL_FLAG IS NULL
       OR DEL_FLAG = ''
       OR DEL_FLAG = '0'
    """)

        rows = cursor.fetchall()

        conn.close()

        for row in rows:
            parent = row["HDR_MATERIAL"]
            child = row["COMP_MATERIAL"]
            self.edge_data[(parent, child)] = {
    "HDR_MATL_GROUP": row["HDR_MATL_GROUP"],
    "COMP_MATL_GROUP": row["COMP_MATL_GROUP"],
    "COMP_QTY": row["COMP_QTY"],
    "HEADER_QTY": row["HEADER_QTY"],
    "PLANT": row["PLANT"],
    "BOM_ALT": row["BOM_ALT"],
    "BOM_STATUS": row["BOM_STATUS"],
    "VALID_FROM": row["VALID_FROM"],
    "VALID_TO": row["VALID_TO"],
}

            if not parent or not child:
                continue

            self.forward_graph[parent].append(child)
            self.reverse_graph[child].append(parent)

        return self.forward_graph, self.reverse_graph

    def get_children(self, material):
        return self.forward_graph.get(material, [])

    def get_parents(self, material):
        return self.reverse_graph.get(material, [])


    def get_all_parents(self, material):
        """
        Return all ancestors of a material:
        direct parent, grandparent, great-grandparent, etc.
        """

        ancestors = []
        visited = set()

        def dfs(node):

         if node in visited:
            return

         visited.add(node)

         parents = self.get_parents(node)

         for parent in parents:
            if parent not in ancestors:
                ancestors.append(parent)

            dfs(parent)

        dfs(material)

        return ancestors


    def get_edge_data(self, parent, child):
        return self.edge_data.get((parent, child), {})

if __name__ == "__main__":

    graph = BOMGraph()

    forward, reverse = graph.build_graph()

    print("\n=== FORWARD GRAPH ===")

    for parent, children in list(forward.items())[:10]:
        print(parent, "->", children)

    print("\n=== REVERSE GRAPH ===")

    for child, parents in list(reverse.items())[:10]:
        print(child, "<-", parents)