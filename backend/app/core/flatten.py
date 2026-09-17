class BOMFlattener:

    def __init__(self, graph):
        self.graph = graph

    def flatten_bom(self, fpn):
        """
        Reconstruct all paths starting from an FPN.

        Returns:
            List of dictionaries containing:
            - path
            - status
        """

        results = []

        def dfs(node, path):

            # -------------------------------------------------
            # Cycle protection
            # -------------------------------------------------
            if node in path:
                results.append({
                    "path": path + [node],
                    "status": "CYCLE"
                })
                return

            current_path = path + [node]

            # -------------------------------------------------
            # Get children
            # -------------------------------------------------
            children = self.graph.get_children(node)

            # -------------------------------------------------
            # Leaf node
            # -------------------------------------------------
            if not children:
                results.append({
                    "path": current_path,
                    "status": "COMPLETE"
                })
                return

            # -------------------------------------------------
            # Traverse every child
            # -------------------------------------------------
            for child in children:
                dfs(child, current_path)

        dfs(fpn, [])

        return results

    def path_to_flat_record(self, path):
        """
        Convert a reconstructed path into BOM_FLAT format.
        """

        record = {
            "FPN": None,
            "PKGD": None,
            "TSTD": None,
            "ASMBLD": None,
            "MODULE": None,
            "CHIP": None,
            "DIE": None,
            "WAFER": None,
            "FAB_OUT": None,
            "RAW": None
        }

        for material in path:

            if material.startswith("FPN-"):
                record["FPN"] = material

            elif material.startswith("PKGD-"):
                record["PKGD"] = material

            elif material.startswith("TSTD-"):
                record["TSTD"] = material

            elif material.startswith("ASMBLD-"):
                record["ASMBLD"] = material

            elif material.startswith("MOD-"):
                record["MODULE"] = material

            elif material.startswith("CHIP-"):
                record["CHIP"] = material

            elif material.startswith("DIE-"):
                record["DIE"] = material

            elif material.startswith("WAFER-"):
                record["WAFER"] = material

            elif material.startswith("FAB_OUT-"):
                record["FAB_OUT"] = material

            elif material.startswith("RAW-"):
                record["RAW"] = material

        return record
    
    def reconstruct_all(self):
        """
        Reconstruct BOM_FLAT records for all FPNs in the graph.
        """

        reconstructed = []

        # FPNs are the root materials that start with FPN-
        fpns = [
            material
            for material in self.graph.forward_graph
            if material.startswith("FPN-")
        ]

        for fpn in fpns:

            paths = self.flatten_bom(fpn)

            for result in paths:

                # Ignore cyclic paths for BOM_FLAT reconstruction
                if result["status"] != "COMPLETE":
                    continue

                record = self.path_to_flat_record(
                    result["path"]
                )

                reconstructed.append(record)

        return reconstructed