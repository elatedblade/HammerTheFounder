import type { Dashboard } from "../lib/api";

export type OverviewMetric = { label: string; value: number | null };

const primaryApplicationMetrics = new Set(["total", "in_progress", "in_review", "interviews", "offers"]);

function labelFor(key: string) {
  const labels: Record<string, string> = {
    total: "Total",
    submitted: "Submitted",
    in_review: "In review",
    in_progress: "In progress",
    interviews: "Interviews",
    interview_scheduled: "Interviews scheduled",
    upcoming_interviews: "Upcoming interviews",
    positive_replies: "Positive replies",
    active: "Active campaigns",
    open: "Open tasks",
  };
  return labels[key] ?? key.toLowerCase().replaceAll("_", " ").replace(/^./, (value) => value.toUpperCase());
}

function numericValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function selectOverviewMetrics(data: Dashboard) {
  const applications = data.applications ?? {};
  const primary: OverviewMetric[] = [
    { label: "Total applications", value: numericValue(applications.total) },
    { label: "In progress", value: numericValue(applications.in_progress) },
    { label: "Under review", value: numericValue(applications.in_review) },
    { label: "Interviews", value: numericValue(applications.interviews) },
    { label: "Offers", value: numericValue(applications.offers) },
  ];

  const additional: OverviewMetric[] = [];
  for (const [section, values] of Object.entries(data)) {
    if (!values || typeof values !== "object" || Array.isArray(values)) continue;
    for (const [key, value] of Object.entries(values)) {
      if (section === "applications" && primaryApplicationMetrics.has(key)) continue;
      if (typeof value !== "number" || !Number.isFinite(value)) continue;
      additional.push({ label: section === "applications" ? labelFor(key) : `${labelFor(section)} · ${labelFor(key)}`, value });
    }
  }
  return { primary, additional };
}
