import random
import pandas as pd
from datetime import date, timedelta

from config import PLANTS, BOM_ALTERNATIVES


RANDOM_SEED = 42


def random_date():
    start = date(2025, 1, 1)
    end = date(2027, 12, 31)

    days = (end - start).days

    return start + timedelta(
        days=random.randint(0, days)
    )


def create_row(
    parent,
    parent_stage,
    child,
    child_stage,
    quantity,
    plant,
    bom_alt,
    item_no
):
    valid_from = random_date()

    # Most records are valid for a long period
    valid_to = valid_from + timedelta(
        days=random.randint(180, 1000)
    )

    return {
        "HDR_MATERIAL": parent,
        "HDR_MATL_GROUP": parent_stage,

        "COMP_MATERIAL": child,
        "COMP_MATL_GROUP": child_stage,

        "COMP_QTY": quantity,
        "HEADER_QTY": 1,

        "PLANT": plant,
        "BOM_ALT": bom_alt,

        "BOM_STATUS": "01",
        "BOM_USG": "1",

        "ITEM_NO": item_no,

        "VALID_FROM": valid_from,
        "VALID_TO": valid_to,

        "DEL_FLAG": ""
    }


def generate_chain(
    chip_id,
    die_counter,
    wafer_counter,
    fab_counter,
    raw_counter,
    plant,
    bom_alt
):
    """
    Every CHIP has exactly ONE descendant.

    CHIP
      |
     DIE
      |
    WAFER
      |
    FAB_OUT
      |
     RAW
    """

    rows = []

    die_id = f"DIE-{die_counter:04d}"
    wafer_id = f"WAFER-{wafer_counter:04d}"
    fab_id = f"FAB-{fab_counter:04d}"
    raw_id = f"RAW-{raw_counter:04d}"

    rows.append(
        create_row(
            chip_id,
            "CHIP",
            die_id,
            "DIE",
            random.randint(1, 4),
            plant,
            bom_alt,
            10
        )
    )

    rows.append(
        create_row(
            die_id,
            "DIE",
            wafer_id,
            "WAFER",
            random.randint(1, 4),
            plant,
            bom_alt,
            10
        )
    )

    rows.append(
        create_row(
            wafer_id,
            "WAFER",
            fab_id,
            "FAB_OUT",
            random.randint(1, 2),
            plant,
            bom_alt,
            10
        )
    )

    rows.append(
        create_row(
            fab_id,
            "FAB_OUT",
            raw_id,
            "RAW",
            random.randint(1, 3),
            plant,
            bom_alt,
            10
        )
    )

    return rows


def generate_fpn(fpn_number):
    """
    Generate one complete FPN BOM.

    Structure:

    FPN
      |
    PKGD
      |
    TSTD
      |
    ASMBLD
      |
    0-3 MODULES
      |
    1+ CHIPS per MODULE

    Modules may share chips.
    """

    rows = []

    fpn = f"FPN-{fpn_number:04d}"
    pkg = f"PKGD-{fpn_number:04d}"
    tstd = f"TSTD-{fpn_number:04d}"
    asmbld = f"ASMBLD-{fpn_number:04d}"

    plant = random.choice(PLANTS)
    bom_alt = random.choice(BOM_ALTERNATIVES)

    # -----------------------------------------
    # FPN -> PKGD
    # -----------------------------------------

    rows.append(
        create_row(
            fpn,
            "FPN",
            pkg,
            "PKGD",
            1,
            plant,
            bom_alt,
            10
        )
    )

    # -----------------------------------------
    # PKGD -> TSTD
    # -----------------------------------------

    rows.append(
        create_row(
            pkg,
            "PKGD",
            tstd,
            "TSTD",
            1,
            plant,
            bom_alt,
            10
        )
    )

    # -----------------------------------------
    # TSTD -> ASMBLD
    # -----------------------------------------

    rows.append(
        create_row(
            tstd,
            "TSTD",
            asmbld,
            "ASMBLD",
            1,
            plant,
            bom_alt,
            10
        )
    )

    # -----------------------------------------
    # ASMBLD -> MODULES
    # -----------------------------------------

    # 0-3 modules
    num_modules = random.randint(0, 3)

    modules = []

    for module_index in range(num_modules):

        module_id = (
            f"MODULE-{fpn_number:04d}-"
            f"{chr(65 + module_index)}"
        )

        modules.append(module_id)

        rows.append(
            create_row(
                asmbld,
                "ASMBLD",
                module_id,
                "MODULE",
                1,
                plant,
                bom_alt,
                (module_index + 1) * 10
            )
        )

        # -----------------------------------------
    # MODULE -> CHIP
    # -----------------------------------------

    chips_for_fpn = []

    chip_counter = 1

    for module in modules:

        # Every module must have at least one CHIP.
        num_chips = random.randint(1, 2)

        # Chips already assigned to this module.
        module_chips = set()

        for _ in range(num_chips):

            # Existing chips that this module has NOT
            # already used.
            available_shared_chips = [
                chip
                for chip in chips_for_fpn
                if chip not in module_chips
            ]

            # 40% chance to share an existing CHIP.
            if (
                available_shared_chips
                and random.random() < 0.40
            ):

                chip_id = random.choice(
                    available_shared_chips
                )

            else:

                chip_id = (
                    f"CHIP-{fpn_number:04d}-"
                    f"{chip_counter:02d}"
                )

                chip_counter += 1

                chips_for_fpn.append(
                    chip_id
                )

            module_chips.add(chip_id)

            rows.append(
                create_row(
                    module,
                    "MODULE",
                    chip_id,
                    "CHIP",
                    random.randint(1, 4),
                    plant,
                    bom_alt,
                    random.randint(10, 90)
                )
            )
    # -----------------------------------------
    # CHIP -> descendants
    # -----------------------------------------

    # Generate exactly ONE chain per UNIQUE CHIP.
    #
    # This is important:
    #
    # MODULE-A -> CHIP-001
    # MODULE-B -> CHIP-001
    #
    # still produces:
    #
    # CHIP-001 -> ONE DIE
    #
    # and NOT two different DIEs.

    for chip_index, chip_id in enumerate(chips_for_fpn):

        rows.extend(
            generate_chain(
                chip_id=chip_id,

                die_counter=(
                    fpn_number * 100
                    + chip_index
                    + 1
                ),

                wafer_counter=(
                    fpn_number * 100
                    + chip_index
                    + 1
                ),

                fab_counter=(
                    fpn_number * 100
                    + chip_index
                    + 1
                ),

                raw_counter=(
                    fpn_number * 100
                    + chip_index
                    + 1
                ),

                plant=plant,
                bom_alt=bom_alt
            )
        )

    return rows


def generate_dataset(num_fpns=20):

    random.seed(RANDOM_SEED)

    all_rows = []

    for fpn_number in range(1, num_fpns + 1):

        rows = generate_fpn(fpn_number)

        all_rows.extend(rows)

    return pd.DataFrame(all_rows)


if __name__ == "__main__":

    df = generate_dataset(num_fpns=20)

    output_file = "data/bom_single_level.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Generated {len(df)} BOM relationships."
    )

    print(
        f"Saved to: {output_file}"
    )

    print("\nFirst 20 rows:\n")

    print(
        df.head(20).to_string(index=False)
    )