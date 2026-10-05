export const applicationStageOptions = [
  { value: "SAVED", label: "Saved" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "UNDER_REVIEW", label: "Under review" },
  { value: "INTERVIEWS", label: "Interviews" },
  { value: "OFFERS", label: "Offers" },
];

export function applicationStageLabel(row: Record<string, unknown>) {
  return applicationStageOptions.find(option => option.value === row.stage)?.label
    ?? String(row.status ?? "Unavailable").toLowerCase().replaceAll("_", " ").replace(/^./, value => value.toUpperCase());
}
