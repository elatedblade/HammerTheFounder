import test from "node:test";
import assert from "node:assert/strict";
import { selectOverviewMetrics } from "./overview-metrics.ts";

test("selects exactly the five authoritative application metrics", () => {
  const result = selectOverviewMetrics({ applications: { total: 8, in_progress: 2, in_review: 3, interviews: 1, offers: 4, submitted: 7 }, outreach: {}, campaigns: {}, tasks: { open: 0 } });
  assert.deepEqual(result.primary.map(({ label, value }) => [label, value]), [
    ["Total applications", 8], ["In progress", 2], ["Under review", 3], ["Interviews", 1], ["Offers", 4],
  ]);
});

test("preserves other numeric dashboard metrics without treating missing values as zero", () => {
  const result = selectOverviewMetrics({ applications: { total: 2, in_progress: undefined, in_review: 1, interviews: 0, offers: 0, rejected: 5 }, outreach: { total: 9, replies: 2 }, campaigns: { active: 1 }, tasks: { open: 3 } });
  assert.equal(result.primary[1].value, null);
  assert.deepEqual(result.additional.map(({ label, value }) => [label, value]), [
    ["Rejected", 5], ["Outreach · Total", 9], ["Outreach · Replies", 2], ["Campaigns · Active campaigns", 1], ["Tasks · Open tasks", 3],
  ]);
});
