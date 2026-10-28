import { h, mount } from "../dom.js";
import { formatNumber, formatPercent } from "../format.js";

export function renderLeaderboard(scope, state, store, thresholds) {
  const rows = scope.regions.filter((region) => !state.tier || region.tier_id === state.tier);
  const [low, mid] = thresholds;

  const items = rows.map((region) =>
    h(
      "li",
      {},
      h(
        "button",
        {
          type: "button",
          class: `lb-row${region.region === state.region ? " is-on" : ""}`,
          style: `--tier:${region.tier_color}`,
          onclick: () => store.set({ region: region.region === state.region ? null : region.region }),
        },
        h("span", { class: "lb-row__rank" }, region.rank),
        h(
          "span",
          { class: "lb-row__body" },
          h("strong", {}, region.region),
          h(
            "span",
            { class: "meter" },
            h("span", { class: "meter__fill", style: `width:${Math.min(region.fill_ratio, 1) * 100}%` }),
            h("span", { class: "meter__mark", style: `inset-inline-start:${low * 100}%` }),
            h("span", { class: "meter__mark", style: `inset-inline-start:${mid * 100}%` })
          ),
          h("small", {}, `تسدّ ${formatPercent(region.fill_ratio)} · الأشد: ${region.worst_domain}`)
        ),
        h("span", { class: "lb-row__need" }, `+${formatNumber(region.needed_total)}`)
      )
    )
  );

  mount("#leaderboard", items.length ? items : h("li", { class: "empty" }, "لا مناطق ضمن هذا الفلتر."));
}
