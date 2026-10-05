import type { Field } from "./types";
// @ts-expect-error Explicit TS extension supports Node strip-types regression tests.
import { checkboxValue } from "./checkbox-value.ts";

export function formPayload(fields: Field[], values: Record<string, string>): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const field of fields) {
    const visible = !field.visibleWhen || field.visibleWhen(values);
    const required = visible && (field.required || field.requiredWhen?.(values));
    if (field.type === "checkbox") {
      const checked = checkboxValue(values[field.name], visible);
      if (visible && required && !checked) throw new Error(`${field.label} is required.`);
      body[field.name] = checked;
      continue;
    }
    if (!visible) continue;
    const value = values[field.name]?.trim() ?? "";
    if (required && !value) throw new Error(`${field.label} is required.`);
    if (!value && field.nullable) body[field.name] = null;
    else if (field.type === "json") {
      const parsed: unknown = JSON.parse(value || "{}");
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error(`${field.label} must be a JSON object.`);
      body[field.name] = parsed;
    } else if (field.type === "list") {
      const items = value ? value.split(",").map((item) => item.trim()).filter(Boolean) : [];
      if (items.length > 10 || items.some((item) => item.length > 100) || new Set(items).size !== items.length) throw new Error(`${field.label}: use at most ten unique values, each at most 100 characters.`);
      body[field.name] = items;
    } else if (field.type === "number") {
      if (value) {
        const number = Number(value);
        if (!Number.isFinite(number) || (field.min !== undefined && number < field.min) || (field.max !== undefined && number > field.max)) throw new Error(`${field.label} is outside the allowed range.`);
        if (field.name === "priority" && !Number.isInteger(number)) throw new Error("Priority must be a whole number from 1 to 5.");
        body[field.name] = number;
      }
    } else if (field.name === "assigned_to" || field.name === "candidate_id") { if (value) body[field.name] = Number(value); }
    else if (field.type === "datetime-local") { if (value) { const date = new Date(value); if (Number.isNaN(date.valueOf()) || (field.future && date.valueOf() <= Date.now())) throw new Error(`${field.label} must be a future date and time.`); body[field.name] = date.toISOString(); } }
    else body[field.name] = value;
  }
  if (typeof body.expected_ctc_min === "number" && typeof body.expected_ctc_max === "number" && body.expected_ctc_min > body.expected_ctc_max) throw new Error("Minimum expected compensation cannot exceed the maximum.");
  return body;
}
