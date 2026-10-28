"""Run the analysis pipeline: workbook -> validated table -> dashboard data, figures and executive report."""
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skills.coverage_skill import build_coverage_matrix, build_population_coverage
from skills.dashboard_export_skill import build_dashboard_payload, build_entity_index
from skills.figures_skill import build_figures
from skills.ingest_skill import audit, load_master, prepare_organizations
from skills.report_skill import build_report

WORKBOOK = "Saudi_Charities_Governance_Final_2026.xlsx"


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def run(project_dir: Path = PROJECT_DIR) -> dict:
    data_dir, outputs_dir = project_dir / "data_clean", project_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    population = pd.read_csv(data_dir / "regional_population_census_2022.csv", encoding="utf-8-sig")

    print("1/6 قراءة المصنف والتحقق منه")
    master = load_master(data_dir / WORKBOOK)
    organizations = prepare_organizations(master, population)
    report = audit(master, organizations)
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    organizations.to_csv(data_dir / "nawa_processed_organizations.csv", index=False, encoding="utf-8-sig")

    print("2/6 مصفوفة التغطية الوصفية")
    build_coverage_matrix(organizations).to_csv(
        outputs_dir / "gaps_analysis_report.csv", index=False, encoding="utf-8-sig"
    )

    print("3/6 المقارنة بالحصة السكانية")
    coverage = build_population_coverage(organizations, population)
    coverage.to_csv(outputs_dir / "population_coverage_analysis.csv", index=False, encoding="utf-8-sig")
    print("4/6 تصدير بيانات اللوحة")
    payload = build_dashboard_payload(organizations, coverage, population)
    write_json(outputs_dir / "dashboard_data.json", payload)
    write_json(outputs_dir / "entities.json", build_entity_index(organizations))
    print("5/6 الرسوم الثابتة")
    build_figures(payload, outputs_dir / "figures")
    print("6/6 التقرير التنفيذي")
    build_report(payload, report, project_dir / "report")
    print(f"تم: {report['total_records']:,} سجلاً، {len(coverage):,} صف مقارنة.")
    return report


if __name__ == "__main__":
    run()


