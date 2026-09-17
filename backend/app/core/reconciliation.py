class BOMReconciler:

    FLAT_COLUMNS = [
        "FPN",
        "PKGD",
        "TSTD",
        "ASMBLD",
        "MODULE",
        "CHIP",
        "DIE",
        "WAFER",
        "FAB_OUT",
        "RAW"
    ]

    def __init__(self, graph, flattener):
        self.graph = graph
        self.flattener = flattener

    def normalize_record(self, record):
        """
        Convert a BOM_FLAT record into a tuple
        so two records can be compared.
        """

        return tuple(
            record.get(column)
            for column in self.FLAT_COLUMNS
        )

    def get_reconstructed_records(self):
        """
        Reconstruct BOM_FLAT from BOM_SINGLE_LEVEL.
        """

        return self.flattener.reconstruct_all()

    def get_flat_records(self):
        """
        Load the existing BOM_FLAT records from SQLite.
        """

        from backend.app.db.database import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                FPN,
                PKGD,
                TSTD,
                ASMBLD,
                MODULE,
                CHIP,
                DIE,
                WAFER,
                FAB_OUT,
                RAW
            FROM bom_flat
        """)

        rows = cursor.fetchall()

        conn.close()

        records = []

        for row in rows:

            records.append({
                "FPN": row["FPN"],
                "PKGD": row["PKGD"],
                "TSTD": row["TSTD"],
                "ASMBLD": row["ASMBLD"],
                "MODULE": row["MODULE"],
                "CHIP": row["CHIP"],
                "DIE": row["DIE"],
                "WAFER": row["WAFER"],
                "FAB_OUT": row["FAB_OUT"],
                "RAW": row["RAW"]
            })

        return records
    
    def reconcile(self):
        """
        Compare reconstructed BOM paths against BOM_FLAT.
        """

        reconstructed = self.get_reconstructed_records()
        provided = self.get_flat_records()

        reconstructed_map = {
        self.normalize_record(record): record
        for record in reconstructed
        }

        provided_map = {
        self.normalize_record(record): record
        for record in provided
        }

        results = []

        # -------------------------------------------------
        # Material mismatches
        # -------------------------------------------------

        results.extend(
        self.find_material_mismatches(
            reconstructed,
            provided
        )
        )

        # -------------------------------------------------
        # Phantom entries
        # -------------------------------------------------

        results.extend(
        self.find_phantom_entries(provided)
         )

        # -------------------------------------------------
         # Present in BOM_FLAT but not reconstructed
        # -------------------------------------------------

        for key, record in provided_map.items():

            if key not in reconstructed_map:

                results.append({
                "type": "FLAT_ONLY",
                "record": record
            })

        # -------------------------------------------------
        # Present in reconstruction but not BOM_FLAT
        # -------------------------------------------------

        for key, record in reconstructed_map.items():

            if key not in provided_map:

                results.append({
                "type": "RECONSTRUCTION_ONLY",
                "record": record
            })

        return results
    
    def find_material_mismatches(self, reconstructed, provided):
        """
        Find BOM paths where the same FPN and structural position
        exist, but one or more material values differ.
        """

        mismatches = []

        reconstructed_groups = {}
        provided_groups = {}

    # -------------------------------------------------
    # Group reconstructed records by FPN
    # -------------------------------------------------

        for record in reconstructed:

            fpn = record.get("FPN")

            reconstructed_groups.setdefault(
            fpn,
            []
        ).append(record)

        # -------------------------------------------------
        # Group provided records by FPN
        # -------------------------------------------------

        for record in provided:

            fpn = record.get("FPN")

            provided_groups.setdefault(
            fpn,
            []
            ).append(record)

    # -------------------------------------------------
    # Compare records belonging to the same FPN
    # -------------------------------------------------

        for fpn in reconstructed_groups:

            if fpn not in provided_groups:
                continue

        reconstructed_records = reconstructed_groups[fpn]
        provided_records = provided_groups[fpn]

        count = min(
            len(reconstructed_records),
            len(provided_records)
        )

        for i in range(count):

            recon = reconstructed_records[i]
            flat = provided_records[i]

            differences = {}

            for column in self.FLAT_COLUMNS:

                recon_value = recon.get(column)
                flat_value = flat.get(column)

                if recon_value != flat_value:

                    differences[column] = {
                        "reconstructed": recon_value,
                        "provided": flat_value
                    }

            if differences:

                mismatches.append({
                    "type": "MATERIAL_MISMATCH",
                    "fpn": fpn,
                    "differences": differences,
                    "reconstructed": recon,
                    "provided": flat
                })

        return mismatches
    
    def get_path_signature(self, record):
        """
        Create a signature for identifying the structural
        position of a BOM path.

        We exclude the actual material values for now and
        use the stage sequence.
        """

        return (
            record.get("FPN"),
            record.get("PKGD"),
            record.get("TSTD"),
            record.get("ASMBLD"),
            record.get("MODULE"),
        )
    
    def find_phantom_entries(self, provided):
        """
        Find materials that appear in BOM_FLAT but do not exist
        anywhere in BOM_SINGLE_LEVEL.
        """

        from backend.app.db.database import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT HDR_MATERIAL
            FROM bom_single_level

            UNION

            SELECT COMP_MATERIAL
            FROM bom_single_level
        """)

        rows = cursor.fetchall()

        conn.close()

        known_materials = {
            row["HDR_MATERIAL"]
            for row in rows
            if row["HDR_MATERIAL"]
        }

        phantom_entries = []

        for record in provided:

            for column in self.FLAT_COLUMNS:

                material = record.get(column)

                if material and material not in known_materials:

                    phantom_entries.append({
                        "type": "PHANTOM_ENTRY",
                        "fpn": record.get("FPN"),
                        "column": column,
                        "material": material
                    })

        return phantom_entries