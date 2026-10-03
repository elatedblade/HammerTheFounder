import test from "node:test";
import assert from "node:assert/strict";
import { presentOutreachRow, presentOutreachStatus, selectOutreachTotal } from "./outreach-presentation.ts";

test("outreach metric preserves a real total and does not turn missing data into zero", () => {
  assert.equal(selectOutreachTotal({ applications: {}, outreach: { total: 4 }, campaigns: {}, tasks: { open: 0 } }), 4);
  assert.equal(selectOutreachTotal({ applications: {}, outreach: {}, campaigns: {}, tasks: { open: 0 } }), null);
});

test("outreach presentation uses recorded status and strips internal fields", () => {
  assert.equal(presentOutreachStatus("POSITIVE_REPLY"), "Positive reply");
  const row = presentOutreachRow({ id: "1", campaign: "c1", company_name: "Acme", contact_name: "A. Contact", channel: "EMAIL", status: "SENT", sent_at: null, delivered_at: null, bounced_at: null, reply_at: null, follow_up_due_at: null, body: "private", subject: "private", notes: "private", thread_reference: "private", contact: "private" });
  assert.deepEqual(Object.keys(row).sort(), ["bounced_at", "campaign", "channel", "company_name", "contact_name", "delivered_at", "follow_up_due_at", "id", "reply_at", "sent_at", "status"]);
});
