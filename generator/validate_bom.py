import pandas as pd


def validate_bom(df):

    print("\n========== BOM VALIDATION ==========\n")

    # ---------------------------------------
    # Rule 1: Every CHIP has exactly 1 child
    # ---------------------------------------

    chip_rows = df[
        df["HDR_MATL_GROUP"] == "CHIP"
    ]

    chip_child_count = (
        chip_rows
        .groupby("HDR_MATERIAL")
        .size()
    )

    invalid_chips = chip_child_count[
        chip_child_count != 1
    ]

    if len(invalid_chips) == 0:
        print("✓ Every CHIP has exactly one descendant.")
    else:
        print("✗ Invalid CHIP descendants:")
        print(invalid_chips)

    # ---------------------------------------
    # Rule 2: ASMBLD has max 3 modules
    # ---------------------------------------

    asmbld_rows = df[
        (df["HDR_MATL_GROUP"] == "ASMBLD")
        &
        (df["COMP_MATL_GROUP"] == "MODULE")
    ]

    module_counts = (
        asmbld_rows
        .groupby("HDR_MATERIAL")
        .size()
    )

    invalid_asmbld = module_counts[
        module_counts > 3
    ]

    if len(invalid_asmbld) == 0:
        print("✓ ASMBLD has at most 3 modules.")
    else:
        print("✗ ASMBLD has more than 3 modules:")
        print(invalid_asmbld)

    # ---------------------------------------
    # Rule 3: Every MODULE has >= 1 CHIP
    # ---------------------------------------

    module_rows = df[
        df["HDR_MATL_GROUP"] == "MODULE"
    ]

    module_chip_counts = (
        module_rows
        .groupby("HDR_MATERIAL")
        .size()
    )

    invalid_modules = module_chip_counts[
        module_chip_counts < 1
    ]

    if len(invalid_modules) == 0:
        print("✓ Every MODULE has at least one CHIP.")
    else:
        print("✗ MODULE without CHIP:")
        print(invalid_modules)

    # ---------------------------------------
    # Rule 4: RAW must be a leaf
    # ---------------------------------------

    raw_as_parent = df[
        df["HDR_MATL_GROUP"] == "RAW"
    ]

    if len(raw_as_parent) == 0:
        print("✓ RAW materials are leaves.")
    else:
        print("✗ RAW materials have descendants!")

    # ---------------------------------------
    # Rule 5: Shared chips
    # ---------------------------------------

    chip_usage = (
        df[df["COMP_MATL_GROUP"] == "CHIP"]
        .groupby("COMP_MATERIAL")
        .size()
    )

    shared_chips = chip_usage[
        chip_usage > 1
    ]

    print(
        f"\nShared CHIP nodes: {len(shared_chips)}"
    )

    if len(shared_chips) > 0:
        print("\nExamples:")
        print(shared_chips.head())


if __name__ == "__main__":

    df = pd.read_csv(
        "data/bom_single_level.csv"
    )

    validate_bom(df)