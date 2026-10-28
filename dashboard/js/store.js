export const ALL = "all";

export function createStore(initial) {
  let state = { ...initial };
  const listeners = [];
  return {
    get: () => state,
    set(patch) {
      state = { ...state, ...patch };
      listeners.forEach((listener) => listener(state));
    },
    subscribe: (listener) => listeners.push(listener),
  };
}

export const initialState = { domain: ALL, tier: null, region: null, query: "" };
