// @ts-expect-error Explicit TS extension supports Node strip-types regression tests.
import { applicationStageOptions } from "./application-stages.ts";
export type Metrics = Record<string, Record<string, number | Record<string, number>>>;
export function metricValue(metrics: Metrics, group: string, key: string) {
  const value = metrics[group]?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
export function dashboardMetrics(metrics: Metrics) {
  const stages = metrics.applications?.stage_counts;
  const outreachStages = metrics.outreach?.stage_counts;
  const primary = applicationStageOptions.map(({ value, label }) => ({
    label: `${label} applications`,
    value: typeof stages === "object" && typeof stages[value] === "number" && Number.isFinite(stages[value]) ? stages[value] : null,
  }));
  primary.push(
    { label: "Sent outreach", value: typeof outreachStages === "object" ? metricValue({ outreach: outreachStages }, "outreach", "SENT") : metricValue(metrics, "outreach", "sent") },
    { label: "Responded outreach", value: typeof outreachStages === "object" ? metricValue({ outreach: outreachStages }, "outreach", "RESPONDED") : metricValue(metrics, "outreach", metrics.outreach?.replies === undefined ? "replied" : "replies") },
  );
  const additional = Object.entries(metrics).flatMap(([group, values]) => Object.entries(values)
    .filter(([key, value]) => typeof value === "number" && Number.isFinite(value)
      && !(group === "applications" && key === "submitted")
      && !(group === "outreach" && ["sent", "replies", "replied", "sent_lifetime", "replied_lifetime"].includes(key)))
    .map(([key, value]) => ({
      label: (group === "applications" || group === "outreach" ? `${key} ${group}` : `${group} · ${key}`).replaceAll("_", " "),
      value: value as number,
    })));
  return { primary, additional, submitted: metricValue(metrics, "applications", "submitted") };
}
