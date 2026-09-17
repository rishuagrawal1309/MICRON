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
        Convert a BOM_FLAT record into a comparable tuple.
        """

        return tuple(
            record.get(column)
            for column in self.FLAT_COLUMNS
        )

    def get_reconstructed_records(self):
        """
        Generate BOM_FLAT records from BOM_SINGLE_LEVEL.
        """

        return self.flattener.reconstruct_all()

    def get_flat_records(self):
        """
        Load existing BOM_FLAT records from SQLite.
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
                MOD_A,
                MOD_B,
                MOD_C,
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

                # For now we preserve the three module columns
                "MOD_A": row["MOD_A"],
                "MOD_B": row["MOD_B"],
                "MOD_C": row["MOD_C"],

                "CHIP": row["CHIP"],
                "DIE": row["DIE"],
                "WAFER": row["WAFER"],
                "FAB_OUT": row["FAB_OUT"],
                "RAW": row["RAW"]
            })

        return records