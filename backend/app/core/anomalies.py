from backend.app.core.graph import BOMGraph
from backend.app.db.database import get_connection

STAGE_ORDER = {
    "RAW": 0,
    "FAB_OUT": 1,
    "WAFER": 2,
    "DIE": 3,
    "CHIP": 4,
    "MODULE": 5,
    "ASMBLD": 6,
    "TSTD": 7,
    "PKGD": 8,
    "FPN": 9
}

class BOMAnomalyDetector:

    def __init__(self, graph):
        self.graph = graph

    # ---------------------------------------------------------
    # 1. Detect circular references
    # ---------------------------------------------------------
    def detect_cycles(self):

        visited = set()
        recursion_stack = set()
        cycles = []

        def dfs(node, path):

            visited.add(node)
            recursion_stack.add(node)
            path.append(node)

            for child in self.graph.get_children(node):

                # Case 1: Cycle found
                if child in recursion_stack:

                    cycle_start = path.index(child)

                    cycle_path = path[cycle_start:] + [child]

                    cycles.append({
                        "type": "CYCLE",
                        "severity": "CRITICAL",
                        "material": child,
                        "path": cycle_path,
                        "description": "Circular dependency detected"
                    })

                # Case 2: Continue DFS
                elif child not in visited:

                    dfs(child, path)

            path.pop()
            recursion_stack.remove(node)

        # Run DFS from every node
        all_nodes = set(self.graph.forward_graph.keys())

        for children in self.graph.forward_graph.values():
            all_nodes.update(children)

        for node in all_nodes:

            if node not in visited:
                dfs(node, [])

        return cycles
    
        # ---------------------------------------------------------
    # 2. Detect orphan / dangling components
    # ---------------------------------------------------------
    def detect_orphans(self):

        anomalies = []

        # Materials that appear as parents
        header_materials = set(self.graph.forward_graph.keys())

        # Materials that appear as children
        child_materials = set()

        for children in self.graph.forward_graph.values():
            child_materials.update(children)

        # A valid RAW material can be a leaf
        # We will determine RAW status from the database.
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COMP_MATERIAL,
                COMP_MATL_GROUP
            FROM bom_single_level
        """)

        rows = cursor.fetchall()

        conn.close()

        raw_materials = set()

        for row in rows:
            material = row["COMP_MATERIAL"]
            material_group = row["COMP_MATL_GROUP"]

            if material and material_group == "RAW":
                raw_materials.add(material)

        # Child but neither a header nor a RAW material
        orphan_materials = (
            child_materials
            - header_materials
            - raw_materials
        )

        for material in sorted(orphan_materials):

            parents = []

            for parent, children in self.graph.forward_graph.items():

                if material in children:
                    parents.append(parent)

            anomalies.append({
                "type": "ORPHAN",
                "severity": "WARNING",
                "material": material,
                "parents": parents,
                "description": (
                    "Component appears as a child but is not "
                    "defined as a header material or valid RAW leaf"
                )
            })

        return anomalies
    
        # ---------------------------------------------------------
    # 3. Detect incomplete manufacturing legs
    # ---------------------------------------------------------
    def detect_incomplete_legs(self):

        anomalies = []

        # Find FPNs from the graph
        fpns = [
            material
            for material in self.graph.forward_graph.keys()
            if material.startswith("FPN-")
        ]

        for fpn in fpns:

            # Traverse every path starting from the FPN
            def dfs(node, path):

                children = self.graph.get_children(node)

                # Leaf node
                if not children:

                    # A valid manufacturing path should terminate
                    # at a RAW material.
                    if not node.startswith("RAW-"):

                        anomalies.append({
                            "type": "INCOMPLETE",
                            "severity": "WARNING",
                            "material": fpn,
                            "path": path.copy(),
                            "break_point": node,
                            "description": (
                                "Manufacturing path terminates before "
                                "reaching a valid RAW material"
                            )
                        })

                    return

                for child in children:

                    # Protect against cycles
                    if child in path:
                        continue

                    dfs(child, path + [child])

            dfs(fpn, [fpn])

        return anomalies
    
        # ---------------------------------------------------------
    # 4. Detect stage progression violations
    # ---------------------------------------------------------
    def detect_stage_violations(self):

        anomalies = []

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                HDR_MATERIAL,
                HDR_MATL_GROUP,
                COMP_MATERIAL,
                COMP_MATL_GROUP,
                PLANT
            FROM bom_single_level
            WHERE DEL_FLAG IS NULL
               OR DEL_FLAG = ''
               OR DEL_FLAG = '0'
        """)

        rows = cursor.fetchall()

        conn.close()

        for row in rows:

            parent = row["HDR_MATERIAL"]
            parent_stage = row["HDR_MATL_GROUP"]

            child = row["COMP_MATERIAL"]
            child_stage = row["COMP_MATL_GROUP"]

            plant = row["PLANT"]

            # Ignore rows with missing stage information
            if not parent_stage or not child_stage:
                continue

            # Ignore unknown stages
            if parent_stage not in STAGE_ORDER:
                continue

            if child_stage not in STAGE_ORDER:
                continue

            parent_order = STAGE_ORDER[parent_stage]
            child_order = STAGE_ORDER[child_stage]

            # Parent should normally be later in the
            # manufacturing process than its child.
            if child_order >= parent_order:
                continue

            anomalies.append({
                "type": "STAGE_VIOLATION",
                "severity": "CRITICAL",
                "material": parent,
                "plant": plant,
                "parent_stage": parent_stage,
                "child": child,
                "child_stage": child_stage,
                "path": [parent, child],
                "description": (
                    f"Invalid stage progression: "
                    f"{parent_stage} -> {child_stage}"
                )
            })

        return anomalies
    
        # ---------------------------------------------------------
    # 5. Detect expired-but-active BOM entries
    # ---------------------------------------------------------
    def detect_expired_active(self):

        anomalies = []

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                HDR_MATERIAL,
                COMP_MATERIAL,
                HDR_MATL_GROUP,
                COMP_MATL_GROUP,
                COMP_QTY,
                PLANT,
                BOM_ALT,
                BOM_STATUS,
                VALID_FROM,
                VALID_TO,
                ITEM_NO
            FROM bom_single_level
            WHERE BOM_STATUS = '01'
              AND VALID_TO IS NOT NULL
              AND VALID_TO != ''
        """)

        rows = cursor.fetchall()

        conn.close()

        from datetime import date, datetime

        today = date.today()

        for row in rows:

            valid_to = row["VALID_TO"]

            # Try to convert database date into a date object
            try:

                if isinstance(valid_to, str):

                    valid_to = valid_to.strip()

                    # Handle YYYY-MM-DD
                    valid_to = datetime.strptime(
                        valid_to,
                        "%Y-%m-%d"
                    ).date()

                elif isinstance(valid_to, datetime):

                    valid_to = valid_to.date()

            except ValueError:
                # Ignore malformed dates for this anomaly
                continue

            # Check if active record has expired
            if valid_to < today:

                anomalies.append({
                    "type": "EXPIRED_ACTIVE",
                    "severity": "WARNING",
                    "material": row["HDR_MATERIAL"],
                    "component": row["COMP_MATERIAL"],
                    "plant": row["PLANT"],
                    "bom_alt": row["BOM_ALT"],
                    "bom_status": row["BOM_STATUS"],
                    "valid_from": row["VALID_FROM"],
                    "valid_to": row["VALID_TO"],
                    "item_no": row["ITEM_NO"],
                    "description": (
                        "BOM entry is marked active but "
                        "its validity period has expired"
                    )
                })

        return anomalies
    
        # ---------------------------------------------------------
    # Run all anomaly checks
    # ---------------------------------------------------------
    def detect_all_anomalies(self):

        all_anomalies = []

        all_anomalies.extend(self.detect_cycles())
        all_anomalies.extend(self.detect_orphans())
        all_anomalies.extend(self.detect_incomplete_legs())
        all_anomalies.extend(self.detect_stage_violations())
        all_anomalies.extend(self.detect_expired_active())

        return all_anomalies


if __name__ == "__main__":

    graph = BOMGraph()
    graph.build_graph()

    detector = BOMAnomalyDetector(graph)

    anomalies = detector.detect_all_anomalies()

    print("\n================================")
    print("BOM ANOMALY SUMMARY")
    print("================================")

    print("Total anomalies:", len(anomalies))

    for anomaly in anomalies:

        print(
            anomaly["type"],
            "|",
            anomaly["severity"],
            "|",
            anomaly.get("material")
        )

# -------------------------------------------------------------
# TEST
# -------------------------------------------------------------

# if __name__ == "__main__":

#     graph = BOMGraph()
#     graph.build_graph()

#     detector = BOMAnomalyDetector(graph)

#     cycles = detector.detect_cycles()

#     print("\n================================")
#     print("CYCLE DETECTION")
#     print("================================")

#     if not cycles:
#         print("No cycles detected.")

#     else:

#         print(f"Cycles found: {len(cycles)}")

#         for cycle in cycles:

#             print("\nType:", cycle["type"])
#             print("Severity:", cycle["severity"])
#             print("Material:", cycle["material"])
#             print("Path:", " -> ".join(cycle["path"]))
#             print("Description:", cycle["description"])

        
#     orphans = detector.detect_orphans()

#     print("\n================================")
#     print("ORPHAN DETECTION")
#     print("================================")

#     if not orphans:
#         print("No orphan components detected.")

#     else:

#         print(f"Orphans found: {len(orphans)}")

#         for anomaly in orphans:

#             print("\nType:", anomaly["type"])
#             print("Severity:", anomaly["severity"])
#             print("Material:", anomaly["material"])
#             print("Parents:", anomaly["parents"])
#             print("Description:", anomaly["description"])

#     incomplete = detector.detect_incomplete_legs()

#     print("\n================================")
#     print("INCOMPLETE MANUFACTURING LEGS")
#     print("================================")

#     if not incomplete:
#         print("No incomplete manufacturing legs detected.")

#     else:

#         print(f"Incomplete legs found: {len(incomplete)}")

#         for anomaly in incomplete:

#             print("\nType:", anomaly["type"])
#             print("Severity:", anomaly["severity"])
#             print("FPN:", anomaly["material"])
#             print("Break point:", anomaly["break_point"])
#             print("Path:", " -> ".join(anomaly["path"]))
#             print("Description:", anomaly["description"])

#     stage_violations = detector.detect_stage_violations()

#     print("\n================================")
#     print("STAGE PROGRESSION VIOLATIONS")
#     print("================================")

#     if not stage_violations:
#         print("No stage violations detected.")

#     else:

#         print(
#             f"Stage violations found: "
#             f"{len(stage_violations)}"
#         )

#         for anomaly in stage_violations:

#             print("\nType:", anomaly["type"])
#             print("Severity:", anomaly["severity"])
#             print("Parent:", anomaly["material"])
#             print("Parent stage:", anomaly["parent_stage"])
#             print("Child:", anomaly["child"])
#             print("Child stage:", anomaly["child_stage"])
#             print("Plant:", anomaly["plant"])
#             print("Path:", " -> ".join(anomaly["path"]))
#             print("Description:", anomaly["description"])

#     expired = detector.detect_expired_active()

#     print("\n================================")
#     print("EXPIRED-BUT-ACTIVE ENTRIES")
#     print("================================")

#     if not expired:

#         print("No expired-but-active entries detected.")

#     else:

#         print(
#             f"Expired-but-active entries found: "
#             f"{len(expired)}"
#         )

#         for anomaly in expired:

#             print("\nType:", anomaly["type"])
#             print("Severity:", anomaly["severity"])
#             print("Material:", anomaly["material"])
#             print("Component:", anomaly["component"])
#             print("Plant:", anomaly["plant"])
#             print("BOM Alternative:", anomaly["bom_alt"])
#             print("Status:", anomaly["bom_status"])
#             print("Valid From:", anomaly["valid_from"])
#             print("Valid To:", anomaly["valid_to"])
#             print("Description:", anomaly["description"])

# if __name__ == "__main__":

#     graph = BOMGraph()

#     # Artificial cycle for testing
#     graph.forward_graph["ASM-001"] = ["MOD-001"]
#     graph.forward_graph["MOD-001"] = ["CHIP-001"]
#     graph.forward_graph["CHIP-001"] = ["ASM-001"]

#     detector = BOMAnomalyDetector(graph)

#     cycles = detector.detect_cycles()

#     print("\n================================")
#     print("CYCLE DETECTION")
#     print("================================")

#     for cycle in cycles:

#         print("\nType:", cycle["type"])
#         print("Severity:", cycle["severity"])
#         print("Path:", " -> ".join(cycle["path"]))