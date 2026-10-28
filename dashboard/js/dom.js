export function h(tag, props = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === false || value == null) continue;
    if (key === "class") element.className = value;
    else if (key.startsWith("on")) element.addEventListener(key.slice(2), value);
    else element.setAttribute(key, value);
  }
  element.append(...children.flat().filter((child) => child != null && child !== false));
  return element;
}

export function mount(selector, ...nodes) {
  const target = document.querySelector(selector);
  target.replaceChildren(...nodes.flat());
  return target;
}
