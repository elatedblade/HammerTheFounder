import test from "node:test";
import assert from "node:assert/strict";
import { applicationStageLabel, applicationStageOptions } from "../src/components/operations/application-stages.ts";
import { applicationStatusOptions, updateApplicationStageAction } from "../src/components/operations/application-helpers.ts";
import { formPayload } from "../src/components/operations/form-payload.ts";
import { resourceQuery } from "../src/components/operations/resource-query.ts";
import { dashboardMetrics } from "../src/components/operations/dashboard-metrics.ts";

test("five stages remain distinct from truthful exception history", () => {
  assert.deepEqual(applicationStageOptions.map(option => option.label), ["Saved", "In progress", "Under review", "Interviews", "Offers"]);
  assert.equal(applicationStageLabel({ stage: "UNDER_REVIEW", status: "SUBMITTED" }), "Under review");
  for (const status of ["REJECTED", "WITHDRAWN", "APPLICATION_FAILED"]) assert.equal(applicationStageLabel({ stage: null, status }), status.toLowerCase().replaceAll("_", " ").replace(/^./, c => c.toUpperCase()));
});
test("editor always offers the same five stages as filters and cards, including Offers", () => {
  assert.deepEqual(applicationStatusOptions(), applicationStageOptions);
  for (const [stage, status] of [["SAVED", "SAVED"], ["IN_PROGRESS", "IN_PROGRESS"], ["OFFERS", "OFFER"]]) {
    const row = { id: "app", stage, status };
    assert.equal(updateApplicationStageAction.when(row), true);
    assert.deepEqual(updateApplicationStageAction.fields(row)[0].options, applicationStageOptions);
    assert.deepEqual(updateApplicationStageAction.initial(row), { stage, submission_confirmed: false });
  }
  assert.equal(updateApplicationStageAction.initial({id: "app", status: "SAVED"}).stage, "");
  assert.equal(updateApplicationStageAction.route, "stage/");
  for (const status of ["REJECTED", "WITHDRAWN", "APPLICATION_FAILED"]) assert.equal(updateApplicationStageAction.when({id: "app", status, stage: null}), false);
});

test("advanced unsent stages require deliberate external submission confirmation", () => {
  const fields = updateApplicationStageAction.fields({ id: "app", stage: "SAVED", status: "SAVED", submitted_at: null });
  const checkbox = fields.find(field => field.name === "submission_confirmed");
  assert.equal(checkbox.type, "checkbox");
  for (const stage of ["UNDER_REVIEW", "INTERVIEWS", "OFFERS"]) {
    assert.equal(checkbox.visibleWhen({stage}), true);
    assert.equal(checkbox.requiredWhen({stage}), true);
    for (const submission_confirmed of [undefined, "", "false", "on", "1"]) {
      assert.throws(() => formPayload(fields, {stage, submission_confirmed}), /Confirm application was submitted externally is required/);
    }
    assert.deepEqual(formPayload(fields, { stage, submission_confirmed: "true", notes: " Confirmed with candidate " }), { stage, submission_confirmed: true, notes: "Confirmed with candidate" });
  }
  for (const stage of ["SAVED", "IN_PROGRESS"]) {
    assert.equal(checkbox.visibleWhen({stage}), false);
    assert.deepEqual(formPayload(fields, { stage }), { stage, submission_confirmed: false, notes: "" });
    assert.deepEqual(formPayload(fields, { stage, submission_confirmed: "true" }), { stage, submission_confirmed: false, notes: "" });
  }
  assert.throws(() => formPayload(fields, {}), /New status is required/);
});

test("already submitted stage updates never reconfirm or rewrite submission history", () => {
  const fields = updateApplicationStageAction.fields({ id: "app", stage: "OFFERS", status: "OFFER", submitted_at: "2026-10-01T12:00:00Z" });
  for (const {value: stage} of applicationStageOptions) {
    assert.deepEqual(formPayload(fields, {stage, submission_confirmed: "true", notes: ""}), { stage, submission_confirmed: false, notes: "" });
  }
});

test("checkbox extension preserves existing form types and validation", () => {
  assert.deepEqual(formPayload([{name: "assigned_to", label: "Operator", nullable: true}, {name: "priority", label: "Priority", type: "number", min: 1, max: 5}, {name: "notes", label: "Notes", type: "textarea"}, {name: "payload", label: "Payload", type: "json"}], {assigned_to: "", priority: "3", notes: " note ", payload: '{"ok":true}'}), {assigned_to: null, priority: 3, notes: "note", payload: {ok: true}});
  assert.throws(() => formPayload([{name: "priority", label: "Priority", type: "number"}], {priority: "2.5"}), /whole number/);
  assert.throws(() => formPayload([{name: "interview_scheduled_at", label: "Interview", type: "datetime-local", future: true}], {interview_scheduled_at: "2000-01-01T12:00"}), /future date/);
});
test("application requests filter stages while unrelated resources retain statuses", () => {
  const resource = {path: "applications/", scoped: true, paginated: true, stageOptions: applicationStageOptions};
  assert.equal(resourceQuery(resource, "campaign", "UNDER_REVIEW", "", 1), "applications/?campaign=campaign&stage=UNDER_REVIEW&limit=100&offset=100");
  assert.ok(!resourceQuery(resource, "", "", "", 0).includes("stage="));
  assert.equal(resourceQuery({path: "outreach/", statusOptions: ["SENT"]}, "", "SENT", "", 0), "outreach/?status=SENT");
});
test("dashboard uses authoritative stages and keeps lifetime submissions separate", () => {
  const result = dashboardMetrics({applications: {submitted: 20, total: 24, stage_counts: {SAVED: 3, IN_PROGRESS: 1, UNDER_REVIEW: 10, INTERVIEWS: 2, OFFERS: 1}}});
  assert.deepEqual(result.primary.slice(0, 5).map(card => card.value), [3, 1, 10, 2, 1]);
  assert.equal(result.submitted, 20);
  assert.ok(result.additional.some(card => card.value === 24));
});
