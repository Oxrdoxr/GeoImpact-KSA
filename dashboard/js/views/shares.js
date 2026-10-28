import { h, mount } from "../dom.js";
import { formatPercent, toPercentWidth } from "../format.js";

export function renderShares(scope, state, store) {
  const rows = scope.regions.filter(
    (region) =>
      (!state.region || region.region === state.region) &&
      (!state.tier || region.tier_id === state.tier)
  );
  const shareList = h(
    "ul",
    { class: `shares${state.region ? " shares--single" : ""}` },
    rows.map((region) =>
      h(
        "li",
        {},
        h(
          "button",
          {
            type: "button",
            class: `share-row${region.region === state.region ? " is-on" : ""}`,
            onclick: () => store.set({ region: region.region }),
          },
          h("span", { class: "share-row__name" }, region.region),
          h(
            "span",
            { class: "share-row__bars" },
            h("span", { class: "bar bar--registered", style: `width:${toPercentWidth(region.registered_share, scope.max_share)}` }),
            h("span", { class: "bar bar--population", style: `width:${toPercentWidth(region.population_share, scope.max_share)}` })
          ),
          h("span", { class: "share-row__nums" }, `${formatPercent(region.registered_share)} / ${formatPercent(region.population_share)}`)
        )
      )
    )
  );
  mount(
    "#shares",
    shareList
  );
}
