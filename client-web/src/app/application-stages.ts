export const applicationStageOptions = [
  { value: "SAVED", label: "Saved" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "UNDER_REVIEW", label: "Under review" },
  { value: "INTERVIEWS", label: "Interviews" },
  { value: "OFFERS", label: "Offers" },
] as const;
export type ApplicationStage = typeof applicationStageOptions[number]["value"];

export function applicationStageLabel(row: { stage?: unknown; status?: unknown }) {
  return applicationStageOptions.find(option => option.value === row.stage)?.label
    ?? String(row.status ?? "Unavailable").toLowerCase().replaceAll("_", " ").replace(/^./, value => value.toUpperCase());
}

export function applicationQuery(campaign: string, stage: string, offset: number) {
  return new URLSearchParams({ ...(campaign ? { campaign } : {}), ...(stage ? { stage } : {}), limit: "50", offset: String(offset) }).toString();
}
