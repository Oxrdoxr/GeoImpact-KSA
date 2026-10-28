"""Stage 3: precompute everything the dashboard shows, so the UI only renders."""
import pandas as pd

from .coverage_skill import (
    TIER_RANGES,
    TIER_THRESHOLDS,
    TIERS,
    coverage_tier,
    short_main_category,
    validate_population,
)

UNCLASSIFIED = "غير مصنف"
ENTITY_COLUMNS = ("id", "name", "region", "type", "supervisor", "mainCategory", "city")


def _tier_payload(tier: tuple) -> dict:
    tier_id, label, color = tier
    return {"id": tier_id, "label": label, "color": color, "range": TIER_RANGES[tier_id]}


def build_region_summary(
    coverage: pd.DataFrame, population: pd.DataFrame, registered: pd.Series
) -> pd.DataFrame:
    """One row per region, ranked from the most critical to the least critical.

    Across several domains fill_ratio caps each domain at its fair share, so a
    surplus in one domain cannot hide a shortage in another. For a single
    domain it is the plain coverage ratio.
    """
    population = validate_population(population)
    total_population = float(population["population_millions"].sum())
    total_registered = max(int(registered.sum()), 1)
    single_domain = coverage["category"].nunique() == 1

    rows = []
    for region, millions in population.itertuples(index=False):
        part = coverage[coverage["region"] == region]
        expected = float(part["expected_count"].sum())
        actual = float(part["actual_count"].sum())
        covered = actual if single_domain else float(part[["actual_count", "expected_count"]].min(axis=1).sum())
        fill_ratio = covered / expected if expected else 1.0
        worst = part.sort_values("gap", ascending=False).iloc[0]
        tier = coverage_tier(fill_ratio)
        count = int(registered.get(region, 0))
        rows.append(
            {
                "region": region,
                "population_millions": millions,
                "population_share": millions / total_population,
                "registered": count,
                "registered_share": count / total_registered,
                "expected_total": round(expected, 1),
                "needed_total": int(part["estimated_gap"].sum()),
                "fill_ratio": fill_ratio,
                "red_domains": int((part["tier_id"] == "red").sum()),
                "worst_domain": worst["category"],
                "worst_domain_needed": int(worst["estimated_gap"]),
                "tier_id": tier[0],
                "tier_label": tier[1],
                "tier_color": tier[2],
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(["fill_ratio", "needed_total"], ascending=[True, False])
        .reset_index(drop=True)
        .assign(rank=lambda frame: frame.index + 1)
    )


def build_domain_summary(coverage: pd.DataFrame) -> pd.DataFrame:
    grouped = coverage.groupby("category")
    return (
        pd.DataFrame(
            {
                "national": grouped["national_count"].first(),
                "needed_total": grouped["estimated_gap"].sum(),
                "red_regions": grouped["tier_id"].apply(lambda s: int((s == "red").sum())),
            }
        )
        .reset_index()
        .rename(columns={"category": "domain"})
        .sort_values("national", ascending=False)
        .reset_index(drop=True)
    )


def _headline(regions: pd.DataFrame, domain: str | None) -> str:
    worst = regions.iloc[0]
    scope = f"في مجال «{domain}»، " if domain else ""
    return (
        f"{scope}{worst['region']} الأكثر حرجًا: تسدّ {round(worst['fill_ratio'] * 100)}% "
        f"من حصتها العادلة وتحتاج {int(worst['needed_total']):,} جهة."
    )


def _region_headline(region: dict, domain: str | None) -> str:
    scope = f"في مجال «{domain}»، " if domain else ""
    return (
        f"{scope}{region['region']}: تسدّ {round(region['fill_ratio'] * 100)}% "
        f"من حصتها العادلة وتحتاج {int(region['needed_total']):,} جهة."
    )


def _scope(regions: pd.DataFrame, domain: str | None) -> dict:
    region_rows = regions.round(4).to_dict(orient="records")
    for region in region_rows:
        region["headline"] = _region_headline(region, domain)
    return {
        "headline": _headline(regions, domain),
        "kpis": {
            "registered": int(regions["registered"].sum()),
            "needed_total": int(regions["needed_total"].sum()),
            "below_balance": int(regions["tier_id"].isin(["red", "yellow"]).sum()),
            "worst_region": regions.iloc[0]["region"],
        },
        "max_share": round(float(regions[["registered_share", "population_share"]].max().max()), 4),
        "regions": region_rows,
    }


def build_scopes(
    organizations: pd.DataFrame, coverage: pd.DataFrame, population: pd.DataFrame
) -> dict:
    """Region ranking for the whole sector and for each domain, precomputed."""
    overall = build_region_summary(coverage, population, organizations.groupby("region").size())
    scopes = {"all": _scope(overall, None)}
    for domain, part in coverage.groupby("category"):
        registered = part.groupby("region")["actual_count"].sum()
        scopes[domain] = _scope(build_region_summary(part, population, registered), domain)
    return scopes


def build_region_details(coverage: pd.DataFrame) -> dict:
    """Domains of each region, largest gap first."""
    ordered = coverage.sort_values(["estimated_gap", "coverage_ratio"], ascending=[False, True])
    return {
        region: [
            {
                "domain": row.category,
                "actual": int(row.actual_count),
                "expected": round(float(row.expected_count), 1),
                "needed": int(row.estimated_gap),
                "ratio": round(float(row.coverage_ratio), 3),
                "tier_id": row.tier_id,
            }
            for row in part.itertuples()
        ]
        for region, part in ordered.groupby("region")
    }


def build_dashboard_payload(
    organizations: pd.DataFrame, coverage: pd.DataFrame, population: pd.DataFrame
) -> dict:
    scopes = build_scopes(organizations, coverage, population)
    domains = build_domain_summary(coverage)
    regions = pd.DataFrame(scopes["all"]["regions"])
    by_registered = regions.sort_values("registered", ascending=False)
    top_two = by_registered.head(2)
    matrix = coverage.assign(
        expected_count=coverage["expected_count"].round(1),
        coverage_ratio=coverage["coverage_ratio"].round(3),
    )[["region", "category", "actual_count", "expected_count", "coverage_ratio", "estimated_gap", "tier_id"]]
    return {
        "meta": {
            "total_records": int(len(organizations)),
            "classified_records": int((~organizations["mainCategory"].eq(UNCLASSIFIED)).sum()),
            "region_count": int(len(regions)),
            "domain_count": int(len(domains)),
            "population_millions": round(float(regions["population_millions"].sum()), 1),
            "top_two_regions": top_two["region"].tolist(),
            "top_two_share": round(float(top_two["registered"].sum() / len(organizations)), 4),
            "top_two_population_share": round(float(top_two["population_share"].sum()), 4),
            "tier_thresholds": list(TIER_THRESHOLDS),
        },
        "tiers": [_tier_payload(tier) for tier in TIERS],
        "domains": domains.to_dict(orient="records"),
        "scopes": scopes,
        "region_details": build_region_details(coverage),
        "matrix": matrix.to_dict(orient="records"),
    }

def build_entity_index(organizations: pd.DataFrame) -> list:
    """Search index; personal data is never part of the prepared table."""
    index = organizations.loc[:, list(ENTITY_COLUMNS)].fillna("").astype(str)
    index["mainCategory"] = index["mainCategory"].map(short_main_category)
    return index.rename(columns={"mainCategory": "domain"}).to_dict(orient="records")
