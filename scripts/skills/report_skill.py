"""Stage 6: executive report (Markdown, HTML, PDF) written from the pipeline outputs."""
import html
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .figures_skill import FIGURE_FILES

TOP_REGIONS = 5
BROWSERS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
)


def _percent(ratio: float) -> str:
    return f"{round(ratio * 100)}%"


def _table(header: list, rows: list) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def _motivation_examples(payload: dict, limit: int = 3) -> list:
    """Lowest-coverage critical (red) region/domain pairs, one per region and domain."""
    rows = [
        {"region": region, **detail}
        for region, details in payload["region_details"].items()
        for detail in details
        if detail["tier_id"] == "red"
    ]
    rows.sort(key=lambda row: row["ratio"])
    picked, seen_regions, seen_domains = [], set(), set()
    for row in rows:
        if row["region"] in seen_regions or row["domain"] in seen_domains:
            continue
        picked.append(row)
        seen_regions.add(row["region"])
        seen_domains.add(row["domain"])
        if len(picked) == limit:
            break
    return picked


def build_markdown(payload: dict, quality: dict, figures_rel: str = "../outputs/figures") -> str:
    meta, tiers = payload["meta"], payload["tiers"]
    scope = payload["scopes"]["all"]
    regions, domains = scope["regions"], payload["domains"]
    low, mid, high = meta["tier_thresholds"]
    unclassified = meta["total_records"] - meta["classified_records"]
    types = "، ".join(f"{name}: {count:,}" for name, count in quality["records_by_type"].items())

    leaderboard = _table(
        ["#", "المنطقة", "نسبة سدّ الحصة العادلة", "جهات مطلوبة", "مجالات حرجة", "الأشد نقصًا"],
        [
            [r["rank"], r["region"], _percent(r["fill_ratio"]), f"{r['needed_total']:,}", r["red_domains"], r["worst_domain"]]
            for r in regions[:TOP_REGIONS]
        ],
    )
    domain_table = _table(
        ["المجال", "جهات وطنيًا", "جهات مطلوبة", "مناطق في العجز الحرج"],
        [[d["domain"], f"{d['national']:,}", f"{d['needed_total']:,}", d["red_regions"]] for d in domains],
    )
    tier_table = _table(["الفئة", "نسبة التغطية"], [[t["label"], t["range"]] for t in tiers])
    figures = "\n\n".join(
        f"![{name.removesuffix('.png')}]({figures_rel}/{name})" for name in FIGURE_FILES
    )
    worst = regions[0]
    red_regions = sum(r["tier_id"] == "red" for r in regions)
    examples = _motivation_examples(payload)
    examples_md = "\n".join(
        f"- **{e['region']} — {e['domain']}:** {e['actual']:,} جهة مسجلة مقابل حصة عادلة تقديرية {e['expected']:.1f} جهة (تغطية {_percent(e['ratio'])})."
        for e in examples
    ) or "- لا توجد فجوات حرجة في البيانات الحالية."

    return f"""# GeoImpact KSA — التقرير التنفيذي

> أُنشئ تلقائيًا من مخرجات خط التحليل بتاريخ {datetime.now():%Y-%m-%d %H:%M}.

## 1. الفكرة

لوحة قرار تفاعلية وخط تحليل قابل لإعادة التشغيل يقارنان التوزيع الجغرافي للجهات غير الربحية المسجلة (سجلات منصة نوى) مع حصة كل منطقة من سكان المملكة، لكل مجال من مجالات العمل، لرصد فجوات التوزيع وترتيبها بما يدعم توجيه التأسيس والدعم نحو المناطق والمجالات الأشد نقصًا.

**السؤال:** هل ينمو القطاع الثالث بتوازن بين مناطق المملكة ومجالات العمل، وكم جهة تحتاجها كل منطقة لتطابق حصتها من السكان؟

## 2. لماذا هذه الفكرة

- غالب الجهات غير الربحية تخدم نطاق منطقتها؛ فإذا كان مجال ما شبه غائب في منطقة، فقد يضطر سكانها إلى السفر بحثًا عن الخدمة أو الاستغناء عنها، لذا يهمّ قياس التنوع المحلي داخل القطاع لا العدد الوطني وحده.
- تستهدف [استراتيجية المركز الوطني لتنمية القطاع غير الربحي](https://www.vision2030.gov.sa/ar/explore/strategies/national-center-for-non-profit-sector-strategy) ضمن رؤية 2030 رفع مساهمة القطاع إلى 5% من الناتج المحلي؛ وهو مستهدف وطني يستدعي نموًا متوازنًا بين المناطق والمجالات، ويُستخدم هنا كسياق لا كهدف عددي لكل منطقة.
- أمثلة حقيقية من مخرجات هذا المشروع (أدنى نسب التغطية ضمن فئة «عجز حرج»):
{examples_md}
- هذه الفجوات إشارات تستحق التحقق الميداني (هل الخدمة غائبة فعلًا أم تغطيها جهات بديلة؟)، وليست إثباتًا لغياب الخدمة — كما تفصّله «حدود القراءة».

## 3. البيانات وطريقة التعامل معها

### المصادر

- **سجلات الجهات:** منصة نوى بعد التنظيف في دفتر `notebooks/cleaning_data.ipynb`، والناتج مصنف `Saudi_Charities_Governance_Final_2026.xlsx`.
- **السكان:** الهيئة العامة للإحصاء، [لوحة معلومات المناطق الإدارية](https://www.stats.gov.sa/ar/w/%D8%B9%D8%B1%D8%B6-%D9%85%D8%B9%D9%84%D9%88%D9%85%D8%A7%D8%AA-%D8%A7%D9%84%D9%85%D9%86%D8%A7%D8%B7%D9%82-%D8%A7%D9%84%D8%A5%D8%AF%D8%A7%D8%B1%D9%8A%D8%A9?category=127436&tab=436327)، ضمن إحصاءات تعداد السعودية 2022. القيم المستخدمة في الملف مقربة إلى 0.1 مليون.

### خطوات التعامل والتنظيف

- إسقاط الأعمدة الفارغة أو الحساسة (العنوان التفصيلي، الجوال، البريد الإلكتروني) وتطهير النصوص من الرموز غير المرئية والمسافات الزائدة.
- اعتماد `unifiedNumber700` مفتاحًا أساسيًا وحذف عمود `id` التالف؛ {quality['unique_keys']:,} سجلًا بمعرّف موحد فريد من أصل {meta['total_records']:,}.
- توحيد أسماء المناطق (إضافة «منطقة» للأسماء المجردة، ومعالجة خاصة لـ«المنطقة الشرقية») لمطابقة جدول السكان.
- توحيد مسميات جهات الإشراف وإسناد القيم المفقودة بمسمى نظامي صريح بدل التخمين؛ وإشراف الصناديق العائلية مشتق من نوع الكيان ومُوسوم بذلك في البيانات (`supervisor_source`, `category_source`).
- **الخصوصية:** تفكيك حقل الأعضاء ثم الاحتفاظ بعددهم فقط (`members_count`)؛ لا تدخل بيانات الأفراد في أي مخرج.
- **المستبعد من المقارنة:** {unclassified} جهة غير مصنفة، إضافة إلى سجلات «تصنيف أساسي أخرى».
- **حالة فحص الجودة:** `{quality['status']}`.

### حجم البيانات وتصنيفها

- **الحجم:** {meta['total_records']:,} سجلًا موزعة على {meta['region_count']} منطقة إدارية.
- **أنواع الكيانات:** {types}.
- **التصنيف:** {meta['classified_records']:,} جهة مصنفة في {meta['domain_count']} مجالًا، والصناديق العائلية مجال مستقل.

### سياق القطاع من التقرير السنوي 2025

- يذكر التقرير السنوي للمركز الوطني لتنمية القطاع غير الربحي أن الإنفاق التنموي بلغ **76.2%** من إجمالي إنفاق القطاع في **2024**، مقابل **75.3%** في **2023**.
- تجاوزت عمليات الفحص والمراجعة للمنظمات غير الربحية **2,300 عملية** في **2025**، ويعرض التقرير نموًا بنسبة **37%** مقارنة بـ **1,670 عملية** في **2024**.
- هذه مؤشرات وطنية مستقلة عن سجلات نوى؛ تُعرض للسياق فقط، ولا تدخل في حساب الحصة العادلة أو الفجوة، ولا تثبت توزيع الجهات أو الطلب أو جودة الخدمات. المصدر: [التقرير السنوي 2025 للمركز الوطني لتنمية القطاع غير الربحي](https://ncnp.gov.sa/ar/reports)، ص 18.

## 4. منهجية التحليل

1. **التحقق:** معرّف فريد لكل سجل، وأعمدة مطلوبة، وتوحيد أسماء المناطق مع جدول السكان (تعداد 2022).
2. **الحصة العادلة** لكل منطقة ومجال: `الحصة العادلة = إجمالي جهات المجال وطنيًا × (سكان المنطقة ÷ إجمالي السكان)`.
3. **الفجوة:** `الفجوة = الحصة العادلة − المسجل فعليًا`، وعدد الجهات المطلوبة هو الفجوة مقرّبة وغير سالبة.
4. **نسبة التغطية** = المسجل ÷ الحصة العادلة، وتُصنَّف بحدود {low} و{mid} و{high}:

{tier_table}

5. **نسبة سدّ المنطقة** تحسب كل مجال حتى حدّ حصته فقط، فلا يُخفي فائضٌ في مجال نقصًا في آخر. وبها تُرتَّب لوحة الأكثر حرجًا من الأسوأ إلى الأفضل.

## 5. النتائج

- المنطقة الأكثر حرجًا هي **{worst['region']}**: تسدّ {_percent(worst['fill_ratio'])} من حصتها العادلة وتحتاج **{worst['needed_total']:,}** جهة، وأشد مجالاتها نقصًا «{worst['worst_domain']}».
- إجمالي الجهات المطلوبة لبلوغ التوازن في كل المناطق: **{sum(r['needed_total'] for r in regions):,}** جهة. عدد المناطق في العجز الحرج: **{red_regions}**، ودون التوازن (حرجة أو متوسطة): **{scope['kpis']['below_balance']}**.
- أكبر منطقتين تسجيلًا ({'، '.join(meta['top_two_regions'])}) تضمان {_percent(meta['top_two_share'])} من الجهات مقابل {_percent(meta['top_two_population_share'])} من السكان.

### المناطق الأكثر حرجًا

{leaderboard}

### المجالات

{domain_table}

## 6. الرسوم البيانية

{figures}

## 7. المخرجات

| الملف | المحتوى |
|---|---|
| `outputs/dashboard_data.json` | بيانات اللوحة المحسوبة مسبقًا |
| `outputs/entities.json` | فهرس بحث الكيانات بلا بيانات شخصية |
| `outputs/population_coverage_analysis.csv` | المقارنة بالحصة السكانية لكل منطقة ومجال |
| `outputs/gaps_analysis_report.csv` | مصفوفة التغطية الوصفية |
| `outputs/data_quality_report.json` | تقرير جودة البيانات |
| `outputs/figures/` | نسخ ثابتة من رسوم اللوحة |
| `dashboard/` | لوحة القرار التفاعلية |

## 8. حدود القراءة

- المؤشر يقارن **التسجيل** بحصة السكان؛ لا يثبت وجود طلب أو غياب خدمة، ولا يقيس جودة الخدمة.
- أرقام السكان مقرّبة إلى 0.1 مليون وتتأثر بها المناطق الصغيرة؛ مصدرها موضح في قسم البيانات.
- الصناديق العائلية وإشرافها مبنيان على قاعدة مشتقة من نوع الكيان، وليستا حقلًا مصدريًا.
- مناطق صغيرة السكان قد تُظهر عجزًا بأرقام صغيرة؛ يُفضَّل قراءتها مع نسبة السدّ لا العدد وحده.
"""


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", text)


def markdown_to_html(markdown: str) -> str:
    out, table, items = [], [], []

    def flush() -> None:
        if table:
            head, *body = [[c.strip() for c in row.strip("|").split("|")] for row in table if "---" not in row]
            out.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>")
            out.extend("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>" for row in body)
            out.append("</tbody></table>")
            table.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in markdown.splitlines():
        if line.startswith("|"):
            table.append(line)
            continue
        if line.startswith("- "):
            items.append(line[2:])
            continue
        flush()
        image = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if image:
            out.append(f'<figure><img src="{html.escape(image.group(2))}" alt="{html.escape(image.group(1))}"></figure>')
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>{_inline(line[level:].strip())}</h{level}>")
        elif line.startswith(">"):
            out.append(f"<blockquote>{_inline(line[1:].strip())}</blockquote>")
        elif re.match(r"\d+\. ", line):
            out.append(f"<p>{_inline(line)}</p>")
        elif line.strip():
            out.append(f"<p>{_inline(line)}</p>")
    flush()
    return "\n".join(out)


STYLE = """
body { font-family: Tajawal, 'Segoe UI', Tahoma, sans-serif; max-width: 900px; margin: 32px auto; padding: 0 20px; color: #14263a; line-height: 1.8; }
h1 { color: #0f2a43; border-bottom: 4px solid #c9a24a; padding-bottom: 8px; }
h2 { color: #0f2a43; margin-top: 32px; } h3 { color: #1b4468; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.92rem; }
th { background: #0f2a43; color: #fff; } th, td { padding: 6px 10px; border: 1px solid #dbe3ec; text-align: right; }
blockquote { margin: 0; padding: 6px 14px; border-inline-start: 4px solid #c9a24a; background: #f3f6fa; color: #5b6b7c; }
figure { margin: 16px 0; page-break-inside: avoid; } img { max-width: 100%; }
code { background: #f3f6fa; padding: 1px 5px; border-radius: 4px; direction: ltr; unicode-bidi: embed; }
"""


def build_html(markdown: str) -> str:
    return (
        '<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">'
        f"<title>GeoImpact KSA — التقرير التنفيذي</title><style>{STYLE}</style></head>"
        f"<body>{markdown_to_html(markdown)}</body></html>"
    )


def _find_browser() -> str | None:
    return next((path for path in (shutil.which("msedge"), *BROWSERS) if path and Path(path).is_file()), None)


def write_pdf(html_path: Path, pdf_path: Path) -> bool:
    browser = _find_browser()
    if not browser:
        return False
    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", f"--user-data-dir={profile}", "--no-pdf-header-footer",
             f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
            capture_output=True, timeout=120,
        )
    return result.returncode == 0 and pdf_path.is_file()


def build_report(payload: dict, quality: dict, report_dir: Path) -> dict:
    report_dir.mkdir(exist_ok=True)
    markdown = build_markdown(payload, quality)
    md_path, html_path, pdf_path = (report_dir / f"executive_summary.{ext}" for ext in ("md", "html", "pdf"))
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(build_html(markdown), encoding="utf-8")
    return {"md": md_path, "html": html_path, "pdf": pdf_path if write_pdf(html_path, pdf_path) else None}
