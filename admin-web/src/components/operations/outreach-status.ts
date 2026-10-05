import type { Option, RecordData } from "./types";

export const outreachDraftStates = ["DRAFT", "TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED", "READY"];
export const outreachStatuses = [...outreachDraftStates, "SENT", "DELIVERED", "REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY", "BOUNCED", "CLOSED", "SUPPRESSED"];
export const outreachFilterStatuses = ["SENT", "RESPONDED"];
export const outreachStageOptions = [{ value: "SENT", label: "Sent" }, { value: "RESPONDED", label: "Responded" }];

export function outreachStatusLabel(status: unknown): string {
  const value = String(status ?? "");
  const labels: Record<string, string> = {
    DRAFT: "Draft", SENT: "Sent", DELIVERED: "Sent", REPLIED: "Responded", RESPONDED: "Responded",
    POSITIVE_REPLY: "Responded", NEGATIVE_REPLY: "Responded",
  };
  return labels[value] ?? (value ? value.toLowerCase().replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase()) : "—");
}

export function outreachStatusOptions(row: RecordData): Option[] {
  const status = String(row.status);
  if (outreachDraftStates.includes(status)) return [{ value: "SENT", label: "Sent" }];
  if (status === "SENT" || status === "DELIVERED") return [{ value: "REPLIED", label: "Responded" }];
  return [];
}
