import { h, mount } from "../dom.js";
import { ALL } from "../store.js";

export function renderMatrix(data, scope, state, store) {
  const cells = new Map(data.matrix.map((row) => [`${row.region}|${row.category}`, row]));
  const colors = Object.fromEntries(data.tiers.map((tier) => [tier.id, tier.color]));

  const header = h(
    "tr",
    {},
    h("th", { scope: "col" }, "المنطقة"),
    data.domains.map((item) =>
      h(
        "th",
        { scope: "col", class: item.domain === state.domain ? "is-on" : "" },
        h("button", { type: "button", onclick: () => store.set({ domain: item.domain === state.domain ? ALL : item.domain }) }, item.domain)
      )
    )
  );

  const visibleRegions = state.region
    ? scope.regions.filter((region) => region.region === state.region)
    : scope.regions;
  const rows = visibleRegions.map((region) =>
    h(
      "tr",
      { class: region.region === state.region ? "is-on" : "" },
      h(
        "th",
        { scope: "row" },
        h("button", { type: "button", onclick: () => store.set({ region: region.region }) }, region.region)
      ),
      data.domains.map((item) => {
        const cell = cells.get(`${region.region}|${item.domain}`);
        const dimmed = state.tier && region.tier_id !== state.tier;
        return h(
          "td",
          { class: dimmed ? "is-dim" : "" },
          h(
            "button",
            {
              type: "button",
              class: "cell",
              style: `--tier:${colors[cell.tier_id]}`,
              title: `${cell.actual_count} من ${cell.expected_count}`,
              onclick: () => store.set({ region: region.region, domain: item.domain }),
            },
            cell.estimated_gap || "·"
          )
        );
      })
    )
  );

  mount("#matrix", h("thead", {}, header), h("tbody", {}, rows));
}
