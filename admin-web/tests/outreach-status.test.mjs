import test from "node:test";
import assert from "node:assert/strict";
import { outreachStatusOptions, outreachStatusLabel, outreachDraftStates } from "../src/components/operations/outreach-status.ts";

test("outreach records Sent without replaying preparation statuses", () => {
  for (const status of outreachDraftStates) {
    assert.deepEqual(outreachStatusOptions({ id: "record", status }), [{ value: "SENT", label: "Sent" }]);
  }
});
test("only sent or delivered outreach can be marked Responded", () => {
  for (const status of ["SENT", "DELIVERED"]) {
    assert.deepEqual(outreachStatusOptions({ id: "record", status }), [{ value: "REPLIED", label: "Responded" }]);
  }
  for (const status of ["REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY", "SUPPRESSED", "CLOSED", "BOUNCED"]) {
    assert.deepEqual(outreachStatusOptions({ id: "record", status }), []);
  }
  assert.equal(outreachStatusLabel("SENT"), "Sent");
  assert.equal(outreachStatusLabel("REPLIED"), "Responded");
  assert.equal(outreachStatusLabel("DELIVERED"), "Sent");
  for (const status of ["POSITIVE_REPLY", "NEGATIVE_REPLY"]) assert.equal(outreachStatusLabel(status), "Responded");
  for (const [status, label] of [["BOUNCED", "Bounced"], ["CLOSED", "Closed"], ["SUPPRESSED", "Suppressed"]]) assert.equal(outreachStatusLabel(status), label);
});
