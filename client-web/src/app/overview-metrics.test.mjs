import test from "node:test";
import assert from "node:assert/strict";
import { selectOverviewMetrics } from "./overview-metrics.ts";
import { applicationStageLabel, applicationStageOptions, applicationQuery } from "./application-stages.ts";

test("overview exposes Sent and Responded outreach totals without duplicates", () => {
  const result = selectOverviewMetrics({ applications: {}, outreach: { sent: 7, replies: 2, replied: 2, total: 10 }, campaigns: {}, tasks: {} });
  assert.deepEqual(result.primary.slice(-2), [{ label: "Sent outreach", value: 7 }, { label: "Responded outreach", value: 2 }]);
  assert.deepEqual(result.additional, [{ label: "Total outreach", value: 10 }]);
});

test("outreach overview preserves zero and unavailable and supports legacy totals", () => {
  for (const [outreach, expected] of [
    [{ sent: 0, replies: 0, replied: 5 }, [0, 0]],
    [{ sent: 4, replied: 1 }, [4, 1]],
    [{}, [null, null]],
    [{ sent: Infinity, replies: NaN }, [null, null]],
  ]) {
    assert.deepEqual(selectOverviewMetrics({ applications: {}, campaigns: {}, tasks: {}, outreach }).primary.slice(-2).map(card => card.value), expected);
  }
});

test("current outreach stages override legacy counters and hide lifetime duplicates", () => {
  const result = selectOverviewMetrics({ applications: { stage_counts: { SAVED: 3, IN_PROGRESS: 2, UNDER_REVIEW: 1, INTERVIEWS: 0, OFFERS: 0 } }, outreach: { stage_counts: { SENT: 0, RESPONDED: 1 }, sent: 0, replies: 1, replied: 1, sent_lifetime: 1, replied_lifetime: 1, total: 1 }, campaigns: {}, tasks: {} });
  assert.deepEqual(result.primary.slice(-2), [{ label: "Sent outreach", value: 0 }, { label: "Responded outreach", value: 1 }]);
  assert.deepEqual(result.primary.slice(0, 5).map(card => card.value), [3, 2, 1, 0, 0]);
  assert.deepEqual(result.additional, [{ label: "Total outreach", value: 1 }]);
  assert.deepEqual(selectOverviewMetrics({ applications: {}, outreach: { stage_counts: { SENT: 0, RESPONDED: 1 }, sent: 9, replies: 9 }, campaigns: {}, tasks: {} }).primary.slice(-2).map(card => card.value), [0, 1]);
});

test("application filters send stages and preserve exception outcome labels", () => {
  assert.deepEqual(applicationStageOptions.map(option => option.label), ["Saved", "In progress", "Under review", "Interviews", "Offers"]);
  assert.equal(applicationQuery("campaign", "UNDER_REVIEW", 50), "campaign=campaign&stage=UNDER_REVIEW&limit=50&offset=50");
  assert.equal(applicationQuery("", "", 0), "limit=50&offset=0");
  assert.equal(applicationStageLabel({ stage: "UNDER_REVIEW", status: "SUBMITTED" }), "Under review");
  assert.equal(applicationStageLabel({ stage: null, status: "REJECTED" }), "Rejected");
  assert.equal(applicationStageLabel({ stage: null, status: "WITHDRAWN" }), "Withdrawn");
  assert.equal(applicationStageLabel({ stage: null, status: "APPLICATION_FAILED" }), "Application failed");
});

test("selects exactly the five authoritative application metrics", () => {
  const result = selectOverviewMetrics({ applications: { total: 8, stage_counts: { SAVED: 8, IN_PROGRESS: 2, UNDER_REVIEW: 3, INTERVIEWS: 1, OFFERS: 4 }, submitted: 7 }, outreach: {}, campaigns: {}, tasks: { open: 0 } });
  assert.deepEqual(result.primary.slice(0, 5).map(({ label, value }) => [label, value]), [
    ["Saved applications", 8], ["In progress applications", 2], ["Under review applications", 3], ["Interviews applications", 1], ["Offers applications", 4],
  ]);
  assert.equal(result.submitted.value, 7);
});

test("preserves other numeric dashboard metrics without treating missing values as zero", () => {
  const result = selectOverviewMetrics({ applications: { total: 2, stage_counts: { UNDER_REVIEW: 1, INTERVIEWS: 0, OFFERS: 0 }, rejected: 5 }, outreach: { total: 9, replies: 2 }, campaigns: { active: 1 }, tasks: { open: 3 } });
  assert.equal(result.primary[1].value, null);
  assert.deepEqual(result.additional.map(({ label, value }) => [label, value]), [
    ["Total applications", 2], ["Rejected applications", 5], ["Total outreach", 9], ["Campaigns · Active campaigns", 1], ["Tasks · Open tasks", 3],
  ]);
});
