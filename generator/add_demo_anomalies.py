"""Load realistic, repeatable BOM examples for three anomaly categories."""

from datetime import date, timedelta

from backend.app.db.database import get_connection


DEMO_FPNS = ("FPN-0021", "FPN-0022", "FPN-0023")
DEMO_MATERIALS = (
    "FPN-0021", "PKGD-0021", "TSTD-0021", "ASMBLD-0021",
    "MODULE-0021-A", "CHIP-0021-01", "DIE-2101", "WAFER-2101", "FAB-2101",
    "FPN-0022", "PKGD-0022", "TSTD-0022", "ASMBLD-0022",
    "MODULE-0022-A", "CHIP-0022-01", "DIE-2201", "WAFER-2201", "FAB-2201",
    "DIE-2299", "WAFER-2299", "FAB-2299",
    "FPN-0023", "PKGD-0023", "TSTD-0023", "ASMBLD-0023",
    "MODULE-0023-A", "CHIP-0023-01", "DIE-2301", "WAFER-2301", "FAB-2301",
)


def standard_chain(number, process_id):
    suffix = f"{number:04d}"
    return [
        (f"FPN-{suffix}", "FPN", f"PKGD-{suffix}", "PKGD"),
        (f"PKGD-{suffix}", "PKGD", f"TSTD-{suffix}", "TSTD"),
        (f"TSTD-{suffix}", "TSTD", f"ASMBLD-{suffix}", "ASMBLD"),
        (f"ASMBLD-{suffix}", "ASMBLD", f"MODULE-{suffix}-A", "MODULE"),
        (f"MODULE-{suffix}-A", "MODULE", f"CHIP-{suffix}-01", "CHIP"),
        (f"CHIP-{suffix}-01", "CHIP", f"DIE-{process_id}", "DIE"),
        (f"DIE-{process_id}", "DIE", f"WAFER-{process_id}", "WAFER"),
        (f"WAFER-{process_id}", "WAFER", f"FAB-{process_id}", "FAB_OUT"),
        (f"FAB-{process_id}", "FAB_OUT", f"RAW-{process_id}", "RAW"),
    ]


def add_demo_anomalies():
    today = date.today()
    future_date = (today + timedelta(days=365)).isoformat()
    past_date = (today - timedelta(days=365)).isoformat()

    # FPN-0021: cycle-only scenario.
    cycle_chain = standard_chain(21, "2101") + [
        ("FAB-2101", "FAB_OUT", "DIE-2101", "DIE"),
    ]

    # FPN-0022: stage-violation-only scenario with a non-cyclic DIE branch.
    stage_chain = standard_chain(22, "2201") + [
        ("FAB-2201", "FAB_OUT", "DIE-2299", "DIE"),
        ("DIE-2299", "DIE", "WAFER-2299", "WAFER"),
        ("WAFER-2299", "WAFER", "FAB-2299", "FAB_OUT"),
        ("FAB-2299", "FAB_OUT", "RAW-2299", "RAW"),
    ]

    # FPN-0023: expired-active-only scenario.
    expired_chain = standard_chain(23, "2301")

    rows = []
    for item_number, relation in enumerate(cycle_chain + stage_chain + expired_chain, 1):
        parent, parent_stage, child, child_stage = relation
        is_expired_active = parent == "PKGD-0023" and child == "TSTD-0023"
        rows.append((
            parent, parent_stage, child, child_stage,
            1, 1, "PLT03", "01", "01", "1", str(item_number * 10),
            (today - timedelta(days=730)).isoformat() if is_expired_active else today.isoformat(),
            past_date if is_expired_active else future_date,
            None,
        ))

    flat_rows = [
        ("FPN-0021", "PKGD-0021", "TSTD-0021", "ASMBLD-0021", None,
         "CHIP-0021-01", "DIE-2101", "WAFER-2101", None, "RAW-2101"),
        ("FPN-0022", "PKGD-0022", "TSTD-0022", "ASMBLD-0022", None,
         "CHIP-0022-01", "DIE-2201", "WAFER-2201", None, "RAW-2201"),
        ("FPN-0022", "PKGD-0022", "TSTD-0022", "ASMBLD-0022", None,
         "CHIP-0022-01", "DIE-2299", "WAFER-2299", None, "RAW-2299"),
        ("FPN-0023", "PKGD-0023", "TSTD-0023", "ASMBLD-0023", None,
         "CHIP-0023-01", "DIE-2301", "WAFER-2301", None, "RAW-2301"),
    ]

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM bom_single_level WHERE BOM_ALT = 'DEMO' AND PLANT = 'PLT_DEMO'"
        )
        placeholders = ", ".join("?" for _ in DEMO_MATERIALS)
        cursor.execute(
            f"DELETE FROM bom_single_level WHERE HDR_MATERIAL IN ({placeholders})",
            DEMO_MATERIALS,
        )
        cursor.executemany(
            """
            INSERT INTO bom_single_level (
                HDR_MATERIAL, HDR_MATL_GROUP, COMP_MATERIAL, COMP_MATL_GROUP,
                COMP_QTY, HEADER_QTY, PLANT, BOM_ALT, BOM_STATUS, BOM_USG,
                ITEM_NO, VALID_FROM, VALID_TO, DEL_FLAG
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        flat_placeholders = ", ".join("?" for _ in DEMO_FPNS)
        cursor.execute(
            f"DELETE FROM bom_flat WHERE FPN IN ({flat_placeholders})",
            DEMO_FPNS,
        )
        cursor.executemany(
            """
            INSERT INTO bom_flat (
                FPN, PKGD, TSTD, ASMBLD, MODULE, CHIP, DIE, WAFER, FAB_OUT, RAW
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            flat_rows,
        )
        connection.commit()
    finally:
        connection.close()

    print(f"Loaded {len(rows)} BOM rows across {len(DEMO_FPNS)} anomaly scenarios.")


if __name__ == "__main__":
    add_demo_anomalies()
