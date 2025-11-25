export const formatNumber = (num: number, decimals = 2): string =>
  num.toFixed(decimals).replace(/\.00$/, "");

export const validatePositive = (value: number, field: string): string | null => {
  if (value <= 0) return `${field} має бути більшим за 0`;
  return null;
};
