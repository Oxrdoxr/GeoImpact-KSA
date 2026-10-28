import json
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_JSONL = PROJECT_DIR / "data_clean" / "nawa_raw_hierarchy.jsonl"
OUTPUT_CSV = PROJECT_DIR / "data_clean" / "nawa_engineered_organizations.csv"
OUTPUT_SUMMARY = PROJECT_DIR / "outputs" / "hierarchical_summary.json"


def process_hierarchical_pipeline(
    input_path: Path = INPUT_JSONL,
    output_csv: Path = OUTPUT_CSV,
    output_summary: Path = OUTPUT_SUMMARY,
) -> pd.DataFrame:
    """Flatten organization records without exporting board-member personal data."""
    input_path = Path(input_path)
    output_csv = Path(output_csv)
    output_summary = Path(output_summary)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input JSONL file not found: {input_path}")

    organizations = []
    with input_path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                organization = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {input_path.name} at line {line_number}"
                ) from error
            if not isinstance(organization, dict):
                raise ValueError(
                    f"Expected a JSON object in {input_path.name} at line {line_number}"
                )

            members = organization.get("members") or []
            if not isinstance(members, list):
                raise ValueError(
                    f"Expected a member list in {input_path.name} at line {line_number}"
                )

            organizations.append(
                {
                    "id": organization.get("id"),
                    "name": organization.get("name", "غير محدد"),
                    "name_english": organization.get("name_english", ""),
                    "type": organization.get("type", "غير مصنف"),
                    "supervisor": organization.get("supervisor", "غير مصنف"),
                    "mainCategory": organization.get("mainCategory", "غير مصنف"),
                    "secondCategory": organization.get("secondCategory", "غير مصنف"),
                    "firstCategory": organization.get("firstCategory", "غير مصنف"),
                    "region": organization.get("region", "غير مصنف"),
                    "city": organization.get("city", "غير محدد"),
                    "unifiedNumber700": organization.get("unifiedNumber700", ""),
                    "members_count": len(members),
                }
            )

    if not organizations:
        raise ValueError(f"No organization records found in {input_path}")

    organizations_df = pd.DataFrame(organizations)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    try:
        organizations_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    except PermissionError as error:
        raise PermissionError(
            f"Cannot write {output_csv}; close it in Excel or another application and retry."
        ) from error

    summary = (
        organizations_df.groupby(
            ["supervisor", "mainCategory", "region"], dropna=False
        )
        .size()
        .reset_index(name="record_count")
    )
    output_summary.write_text(
        json.dumps(summary.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"Flattened {len(organizations_df):,} organization records; "
        "member-level personal data was not exported."
    )
    return organizations_df


if __name__ == "__main__":
    process_hierarchical_pipeline()
