import type { Dashboard, Outreach } from "../lib/api";
export function selectOutreachTotal(data: Dashboard): number | null { const value = data.outreach?.total; return typeof value === "number" && Number.isFinite(value) ? value : null; }
export function presentOutreachStatus(status: string): string { return status.toLowerCase().replaceAll("_", " ").replace(/^./, value => value.toUpperCase()); }
export function presentOutreachRow(row: Outreach) { return { id: row.id, campaign: row.campaign, company_name: row.company_name, contact_name: row.contact_name, channel: row.channel, status: row.status, sent_at: row.sent_at, delivered_at: row.delivered_at, bounced_at: row.bounced_at, reply_at: row.reply_at, follow_up_due_at: row.follow_up_due_at }; }
