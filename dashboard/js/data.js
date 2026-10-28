const DATA_URL = "../outputs/dashboard_data.json";
const ENTITIES_URL = "../outputs/entities.json";

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`تعذّر تحميل ${url} (${response.status})`);
  return response.json();
}

export const loadDashboardData = () => fetchJson(DATA_URL);

let entitiesPromise;
export function loadEntities() {
  entitiesPromise ??= fetchJson(ENTITIES_URL);
  return entitiesPromise;
}
