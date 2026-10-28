import { loadDashboardData, loadEntities } from "./data.js";
import { createStore, initialState } from "./store.js";
import { renderDetail } from "./views/detail.js";
import { renderEntities } from "./views/entities.js";
import { renderFilters } from "./views/filters.js";
import { renderLeaderboard } from "./views/leaderboard.js";
import { renderMatrix } from "./views/matrix.js";
import { renderMethod } from "./views/method.js";
import { renderShares } from "./views/shares.js";
import { renderFooter, renderHeadline, renderKpis } from "./views/summary.js";

async function start() {
  const [data, entities] = await Promise.all([loadDashboardData(), loadEntities()]);
  const store = createStore(initialState);

  const render = (state) => {
    const scope = data.scopes[state.domain];
    const regionSummary = state.region
      ? scope.regions.find((item) => item.region === state.region)
      : null;
    const region = regionSummary?.region ?? scope.regions[0].region;
    renderFilters(data, state, store);
    renderHeadline(scope, regionSummary);
    renderKpis(scope, regionSummary);
    renderLeaderboard(scope, state, store, data.meta.tier_thresholds);
    renderMatrix(data, scope, state, store);
    renderDetail(data, region, state, store);
    renderShares(scope, state, store);
    renderEntities(entities, state, scope);
  };

  store.subscribe(render);
  renderMethod(data.tiers);
  renderFooter(data.meta);
  render(store.get());

  const dialog = document.querySelector("#method-dialog");
  document.querySelector("#method-button").addEventListener("click", () => dialog.showModal());
  document.querySelector("#method-close").addEventListener("click", () => dialog.close());
  document.querySelector("#print-button").addEventListener("click", () => window.print());
  document.querySelector("#entity-search").addEventListener("input", (event) => store.set({ query: event.target.value }));
}

start().catch((error) => {
  document.body.prepend(Object.assign(document.createElement("p"), { className: "empty", textContent: error.message }));
});
