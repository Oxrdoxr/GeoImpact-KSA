"""Stage 1: read the governed workbook, validate it, and prepare the analysis table."""
import ast
from pathlib import Path
from typing import Union

import pandas as pd

MASTER_SHEET = "Charities_Master"
KEY_COLUMN = "unifiedNumber700"
UNCLASSIFIED = "غير مصنف"
REQUIRED_COLUMNS = (
    KEY_COLUMN,
    "name",
    "type",
    "region",
    "supervisor_final",
    "mainCategory",
    "secondCategory",
    "firstCategory",
)
TEXT_COLUMNS = (
    "type",
    "supervisor_final",
    "mainCategory",
    "secondCategory",
    "firstCategory",
    "city",
)
REGION_PREFIX = "منطقة "


def normalize_region(value: object, population_regions: set) -> str:
    """Map workbook labels ("منطقة الرياض") to the population table labels ("الرياض")."""
    if pd.isna(value):
        return ""
    label = " ".join(str(value).split())
    if label in population_regions:
        return label
    if label.startswith(REGION_PREFIX) and label[len(REGION_PREFIX):] in population_regions:
        return label[len(REGION_PREFIX):]
    return label


def count_members(value: object) -> int:
    """Count board members without keeping any personal data."""
    if not isinstance(value, str) or not value.strip():
        return 0
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return 0
    return len(parsed) if isinstance(parsed, (list, tuple)) else 0


def prepare_organizations(master: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in master.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if master.empty:
        raise ValueError("The master sheet is empty.")
    if master[KEY_COLUMN].isna().any() or master[KEY_COLUMN].duplicated().any():
        raise ValueError(f"{KEY_COLUMN} must be present and unique.")

    population_regions = set(population["region"].astype(str).str.strip())
    data = master.copy()
    data["region"] = data["region"].map(lambda v: normalize_region(v, population_regions))
    unknown = sorted(set(data["region"]) - population_regions)
    if unknown:
        raise ValueError("Regions missing from the population table: " + ", ".join(unknown))

    for column in TEXT_COLUMNS:
        if column in data.columns:
            data[column] = (
                data[column].astype("object").map(lambda v: v.strip() if isinstance(v, str) else v)
            )
            data[column] = data[column].replace("", pd.NA).fillna(UNCLASSIFIED)

    data["id"] = data[KEY_COLUMN].astype("int64").astype(str)
    data["unifiedNumber700"] = data["id"]
    data["supervisor"] = data["supervisor_final"]
    data["members_count"] = data["members"].map(count_members) if "members" in data else 0
    columns = [
        "id",
        "name",
        "name_english",
        "type",
        "supervisor",
        "mainCategory",
        "secondCategory",
        "firstCategory",
        "region",
        "city",
        "unifiedNumber700",
        "members_count",
    ]
    return data.loc[:, [c for c in columns if c in data.columns]].reset_index(drop=True)


def audit(master: pd.DataFrame, prepared: pd.DataFrame) -> dict:
    unclassified_main = int(prepared["mainCategory"].eq(UNCLASSIFIED).sum())
    return {
        "total_records": int(len(prepared)),
        "unique_keys": int(prepared["id"].nunique()),
        "regions": int(prepared["region"].nunique()),
        "missing_main_category": unclassified_main,
        "missing_supervisor": int(prepared["supervisor"].eq(UNCLASSIFIED).sum()),
        "records_by_type": {k: int(v) for k, v in prepared["type"].value_counts().items()},
        "status": "PASSED" if unclassified_main == 0 else "PASSED_WITH_WARNINGS",
    }


def load_master(path: Union[str, Path]) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Workbook not found: {path}")
    return pd.read_excel(path, sheet_name=MASTER_SHEET) 
