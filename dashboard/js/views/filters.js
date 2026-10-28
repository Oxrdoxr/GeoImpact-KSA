import { h, mount } from "../dom.js";
import { ALL, initialState } from "../store.js";

export function renderFilters(data, state, store) {
  const select = h(
    "select",
    { class: "select", "aria-label": "المجال", onchange: (event) => store.set({ domain: event.target.value }) },
    h("option", { value: ALL }, "كل المجالات"),
    data.domains.map((item) =>
      h("option", { value: item.domain, selected: item.domain === state.domain }, item.domain)
    )
  );
  select.value = state.domain;

  const chips = data.tiers.map((tier) =>
    h(
      "button",
      {
        type: "button",
        class: `chip${state.tier === tier.id ? " is-on" : ""}`,
        style: `--tier:${tier.color}`,
        title: tier.range,
        onclick: () => store.set({ tier: state.tier === tier.id ? null : tier.id, region: null }),
      },
      h("i", { class: "chip__dot" }),
      tier.label
    )
  );

  const dirty = state.domain !== ALL || state.tier || state.region || state.query;
  const reset = h(
    "button",
    { type: "button", class: "btn btn--ghost", disabled: dirty ? false : "disabled", onclick: () => store.set(initialState) },
    "إعادة ضبط"
  );

  mount("#filters", select, h("div", { class: "chips" }, chips), reset);
}
