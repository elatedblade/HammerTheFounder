// Hidden confirmations must never retain a previously checked value.
export function checkboxValue(value: unknown, visible = true): boolean {
  return visible && (value === true || value === "true");
}
