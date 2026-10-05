import type { Campaign, ServicePlan } from "../../lib/api";

export function selectedPlan(value: string | null): ServicePlan | null {
  return value === "NORMAL_APPLY" || value === "COLD_APPLY" || value === "FULL_THROTTLE" ? value : null;
}

export function activeCampaigns(campaigns: Campaign[]): Campaign[] {
  return campaigns.filter((campaign) => campaign.status === "ACTIVE");
}

export function supportMailto(value: unknown): string | null {
  if (typeof value !== "string" || value.length > 254) return null;
  if (!/^[A-Za-z0-9.!$'*+_=-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/.test(value)) return null;
  const [local] = value.split("@");
  if (local.length > 64 || local.startsWith(".") || local.endsWith(".") || local.includes("..")) return null;
  return `mailto:${value}`;
}
