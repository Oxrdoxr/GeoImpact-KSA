import { h, mount } from "../dom.js";
import { formatNumber } from "../format.js";

export function renderHeadline(scope, regionSummary) {
  mount("#headline", h("p", {}, regionSummary?.headline ?? scope.headline));
}

export function renderKpis(scope, regionSummary) {
  const { kpis } = scope;
  const selected = regionSummary;
  const cards = [
    {
      label: selected ? "جهة مسجلة في المنطقة" : "جهة مسجلة في النطاق",
      value: formatNumber(selected?.registered ?? kpis.registered),
    },
    {
      label: selected ? "مستوى التوازن في المنطقة" : "مناطق دون التوازن (حرجة أو متوسطة)",
      value: selected ? selected.tier_label : formatNumber(kpis.below_balance),
      tone: selected ? "status" : "red",
      color: selected?.tier_color,
    },
    {
      label: selected ? "جهة مطلوبة في المنطقة" : "جهة مطلوبة لبلوغ التوازن",
      value: formatNumber(selected?.needed_total ?? kpis.needed_total),
      tone: "red",
    },
    {
      label: selected ? "المنطقة المختارة" : "أكثر منطقة حرجًا",
      value: selected?.region ?? kpis.worst_region,
    },
  ];

  mount(
    "#kpis",
    cards.map((card) =>
      h(
        "div",
        { class: `kpi${card.tone ? ` kpi--${card.tone}` : ""}`, style: card.color ? `--tier:${card.color}` : null },
        h("span", { class: "kpi__value" }, card.value),
        h("span", { class: "kpi__label" }, card.label)
      )
    )
  );
}

export function renderFooter(meta) {
  const unclassified = meta.total_records - meta.classified_records;
  mount(
    "#footer",
    h(
      "p",
      {},
      `مؤشر تسجيل مقابل حصة السكان وليس قياسًا للطلب الفعلي. ${formatNumber(unclassified)} جهة غير مصنفة مستبعدة من المقارنة. ` +
        "الصناديق العائلية مجال مستقل وإشرافها مشتق من نوع الكيان. أرقام السكان مقرّبة إلى 0.1 مليون."
    )
  );
}
