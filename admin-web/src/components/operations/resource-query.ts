import type { Resource } from "./types";

export function resourceQuery(resource: Resource, campaign: string, status: string, query: string, page: number) {
  const params = new URLSearchParams();
  if (resource.scoped && campaign) params.set("campaign", campaign);
  if (status && resource.stageOptions) params.set("stage", resource.path === "outreach/" && status === "REPLIED" ? "RESPONDED" : status);
  else if (status && resource.statusOptions) params.set("status", status);
  if (resource.path === "jobs/" && query.trim()) params.set("q", query.trim());
  if (resource.paginated) { const size = resource.pageSize ?? 100; params.set("limit", String(size)); params.set("offset", String(page * size)); }
  return `${resource.path}${params.size ? `?${params.toString()}` : ""}`;
}
