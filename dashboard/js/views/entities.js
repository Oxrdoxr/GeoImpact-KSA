import { h, mount } from "../dom.js";
import { formatNumber } from "../format.js";
import { ALL } from "../store.js";

const MAX_RESULTS = 40;

export function renderEntities(entities, state, scope) {
  const query = state.query.trim();
  const regionTiers = new Map(scope.regions.map((region) => [region.region, region.tier_id]));
  const matches = entities.filter(
    (entity) =>
      (!state.region || entity.region === state.region) &&
      (state.domain === ALL || entity.domain === state.domain) &&
      (!state.tier || regionTiers.get(entity.region) === state.tier) &&
      (!query || entity.name.includes(query) || entity.id === query)
  );

  const place = state.region ?? "كل المناطق";
  const domain = state.domain === ALL ? "كل المجالات" : state.domain;
  mount("#entities-title", `الكيانات · ${place} · ${domain} (${formatNumber(matches.length)})`);

  const items = matches.slice(0, MAX_RESULTS).map((entity) =>
    h(
      "li",
      {},
      h("strong", {}, entity.name),
      h("span", {}, [entity.type, entity.domain, entity.supervisor].filter(Boolean).join(" · ")),
      h("small", {}, `${entity.region} · ${entity.id}`)
    )
  );
  const visibleCount = Math.min(matches.length, MAX_RESULTS);
  const resultList = items.length
    ? [h("li", { class: "results__count" }, `عرض ${formatNumber(visibleCount)} من ${formatNumber(matches.length)} نتيجة`), ...items]
    : [h("li", { class: "empty" }, "لا نتائج مطابقة.")];
  mount("#entities", resultList);
}
