import test from "node:test";
import assert from "node:assert/strict";
import { OUTREACH_STATUS_OPTIONS, outreachQuery, presentOutreachRow, presentOutreachStatus, selectOutreachTotal } from "./outreach-presentation.ts";
test("manual outreach status uses the same Sent and Responded labels as admin", () => {
  assert.equal(presentOutreachStatus("SENT"), "Sent");
  assert.equal(presentOutreachStatus("REPLIED"), "Responded");
  assert.equal(presentOutreachStatus("DRAFT"), "Draft");
  assert.equal(presentOutreachStatus("DELIVERED"), "Sent");
  for (const status of ["POSITIVE_REPLY", "NEGATIVE_REPLY"]) assert.equal(presentOutreachStatus(status), "Responded");
  for (const [status, label] of [["BOUNCED", "Bounced"], ["CLOSED", "Closed"], ["SUPPRESSED", "Suppressed"]]) assert.equal(presentOutreachStatus(status), label);
});
test("outreach metric preserves missing as unavailable", () => { assert.equal(selectOutreachTotal({applications:{}, outreach:{total:2}, campaigns:{}, tasks:{open:0}}), 2); assert.equal(selectOutreachTotal({applications:{}, outreach:{}, campaigns:{}, tasks:{open:0}}), null); });
test("outreach presentation excludes internal fields and preserves history timestamps", () => { const row = presentOutreachRow({id:"1",campaign:"c",company_name:"Acme",contact_name:"A",channel:"EMAIL",status:"POSITIVE_REPLY",sent_at:"2026-10-01",delivered_at:"2026-10-02",bounced_at:null,reply_at:"2026-10-03",follow_up_due_at:null,subject:"x",body:"x",notes:"x",thread_reference:"x",contact:"x"}); assert.equal("body" in row, false); assert.equal("contact" in row, false); assert.equal(row.status, "POSITIVE_REPLY"); assert.equal(row.sent_at, "2026-10-01"); assert.equal(row.delivered_at, "2026-10-02"); assert.equal(row.reply_at, "2026-10-03"); });
test("outreach filters send grouped stages and migrate the old reply filter", () => {
  assert.deepEqual(OUTREACH_STATUS_OPTIONS, [{ value: "SENT", label: "Sent" }, { value: "RESPONDED", label: "Responded" }]);
  for (const stage of ["SENT", "RESPONDED", "REPLIED"]) {
    assert.equal(outreachQuery("campaign", stage, 50), `campaign=campaign&stage=${stage === "REPLIED" ? "RESPONDED" : stage}&limit=50&offset=50`);
  }
  assert.equal(outreachQuery("", "", 0), "limit=50&offset=0");
});
