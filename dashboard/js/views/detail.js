import { h, mount } from "../dom.js";
import { formatDecimal, formatNumber, toPercentWidth } from "../format.js";

export function renderDetail(data, regionName, state, store) {
  const rows = data.region_details[regionName];
  const colors = Object.fromEntries(data.tiers.map((tier) => [tier.id, tier.color]));
  const maxValue = Math.max(...rows.map((row) => Math.max(row.actual, row.expected)));
  const scaleMax = Math.max(50, Math.ceil(maxValue / 50) * 50);
  const ticks = Array.from({ length: 5 }, (_, index) => (scaleMax * index) / 4);

  mount("#detail-title", `${regionName} · الفعلي مقابل الحصة العادلة`);
  mount(
    "#detail",
    h(
      "div",
      { class: "detail-chart-scroll" },
      h(
        "div",
        { class: "detail-chart" },
        h(
          "div",
          { class: "detail-chart__axis", "aria-label": "عدد الجهات" },
          ticks.map((value, index) =>
            h(
              "span",
              { class: "detail-chart__tick", style: `bottom:${index * 25}%` },
              formatDecimal(value)
            )
          )
        ),
        h(
          "div",
          { class: "detail-chart__plot" },
          h(
            "div",
            { class: "detail-chart__grid", "aria-hidden": "true" },
            ticks.map((_, index) =>
              h("span", { class: "detail-chart__gridline", style: `bottom:${index * 25}%` })
            )
          ),
          h(
            "div",
            { class: "detail-chart__columns" },
            rows.map((row) =>
              h(
                "button",
                {
                  type: "button",
                  class: `detail-column${row.domain === state.domain ? " is-on" : ""}`,
                  title: `${row.domain}: المسجل ${formatNumber(row.actual)}، الحصة العادلة ${formatDecimal(row.expected)}`,
                  onclick: () => store.set({ domain: row.domain === state.domain ? "all" : row.domain }),
                },
                h(
                  "span",
                  { class: "detail-column__plot" },
                  h(
                    "span",
                    { class: "detail-column__bars" },
                    h("span", {
                      class: "detail-column__expected",
                      style: `height:${toPercentWidth(row.expected, scaleMax)}`,
                    }),
                    h("span", {
                      class: "detail-column__actual",
                      style: `--tier:${colors[row.tier_id]};height:${toPercentWidth(row.actual, scaleMax)}`,
                    })
                  )
                ),
                h("span", { class: "detail-column__name" }, row.domain),
                h("span", { class: "detail-column__values" }, `${formatNumber(row.actual)} / ${formatDecimal(row.expected)}`)
              )
            )
          )
        )
      )
    )
  );
}
