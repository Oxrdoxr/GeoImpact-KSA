import { h, mount } from "../dom.js";

export function renderMethod(tiers) {
  mount(
    "#method-body",
    h("h2", {}, "كيف نقيس العدالة؟"),
    h("p", {}, "لكل مجال نوزّع عدد جهاته الوطني على المناطق بنسبة سكانها؛ هذه هي الحصة العادلة. الفرق بينها وبين المسجل فعليًا هو الفجوة."),
    h("p", {}, "«نسبة السدّ» لمنطقة تحسب كل مجال حتى حدّ حصته فقط، فلا يُخفي فائضُ مجالٍ عجزَ آخر."),
    h(
      "ul",
      { class: "tier-list" },
      tiers.map((tier) => h("li", { style: `--tier:${tier.color}` }, h("i", { class: "chip__dot" }), h("strong", {}, tier.label), ` · ${tier.range}`))
    )
  );
}
