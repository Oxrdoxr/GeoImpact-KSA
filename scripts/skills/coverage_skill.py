"""Stage 2: descriptive coverage matrix and the population-share comparison."""
import re

import pandas as pd

UNCLASSIFIED = "غير مصنف"
EXCLUDED_MAIN_CATEGORIES = {UNCLASSIFIED, "تصنيف اساسي اخرى"}
TIERS = (
    ("red", "عجز حرج", "#d9383a"),
    ("yellow", "فجوة متوسطة", "#e69500"),
    ("green", "متوازن", "#2e8540"),
    ("purple", "تشبع", "#7b4acb"),
)
TIER_RANGES = {
    "red": "أقل من 50% من الحصة العادلة",
    "yellow": "من 50% إلى أقل من 85%",
    "green": "من 85% إلى 125%",
    "purple": "أعلى من 125%",
}


TIER_THRESHOLDS = (0.5, 0.85, 1.25)


def coverage_tier(ratio: float) -> tuple:
    low, mid, high = TIER_THRESHOLDS
    if ratio < low:
        return TIERS[0]
    if ratio < mid:
        return TIERS[1]
    if ratio <= high:
        return TIERS[2]
    return TIERS[3]


DOMAIN_DISPLAY_OVERRIDES = {
    "الدعوة والإرشاد والتعليم الديني وخدمة ضيوف الرحمن": "الدعوة والتعليم الديني",
}


def short_main_category(value: str) -> str:
    """Display name of a domain: drops the group ordinal, the parenthetical and filler words."""
    text = str(value).split("(", maxsplit=1)[0]
    text = re.sub(r"^المجموعة\s+[^\s:]+\s*:?\s*", "", text)
    text = re.sub(r"^منظمات\s+", "", text.strip())
    text = re.sub(r"\s+و\s+", " و", re.sub(r"\s+", " ", text)).strip()
    return DOMAIN_DISPLAY_OVERRIDES.get(text, text)


def validate_population(population: pd.DataFrame) -> pd.DataFrame:
    data = population.loc[:, ["region", "population_millions"]].copy()
    data["region"] = data["region"].astype(str).str.strip()
    data["population_millions"] = pd.to_numeric(data["population_millions"], errors="raise")
    if (data["population_millions"] <= 0).any() or data["region"].duplicated().any():
        raise ValueError("Population values must be positive and regions unique.")
    return data


def build_coverage_matrix(organizations: pd.DataFrame) -> pd.DataFrame:
    """Registered counts per region x category path x type; a registration indicator only."""
    dimensions = ["region", "mainCategory", "secondCategory", "firstCategory", "type"]
    observed = organizations.groupby(dimensions).size().reset_index(name="record_count")
    regions = organizations[["region"]].drop_duplicates()
    paths = organizations[dimensions[1:]].drop_duplicates()
    matrix = regions.merge(paths, how="cross").merge(observed, on=dimensions, how="left")
    matrix["record_count"] = matrix["record_count"].fillna(0).astype(int)
    positive = matrix.loc[matrix["record_count"] > 0, "record_count"]
    cutoff = float(positive.quantile(0.25, interpolation="lower"))
    matrix["low_coverage_cutoff"] = round(cutoff, 2)
    matrix["gap_status"] = matrix["record_count"].map(
        lambda n: "لا توجد سجلات مطابقة في لقطة نوى (مؤشر تسجيل فقط)"
        if n == 0
        else "تسجيل منخفض نسبياً (الربع الأدنى)"
        if n <= cutoff
        else "توجد سجلات"
    )
    return matrix.sort_values(["record_count", *dimensions]).reset_index(drop=True)


def build_population_coverage(
    organizations: pd.DataFrame, population: pd.DataFrame
) -> pd.DataFrame:
    """Fair share per region: national entities in the domain x region share of population."""
    population = validate_population(population)
    total_population = float(population["population_millions"].sum())

    source = organizations.copy()
    source["mainCategory"] = source["mainCategory"].map(short_main_category)
    source["category"] = source["mainCategory"]
    source = source[
        ~source["mainCategory"].isin(EXCLUDED_MAIN_CATEGORIES)
        & source["region"].isin(population["region"])
    ]
    if source.empty:
        raise ValueError("No comparable organization records were found.")

    keys = source[["id", "region", "category"]].drop_duplicates()
    national = keys.groupby("category")["id"].nunique()
    actual = keys.groupby(["category", "region"])["id"].nunique()
    rows = []
    for category, national_count in national.items():
        for region, millions in population.itertuples(index=False):
            actual_count = int(actual.get((category, region), 0))
            expected = national_count * millions / total_population
            ratio = actual_count / expected
            tier_id, tier_label, tier_color = coverage_tier(ratio)
            rows.append(
                {
                    "region": region,
                    "category": category,
                    "actual_count": actual_count,
                    "national_count": int(national_count),
                    "expected_count": expected,
                    "gap": expected - actual_count,
                    "coverage_ratio": ratio,
                    "estimated_gap": max(0, round(expected - actual_count)),
                    "tier_id": tier_id,
                    "tier_label": tier_label,
                    "tier_color": tier_color,
                }
            )
    return pd.DataFrame(rows)
