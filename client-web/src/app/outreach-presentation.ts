import type { Dashboard, Outreach } from "../lib/api";
export function selectOutreachTotal(data: Dashboard): number | null { const value = data.outreach?.total; return typeof value === "number" && Number.isFinite(value) ? value : null; }
export const OUTREACH_STATUS_OPTIONS = [
  { value: "SENT", label: "Sent" },
  { value: "RESPONDED", label: "Responded" },
];
export function presentOutreachStatus(status: string): string {
  if (["SENT", "DELIVERED"].includes(status)) return "Sent";
  if (["RESPONDED", "REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY"].includes(status)) return "Responded";
  return status.toLowerCase().replaceAll("_", " ").replace(/^./, value => value.toUpperCase());
}
export function outreachQuery(campaign: string, stage: string, offset: number) {
  const currentStage = stage === "REPLIED" ? "RESPONDED" : stage;
  return new URLSearchParams({ ...(campaign ? { campaign } : {}), ...(currentStage ? { stage: currentStage } : {}), limit: "50", offset: String(offset) }).toString();
}
export function presentOutreachRow(row: Outreach) { return { id: row.id, campaign: row.campaign, company_name: row.company_name, contact_name: row.contact_name, channel: row.channel, status: row.status, sent_at: row.sent_at, delivered_at: row.delivered_at, bounced_at: row.bounced_at, reply_at: row.reply_at, follow_up_due_at: row.follow_up_due_at }; }
