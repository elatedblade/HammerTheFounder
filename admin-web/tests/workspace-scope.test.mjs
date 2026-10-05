import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { campaignScopeForTab, workspaceTabs } from "../src/components/operations/workspace-tabs.ts";

test("campaign scope is pure and Overview-only", () => {
  assert.equal(campaignScopeForTab("Overview", "campaign-1"), "campaign-1");
  for (const tab of workspaceTabs.filter((tab) => tab !== "Overview")) {
    assert.equal(campaignScopeForTab(tab, "campaign-1"), "");
  }
});

test("workspace registry restores inquiry and notification primary tabs", () => {
  assert.deepEqual(workspaceTabs, ["Overview", "Candidates", "Campaigns", "Applications", "Payments", "Inquiries", "Notifications", "Outreach"]);
});

test("workspace component consumes the tab registry and scope helper", async () => {
  const source = await readFile(new URL("../src/components/operations/workspace.tsx", import.meta.url), "utf8");
  assert.match(source, /workspaceTabs\.map/);
  assert.match(source, /campaignScopeForTab\(tab, campaign\)/);
  assert.match(source, /tab === "Overview" && <div className="workspace-toolbar">/);
  assert.match(source, /campaign: scopedCampaign/);
});

test("workspace renders one Outreach section and retains inline creation dependencies", async () => {
  const source = await readFile(new URL("../src/components/operations/workspace.tsx", import.meta.url), "utf8");
  assert.match(source, /tab === "Outreach" && <ResourcePanel resource=\{outreach\} context=\{context\}/);
  assert.doesNotMatch(source, /resources=\{\[outreach, contacts, suppression, outreachTemplates\]\}/);
  assert.match(source, /paths\.companies = "companies\/"; paths\.contacts = "contacts\/"/);
});
