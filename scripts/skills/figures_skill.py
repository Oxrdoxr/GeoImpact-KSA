"""Stage 5: static copies of the dashboard figures, drawn from the same payload."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

FONT_CANDIDATES = ("Tajawal", "Segoe UI", "Tahoma", "Arial")
NAVY, GOLD, MUTED, TINT = "#0f2a43", "#c9a24a", "#5b6b7c", "#f3f6fa"
FIGURE_FILES = (
    "reverse_leaderboard.png",
    "deficit_heatmap.png",
    "shares_vs_population.png",
    "worst_region_domains.png",
)


def _use_font() -> None:
    installed = {font.name for font in font_manager.fontManager.ttflist}
    name = next((font for font in FONT_CANDIDATES if font in installed), "DejaVu Sans")
    plt.rcParams.update({"font.family": name, "axes.unicode_minus": False})


def ar(text: object) -> str:
    """Matplotlib >= 3.11 shapes and reorders Arabic itself (libraqm)."""
    return str(text)


def _tier_colors(payload: dict) -> dict:
    return {tier["id"]: tier["color"] for tier in payload["tiers"]}


def _save(fig, path: Path) -> Path:
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def reverse_leaderboard(payload: dict, path: Path) -> Path:
    regions = payload["scopes"]["all"]["regions"]
    low, mid, _ = payload["meta"]["tier_thresholds"]
    fig, ax = plt.subplots(figsize=(9, 0.55 * len(regions) + 1.4))
    for position, region in enumerate(regions):
        ax.barh(position, 1, color=TINT, height=0.55)
        ax.barh(position, min(region["fill_ratio"], 1), color=region["tier_color"], height=0.55)
        ax.text(
            min(region["fill_ratio"], 1) + 0.015,
            position,
            f"{round(region['fill_ratio'] * 100)}%  ·  +{region['needed_total']:,}",
            va="center",
            fontsize=9,
            color=MUTED,
        )
    for mark in (low, mid):
        ax.axvline(mark, color=NAVY, alpha=0.35, linewidth=1, linestyle="--")
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels([ar(f"{r['rank']}. {r['region']}") for r in regions], fontsize=10)
    ax.set_xlim(0, 1.35)
    ax.set_xticks([0, 0.5, 1])
    ax.set_xticklabels(["0%", "50%", "100%"], color=MUTED)
    ax.invert_yaxis()
    ax.set_title(ar("الأكثر حرجًا أولًا · نسبة سدّ الحصة العادلة وعدد الجهات المطلوبة"), fontsize=12, color=NAVY)
    ax.spines[["top", "right", "left"]].set_visible(False)
    return _save(fig, path)


def deficit_heatmap(payload: dict, path: Path) -> Path:
    regions = [row["region"] for row in payload["scopes"]["all"]["regions"]]
    domains = [row["domain"] for row in payload["domains"]]
    colors = _tier_colors(payload)
    cells = {(row["region"], row["category"]): row for row in payload["matrix"]}
    fig, ax = plt.subplots(figsize=(1.0 * len(domains) + 2, 0.5 * len(regions) + 2.4))
    for y, region in enumerate(regions):
        for x, domain in enumerate(domains):
            cell = cells[(region, domain)]
            color = colors[cell["tier_id"]]
            ax.add_patch(Rectangle((x, y), 0.94, 0.88, facecolor=color, alpha=0.22, edgecolor="none"))
            ax.text(x + 0.47, y + 0.46, cell["estimated_gap"] or "·", ha="center", va="center", fontsize=9, fontweight="bold", color=color)
    ax.set_xlim(0, len(domains))
    ax.set_ylim(len(regions), 0)
    ax.set_xticks([x + 0.47 for x in range(len(domains))])
    ax.set_xticklabels([ar(d) for d in domains], rotation=40, ha="right", fontsize=9)
    ax.set_yticks([y + 0.44 for y in range(len(regions))])
    ax.set_yticklabels([ar(r) for r in regions], fontsize=10)
    ax.xaxis.tick_top()
    plt.setp(ax.get_xticklabels(), rotation=40, ha="left")
    ax.tick_params(length=0)
    ax.spines[:].set_visible(False)
    ax.set_title(ar("خريطة العجز · الرقم = جهات مطلوبة لبلوغ الحصة العادلة"), fontsize=12, color=NAVY, pad=70)
    return _save(fig, path)


def shares_vs_population(payload: dict, path: Path) -> Path:
    regions = sorted(payload["scopes"]["all"]["regions"], key=lambda r: -r["registered_share"])
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(regions) + 1.6))
    for position, region in enumerate(regions):
        ax.barh(position - 0.18, region["registered_share"] * 100, height=0.34, color=NAVY)
        ax.barh(position + 0.18, region["population_share"] * 100, height=0.34, color=GOLD)
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels([ar(r["region"]) for r in regions], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("%", color=MUTED)
    ax.legend(
        [Rectangle((0, 0), 1, 1, color=NAVY), Rectangle((0, 0), 1, 1, color=GOLD)],
        [ar("حصتها من الجهات المسجلة"), ar("حصتها من السكان")],
        frameon=False,
        loc="lower right",
    )
    ax.set_title(ar("حصة الجهات المسجلة مقابل حصة السكان"), fontsize=12, color=NAVY)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, path)


def worst_region_domains(payload: dict, path: Path) -> Path:
    region = payload["scopes"]["all"]["regions"][0]["region"]
    rows = payload["region_details"][region]
    colors = _tier_colors(payload)
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(rows) + 1.6))
    for position, row in enumerate(rows):
        ax.barh(position, row["expected"], height=0.62, facecolor=TINT, edgecolor=MUTED, linestyle="--", linewidth=0.8)
        ax.barh(position, row["actual"], height=0.34, color=colors[row["tier_id"]])
        ax.text(max(row["expected"], row["actual"]) * 1.02, position, f"{row['actual']:,} / {row['expected']:,.1f}", va="center", fontsize=9, color=MUTED)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([ar(row["domain"]) for row in rows], fontsize=10)
    ax.invert_yaxis()
    ax.legend(
        handles=[
            Line2D([0], [0], color=NAVY, linewidth=5, label=ar("المسجل فعليًا")),
            Patch(facecolor=TINT, edgecolor=NAVY, linestyle="--", label=ar("الحصة العادلة المتوقعة")),
        ],
        frameon=False,
        loc="lower right",
        ncols=2,
    )
    ax.set_title(ar(f"{region} · الفعلي مقابل الحصة العادلة"), fontsize=12, color=NAVY)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, path)


def build_figures(payload: dict, figures_dir: Path) -> list[Path]:
    """Redraw every figure, and drop stale ones so the folder mirrors the dashboard."""
    _use_font()
    figures_dir.mkdir(parents=True, exist_ok=True)
    for stale in figures_dir.glob("*.png"):
        stale.unlink()
    builders = (reverse_leaderboard, deficit_heatmap, shares_vs_population, worst_region_domains)
    return [builder(payload, figures_dir / name) for builder, name in zip(builders, FIGURE_FILES)]
