import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { applicationColumns, applicationSubmittedDate, applicationTransitions, canRecordSubmitted, recordSubmittedAction } from "../src/components/operations/application-helpers.ts";

test("application list prioritizes the candidate and keeps one concise submission date", () => {
  assert.deepEqual(applicationColumns, ["candidate_name", "candidate_email", "company_name", "job_title", "status", "submitted_at"]);
  assert.equal(applicationSubmittedDate("2026-10-05T23:59:59.123456Z"), "2026-10-05");
  assert.equal(applicationSubmittedDate("2026-10-05T23:59:59-04:00"), "2026-10-06");
  assert.equal(applicationSubmittedDate(null), "Not recorded");
  assert.equal(applicationSubmittedDate("invalid"), "Unavailable");
});

test("record submitted and the status dropdown share every eligible unsent state", () => {
  const eligible = ["SAVED", "DISCOVERED", "SHORTLISTED", "READY", "IN_PROGRESS"];
  for (const status of Object.keys(applicationTransitions)) {
    const row = { id: "application-id", status, submitted_at: null };
    assert.equal(canRecordSubmitted(row), eligible.includes(status), status);
    assert.equal(recordSubmittedAction.when(row), applicationTransitions[status].includes("SUBMITTED"), status);
    assert.equal(canRecordSubmitted({ ...row, submitted_at: "2026-10-01T12:00:00Z" }), false, `${status} already submitted`);
  }
  assert.equal(canRecordSubmitted({ status: "UNKNOWN" }), false);
});

test("manual submission action requires external confirmation and sends only a transition", () => {
  assert.equal(recordSubmittedAction.label, "Record submitted");
  assert.equal(recordSubmittedAction.route, "transition/");
  assert.deepEqual(recordSubmittedAction.body, { status: "SUBMITTED" });
  assert.deepEqual(recordSubmittedAction.fields.map((field) => field.name), ["notes"]);
  assert.match(recordSubmittedAction.confirm, /already been submitted externally/);
  assert.match(recordSubmittedAction.confirm, /does not send an application/);
  assert.match(recordSubmittedAction.fields[0].help, /Edit record/);
  // Readiness is validated by the API when explicitly recording, not inferred
  // from list DTO fields that may be stale or omit job readiness.
  assert.equal(recordSubmittedAction.when({ id: "id", status: "SAVED", campaign_status: "PAUSED", campaign_plan: "COLD_APPLY" }), true);
});

test("application-specific presentation preserves generic tables and API error handling", async () => {
  const source = await readFile(new URL("../src/components/operations/resource-panel.tsx", import.meta.url), "utf8");
  const table = await readFile(new URL("../src/components/operations/application-table.tsx", import.meta.url), "utf8");
  const resources = await readFile(new URL("../src/components/operations/resources.ts", import.meta.url), "utf8");
  const ui = await readFile(new URL("../src/components/operations/ui.tsx", import.meta.url), "utf8");
  assert.match(source, /resource\.path === "applications\/" \? <ApplicationTable/);
  assert.match(source, /: <RecordTable rows=\{filtered\}/);
  assert.match(resources, /actions: \[recordSubmittedAction/);
  assert.match(resources, /columns: applicationColumns/);
  assert.match(table, /matching application/);
  assert.match(table, /on this page/);
  assert.match(table, /current filters only/);
  assert.match(ui, /catch \(e\) \{ setError\(e\); \}/);
  assert.match(ui, /<ErrorMessage error=\{error\}/);
});
