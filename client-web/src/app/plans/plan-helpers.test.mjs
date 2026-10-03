import assert from "node:assert/strict";
import test from "node:test";
import { activeCampaigns, supportMailto } from "./plan-helpers.ts";

test("activeCampaigns excludes every non-active lifecycle state", () => {
  const campaigns = ["DRAFT", "ONBOARDING", "READY", "ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"].map((status, index) => ({ id: String(index), plan: "NORMAL_APPLY", status }));
  assert.deepEqual(activeCampaigns(campaigns).map((campaign) => campaign.status), ["ACTIVE"]);
});

test("supportMailto only creates a plain recipient mailto", () => {
  assert.equal(supportMailto("help@example.com"), "mailto:help@example.com");
  assert.equal(supportMailto("help@example.com?bcc=evil@example.com"), null);
  assert.equal(supportMailto("help@example.com\r\nBcc: evil@example.com"), null);
  assert.equal(supportMailto("help@example"), null);
});
