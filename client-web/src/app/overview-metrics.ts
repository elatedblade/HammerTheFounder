import type { Dashboard } from "../lib/api";
// @ts-expect-error Explicit TS extension supports Node strip-types regression tests.
import { applicationStageOptions } from "./application-stages.ts";

export type OverviewMetric = { label: string; value: number | null };

const primaryApplicationMetrics = new Set(["submitted", "stage_counts"]);
const primaryOutreachMetrics = new Set(["sent", "replies", "replied", "stage_counts", "sent_lifetime", "replied_lifetime"]);

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
  const outreach = data.outreach ?? {};
  const primary: OverviewMetric[] = applicationStageOptions.map(({ value, label }) => ({ label: `${label} applications`, value: numericValue(applications.stage_counts?.[value]) }));
  primary.push(
    { label: "Sent outreach", value: numericValue(outreach.stage_counts ? outreach.stage_counts.SENT : outreach.sent) },
    { label: "Responded outreach", value: numericValue(outreach.stage_counts ? outreach.stage_counts.RESPONDED : outreach.replies ?? outreach.replied) },
  );
  const submitted: OverviewMetric = { label: "Submitted applications (lifetime)", value: numericValue(applications.submitted) };

  const additional: OverviewMetric[] = [];
  for (const [section, values] of Object.entries(data)) {
    if (!values || typeof values !== "object" || Array.isArray(values)) continue;
    for (const [key, value] of Object.entries(values)) {
      if (section === "applications" && primaryApplicationMetrics.has(key)) continue;
      if (section === "outreach" && primaryOutreachMetrics.has(key)) continue;
      if (typeof value !== "number" || !Number.isFinite(value)) continue;
      const label = section === "applications" || section === "outreach"
        ? `${labelFor(key)} ${section}`
        : `${labelFor(section)} · ${labelFor(key)}`;
      additional.push({ label, value });
    }
  }
  return { primary, submitted, additional };
}
