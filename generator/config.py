# Manufacturing stages

STAGES = [
    "RAW",
    "FAB_OUT",
    "WAFER",
    "DIE",
    "CHIP",
    "MODULE",
    "ASMBLD",
    "TSTD",
    "PKGD",
    "FPN",
]

PLANTS = [
    "PLT01",
    "PLT02",
    "PLT03",
]

BOM_ALTERNATIVES = [
    "01",
    "02",
]

# Maximum number of modules an ASMBLD can have
MAX_MODULES_PER_ASMBLD = 3

# Each CHIP must have exactly one descendant
CHIP_MAX_CHILDREN = 1