class BOMAlternatives:

    def __init__(self, graph):
        self.graph = graph

    def find_alternative_paths(self, material):

        alternatives = []

        parents = self.graph.get_parents(material)

        for parent in parents:

            current_edge = self.graph.edge_data.get(
                (parent, material),
                {}
            )

            current_alt = current_edge.get("BOM_ALT")

            # Look at other children of the same parent
            for child in self.graph.get_children(parent):

                if child == material:
                    continue

                edge = self.graph.edge_data.get(
                    (parent, child),
                    {}
                )

                alt = edge.get("BOM_ALT")

                if alt != current_alt:
                    alternatives.append({
                        "parent": parent,
                        "original_material": material,
                        "alternative_material": child,
                        "bom_alt": alt,
                        "plant": edge.get("PLANT")
                    })

        return alternatives