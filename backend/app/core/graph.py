from collections import defaultdict

from backend.app.db.database import get_connection


class BOMGraph:

    def __init__(self):
        self.forward_graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)

    def build_graph(self):
        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                HDR_MATERIAL,
                COMP_MATERIAL
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

            if not parent or not child:
                continue

            self.forward_graph[parent].append(child)
            self.reverse_graph[child].append(parent)

        return self.forward_graph, self.reverse_graph

    def get_children(self, material):
        return self.forward_graph.get(material, [])

    def get_parents(self, material):
        return self.reverse_graph.get(material, [])

if __name__ == "__main__":

    graph = BOMGraph()

    forward, reverse = graph.build_graph()

    print("\n=== FORWARD GRAPH ===")

    for parent, children in list(forward.items())[:10]:
        print(parent, "->", children)

    print("\n=== REVERSE GRAPH ===")

    for child, parents in list(reverse.items())[:10]:
        print(child, "<-", parents)