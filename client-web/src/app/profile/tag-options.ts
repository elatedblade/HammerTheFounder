export const MAX_TAG_ITEMS = 10;
export const MAX_TAG_ITEM_LENGTH = 100;
export const MAX_VISIBLE_TAG_OPTIONS = 50;

export type TagOption = { value: string; custom: boolean };

export function tagInputIssue(values: readonly string[], rawValue: string): string | null {
  const value = rawValue.trim();
  if (!value) return null;
  if (value.length > MAX_TAG_ITEM_LENGTH) return `Use ${MAX_TAG_ITEM_LENGTH} characters or fewer for each entry.`;
  if (values.some((existing) => existing.trim().toLowerCase() === value.toLowerCase())) return "This entry is already added.";
  if (values.length >= MAX_TAG_ITEMS) return `You can add up to ${MAX_TAG_ITEMS} entries. Remove one to add another.`;
  return null;
}

// Keep the exact entry, including commas, and never rewrite existing saved values.
export function appendTagValue(values: string[], rawValue: string): string[] {
  const value = rawValue.trim();
  if (!value || tagInputIssue(values, value)) return values;
  return [...values, value];
}

export function getTagOptions(query: string, values: readonly string[], suggestions: readonly string[]): {
  options: TagOption[];
  matchingCount: number;
} {
  if (values.length >= MAX_TAG_ITEMS) return { options: [], matchingCount: 0 };
  const normalizedQuery = query.trim().toLowerCase();
  const selected = new Set(values.map((value) => value.trim().toLowerCase()));
  const seen = new Set<string>();
  const matching = suggestions.filter((suggestion) => {
    const normalized = suggestion.trim().toLowerCase();
    if (!normalized || suggestion.length > MAX_TAG_ITEM_LENGTH || selected.has(normalized) || seen.has(normalized)) return false;
    seen.add(normalized);
    return !normalizedQuery || normalized.includes(normalizedQuery);
  });
  // An exact match remains reachable even when a broad query has more than 50 results.
  const exactIndex = matching.findIndex((suggestion) => suggestion.trim().toLowerCase() === normalizedQuery);
  if (exactIndex > 0) matching.unshift(...matching.splice(exactIndex, 1));
  const custom = normalizedQuery && exactIndex === -1 && !tagInputIssue(values, query)
    ? [{ value: query.trim(), custom: true }]
    : [];
  return {
    options: [...custom, ...matching.slice(0, MAX_VISIBLE_TAG_OPTIONS - custom.length).map((value) => ({ value, custom: false }))],
    matchingCount: matching.length,
  };
}
