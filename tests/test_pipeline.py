import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from skills.coverage_skill import build_population_coverage, coverage_tier
from skills.dashboard_export_skill import build_dashboard_payload, build_entity_index
from skills.ingest_skill import count_members, normalize_region, prepare_organizations

POPULATION = pd.DataFrame(
    {"region": ["الرياض", "المنطقة الشرقية"], "population_millions": [6.0, 2.0]}
)


def master(rows):
    base = {
        "name": "x",
        "type": "جمعية أهلية",
        "supervisor_final": "وزارة",
        "secondCategory": "s",
        "firstCategory": "f",
        "city": "c",
        "members": "[]",
    }
    return pd.DataFrame([{**base, **row} for row in rows])


def test_region_prefix_is_removed_and_eastern_kept():
    regions = set(POPULATION["region"])
    assert normalize_region("منطقة الرياض", regions) == "الرياض"
    assert normalize_region("المنطقة الشرقية", regions) == "المنطقة الشرقية"


def test_prepare_requires_unique_key():
    data = master(
        [
            {"unifiedNumber700": 1, "region": "منطقة الرياض", "mainCategory": "a"},
            {"unifiedNumber700": 1, "region": "منطقة الرياض", "mainCategory": "a"},
        ]
    )
    with pytest.raises(ValueError):
        prepare_organizations(data, POPULATION)


def test_prepare_rejects_unknown_region():
    data = master([{"unifiedNumber700": 1, "region": "منطقة مجهولة", "mainCategory": "a"}])
    with pytest.raises(ValueError):
        prepare_organizations(data, POPULATION)


def test_members_are_counted_not_kept():
    assert count_members("[{'name': 'a'}, {'name': 'b'}]") == 2
    assert count_members("[]") == 0
    prepared = prepare_organizations(
        master([{"unifiedNumber700": 1, "region": "منطقة الرياض", "mainCategory": "a",
                 "members": "[{'name': 'a'}]"}]),
        POPULATION,
    )
    assert "members" not in prepared.columns
    assert prepared.loc[0, "members_count"] == 1


def test_fair_share_and_gap():
    rows = [{"unifiedNumber700": i, "region": "منطقة الرياض", "mainCategory": "دعوة"} for i in range(1, 4)]
    rows.append({"unifiedNumber700": 9, "region": "المنطقة الشرقية", "mainCategory": "دعوة"})
    prepared = prepare_organizations(master(rows), POPULATION)
    result = build_population_coverage(prepared, POPULATION)
    east = result[result["region"] == "المنطقة الشرقية"].iloc[0]
    assert east["national_count"] == 4
    assert east["expected_count"] == pytest.approx(1.0)
    assert east["tier_id"] == "green"
    riyadh = result[result["region"] == "الرياض"].iloc[0]
    assert riyadh["expected_count"] == pytest.approx(3.0)


def test_unclassified_domains_are_excluded_from_comparison():
    rows = [
        {"unifiedNumber700": 1, "region": "منطقة الرياض", "mainCategory": "دعوة"},
        {"unifiedNumber700": 2, "region": "منطقة الرياض", "mainCategory": None},
    ]
    prepared = prepare_organizations(master(rows), POPULATION)
    result = build_population_coverage(prepared, POPULATION)
    assert set(result["category"]) == {"دعوة"}


@pytest.mark.parametrize(
    "ratio,tier",
    [(0.49, "red"), (0.5, "yellow"), (0.85, "green"), (1.25, "green"), (1.26, "purple")],
)
def test_tier_boundaries(ratio, tier):
    assert coverage_tier(ratio)[0] == tier


def test_dashboard_payload_ranks_most_critical_region_first():
    rows = [{"unifiedNumber700": i, "region": "منطقة الرياض", "mainCategory": "دعوة"} for i in range(1, 9)]
    rows.append({"unifiedNumber700": 99, "region": "المنطقة الشرقية", "mainCategory": "دعوة"})
    prepared = prepare_organizations(master(rows), POPULATION)
    coverage = build_population_coverage(prepared, POPULATION)
    payload = build_dashboard_payload(prepared, coverage, POPULATION)
    assert [r["region"] for r in payload["scopes"]["all"]["regions"]] == ["المنطقة الشرقية", "الرياض"]
    east = payload["scopes"]["all"]["regions"][0]
    assert east["rank"] == 1 and east["fill_ratio"] < 0.5 and east["tier_id"] == "red"
    assert payload["meta"]["total_records"] == 9
    assert "دعوة" in payload["scopes"] and payload["region_details"]["الرياض"]
    assert {"id", "label", "color", "range"} <= set(payload["tiers"][0])
    assert payload["scopes"]["all"]["regions"][0]["headline"].startswith("المنطقة الشرقية:")
    assert payload["scopes"]["all"]["regions"][1]["headline"].startswith("الرياض:")


def test_entity_index_has_no_member_data():
    prepared = prepare_organizations(
        master([{"unifiedNumber700": 1, "region": "منطقة الرياض", "mainCategory": "دعوة",
                 "members": "[{'name': 'secret'}]"}]),
        POPULATION,
    )
    index = build_entity_index(prepared)
    assert "secret" not in str(index) and "members" not in index[0]



def _payload():
    rows = [{"unifiedNumber700": i, "region": "منطقة الرياض", "mainCategory": "دعوة"} for i in range(1, 9)]
    rows.append({"unifiedNumber700": 99, "region": "المنطقة الشرقية", "mainCategory": "دعوة"})
    prepared = prepare_organizations(master(rows), POPULATION)
    coverage = build_population_coverage(prepared, POPULATION)
    return build_dashboard_payload(prepared, coverage, POPULATION)


def test_figures_mirror_dashboard_and_replace_stale_files(tmp_path):
    from skills.figures_skill import FIGURE_FILES, build_figures

    (tmp_path / "stale.png").write_bytes(b"x")
    build_figures(_payload(), tmp_path)
    assert sorted(p.name for p in tmp_path.glob("*.png")) == sorted(FIGURE_FILES)


def test_report_names_the_most_critical_region():
    from skills.report_skill import build_html, build_markdown

    quality = {"unique_keys": 9, "records_by_type": {"جمعية أهلية": 9}, "status": "PASSED"}
    markdown = build_markdown(_payload(), quality)
    assert "**المنطقة الشرقية**" in markdown
    for section in (
        "## 1. الفكرة",
        "## 2. لماذا هذه الفكرة",
        "## 3. البيانات وطريقة التعامل معها",
        "## 4. منهجية التحليل",
        "## 5. النتائج",
        "## 6. الرسوم",
        "## 7. المخرجات",
        "## 8. حدود القراءة",
    ):
        assert section in markdown
    # motivation examples are real rows from the outputs, not hypotheticals
    assert "**المنطقة الشرقية — دعوة:**" in markdown
    html = build_html(markdown)
    assert "<table>" in html
    assert 'href="https://www.stats.gov.sa/' in html
    assert "76.2%" in markdown and "2,300" in markdown
    assert "لا تدخل في حساب الحصة العادلة أو الفجوة" in markdown
