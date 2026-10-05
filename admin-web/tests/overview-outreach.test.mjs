import test from "node:test";
import assert from "node:assert/strict";
import { dashboardMetrics } from "../src/components/operations/dashboard-metrics.ts";
import { outreachFilterStatuses, outreachStatusLabel } from "../src/components/operations/outreach-status.ts";
import { resourceQuery } from "../src/components/operations/resource-query.ts";
import { outreachStageOptions } from "../src/components/operations/outreach-status.ts";

test("overview distinguishes applications from outreach using authoritative totals", () => {
  const result = dashboardMetrics({ applications: { stage_counts: { SAVED: 3, IN_PROGRESS: 2, UNDER_REVIEW: 1, INTERVIEWS: 0, OFFERS: 0 } }, outreach: { sent: 7, replies: 2, replied: 2, total: 10 } });
  assert.deepEqual(result.primary, [
    { label: "Saved applications", value: 3 },
    { label: "In progress applications", value: 2 },
    { label: "Under review applications", value: 1 },
    { label: "Interviews applications", value: 0 },
    { label: "Offers applications", value: 0 },
    { label: "Sent outreach", value: 7 },
    { label: "Responded outreach", value: 2 },
  ]);
  assert.deepEqual(result.additional, [{ label: "total outreach", value: 10 }]);
});

test("outreach cards retain zero, unavailable and legacy reply totals", () => {
  for (const [outreach, expected] of [
    [{ sent: 0, replies: 0, replied: 5 }, [0, 0]],
    [{ sent: 3, replied: 1 }, [3, 1]],
    [{}, [null, null]],
    [{ sent: Infinity, replies: NaN }, [null, null]],
  ]) {
    assert.deepEqual(dashboardMetrics({ outreach }).primary.slice(-2).map(card => card.value), expected);
  }
});

test("outreach filters expose only grouped Sent and Responded stages", () => {
  assert.deepEqual(outreachFilterStatuses, ["SENT", "RESPONDED"]);
  assert.deepEqual(outreachFilterStatuses.map(outreachStatusLabel), ["Sent", "Responded"]);
  const resource = { path: "outreach/", scoped: true, paginated: true, stageOptions: outreachStageOptions };
  for (const stage of ["SENT", "RESPONDED", "REPLIED"]) {
    const query = resourceQuery(resource, "campaign", stage, "", 1);
    assert.equal(query, `outreach/?campaign=campaign&stage=${stage === "REPLIED" ? "RESPONDED" : stage}&limit=100&offset=100`);
    assert.equal(new URLSearchParams(query.split("?")[1]).has("status"), false);
  }
});

test("current outreach stages override legacy counters and hide lifetime duplicates", () => {
  const result = dashboardMetrics({ applications: { stage_counts: { SAVED: 3, IN_PROGRESS: 2, UNDER_REVIEW: 1, INTERVIEWS: 0, OFFERS: 0 } }, outreach: { stage_counts: { SENT: 0, RESPONDED: 1 }, sent: 0, replies: 1, replied: 1, sent_lifetime: 1, replied_lifetime: 1, total: 1 } });
  assert.deepEqual(result.primary.slice(-2), [{ label: "Sent outreach", value: 0 }, { label: "Responded outreach", value: 1 }]);
  assert.deepEqual(result.primary.slice(0, 5).map(card => card.value), [3, 2, 1, 0, 0]);
  assert.deepEqual(result.additional, [{ label: "total outreach", value: 1 }]);
  assert.deepEqual(dashboardMetrics({ outreach: { stage_counts: { SENT: 0, RESPONDED: 1 }, sent: 9, replies: 9 } }).primary.slice(-2).map(card => card.value), [0, 1]);
});
