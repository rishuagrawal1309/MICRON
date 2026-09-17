import pandas as pd


STAGE_COLUMNS = [
    "FPN",
    "PKGD",
    "TSTD",
    "ASMBLD",
    "MODULE",
    "CHIP",
    "DIE",
    "WAFER",
    "FAB_OUT",
    "RAW",
]


def build_graph(df):
    """
    Build:

        parent -> children

    from BOM_SINGLE_LEVEL.
    """

    graph = {}

    for _, row in df.iterrows():

        parent = row["HDR_MATERIAL"]
        child = row["COMP_MATERIAL"]

        if parent not in graph:
            graph[parent] = []

        graph[parent].append({
            "material": child,
            "stage": row["COMP_MATL_GROUP"],
        })

    return graph


def find_fpns(df):
    """
    Find all FPN materials.
    """

    fpns = df[
        df["HDR_MATL_GROUP"] == "FPN"
    ]["HDR_MATERIAL"].unique()

    return list(fpns)


def dfs_paths(
    graph,
    current_material,
    current_path,
    all_paths,
    visited
):
    """
    DFS traversal.

    current_path contains:

        [(material, stage), ...]
    """

    # Cycle protection
    if current_material in visited:
        return

    visited = visited | {current_material}

    children = graph.get(
        current_material,
        []
    )

    # No children => leaf
    if not children:

        all_paths.append(
            current_path
        )

        return

    for child in children:

        child_material = child["material"]
        child_stage = child["stage"]

        dfs_paths(
            graph=graph,
            current_material=child_material,

            current_path=current_path + [
                (
                    child_material,
                    child_stage
                )
            ],

            all_paths=all_paths,

            visited=visited
        )


def flatten_fpn(df, fpn):
    """
    Generate all complete paths
    starting from one FPN.
    """

    graph = build_graph(df)

    all_paths = []

    dfs_paths(
        graph=graph,

        current_material=fpn,

        current_path=[
            (
                fpn,
                "FPN"
            )
        ],

        all_paths=all_paths,

        visited=set()
    )

    return all_paths


def path_to_flat_row(path):
    """
    Convert:

        [(material, stage), ...]

    into:

        {
            FPN: ...,
            PKGD: ...,
            ...
        }
    """

    row = {
        column: None
        for column in STAGE_COLUMNS
    }

    for material, stage in path:

        if stage in row:

            row[stage] = material

    return row


def generate_flat_bom(df):
    """
    Generate BOM_FLAT for all FPNs.
    """

    all_rows = []

    fpns = find_fpns(df)

    for fpn in fpns:

        paths = flatten_fpn(
            df,
            fpn
        )

        for path in paths:

            flat_row = path_to_flat_row(
                path
            )

            all_rows.append(
                flat_row
            )

    return pd.DataFrame(
        all_rows,
        columns=STAGE_COLUMNS
    )


if __name__ == "__main__":

    input_file = (
        "data/bom_single_level.csv"
    )

    output_file = (
        "data/bom_flat.csv"
    )

    df = pd.read_csv(
        input_file
    )

    flat_df = generate_flat_bom(
        df
    )

    flat_df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Generated {len(flat_df)} flat paths."
    )

    print(
        f"Saved to: {output_file}"
    )

    print(
        "\nFirst 20 paths:\n"
    )

    print(
        flat_df
        .head(20)
        .to_string(index=False)
    )