const number = new Intl.NumberFormat("ar-SA", { numberingSystem: "latn" });
const decimal = new Intl.NumberFormat("ar-SA", { numberingSystem: "latn", maximumFractionDigits: 1 });

export const formatNumber = (value) => number.format(value);
export const formatDecimal = (value) => decimal.format(value);
export const formatPercent = (ratio) => `${number.format(Math.round(ratio * 100))}%`;
export const toPercentWidth = (value, max) => `${max ? (value / max) * 100 : 0}%`;
