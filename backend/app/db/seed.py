import pandas as pd

from database import get_connection


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bom_single_level (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            HDR_MATERIAL TEXT,
            HDR_MATL_GROUP TEXT,
            COMP_MATERIAL TEXT,
            COMP_MATL_GROUP TEXT,
            COMP_QTY REAL,
            HEADER_QTY REAL,
            PLANT TEXT,
            BOM_ALT TEXT,
            BOM_STATUS TEXT,
            BOM_USG TEXT,
            ITEM_NO TEXT,
            VALID_FROM TEXT,
            VALID_TO TEXT,
            DEL_FLAG TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bom_flat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            FPN TEXT,
            PKGD TEXT,
            TSTD TEXT,
            ASMBLD TEXT,
            MODULE TEXT,
            CHIP TEXT,
            DIE TEXT,
            WAFER TEXT,
            FAB_OUT TEXT,
            RAW TEXT
        )
    """)

    conn.commit()


def load_data(conn):
    single_level = pd.read_csv("data/bom_single_level.csv")
    flat = pd.read_csv("data/bom_flat.csv")

    single_level.to_sql(
        "bom_single_level",
        conn,
        if_exists="append",
        index=False
    )

    flat.to_sql(
        "bom_flat",
        conn,
        if_exists="append",
        index=False
    )


def main():
    conn = get_connection()

    create_tables(conn)
    load_data(conn)

    conn.close()

    print("Database created successfully.")
    print("BOM data loaded successfully.")


if __name__ == "__main__":
    main()