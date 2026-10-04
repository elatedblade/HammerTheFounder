import test from "node:test";
import assert from "node:assert/strict";
import { oneStepApplicationPayload } from "../src/components/operations/application-helpers.ts";

const values = { campaign: "campaign-id", notes: "draft notes", source_reference: "receipt" };
const draft = { company_name: " Acme ", title: " Engineer ", location: "", canonical_url: "" };

test("one-step intake sends exclusively an existing job or an inline job draft", () => {
  assert.deepEqual(oneStepApplicationPayload(values, "job-id", draft), { ...values, job: "job-id" });
  assert.deepEqual(oneStepApplicationPayload(values, null, draft), { ...values, new_job: { ...draft, company_name: "Acme", title: "Engineer" } });
});

test("incomplete intake is rejected before a mutation", () => {
  assert.throws(() => oneStepApplicationPayload({ ...values, campaign: "" }, "job-id", draft), /campaign/);
  assert.throws(() => oneStepApplicationPayload(values, null, { ...draft, company_name: " " }), /company/);
  assert.throws(() => oneStepApplicationPayload(values, null, { ...draft, title: " " }), /title/);
});
