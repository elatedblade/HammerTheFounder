import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { applicationPayload, jobPayload, lookupPath } from "../src/components/operations/application-helpers.ts";

test("UUID identities survive application and dependent job serialization", () => {
  const campaign = "550e8400-e29b-41d4-a716-446655440000";
  const job = "550e8400-e29b-41d4-a716-446655440001";
  const company = "550e8400-e29b-41d4-a716-446655440002";
  const payload = JSON.parse(JSON.stringify(applicationPayload({ campaign, job, notes: "", source_reference: "" })));
  assert.equal(payload.campaign, campaign);
  assert.equal(payload.job, job);
  assert.equal(jobPayload({ company, title: " Engineer ", location: "", canonical_url: "" }).company, company);
  assert.throws(() => applicationPayload({ campaign, job: "", notes: "", source_reference: "" }));
  assert.equal(lookupPath("jobs/", "a&b", 1), "jobs/?q=a%26b&limit=50&offset=50");
});

const read = (name) => readFile(new URL(`../src/components/operations/${name}`, import.meta.url), "utf8");

test("application creation preserves dependent-flow safeguards", async () => {
  const source = await read("application-create.tsx");
  assert.match(source, /applicationPayload/);
  assert.match(source, /saving\.current/);
  assert.match(source, /jobs\/\"/);
  assert.match(source, /companies\/\"/);
  assert.match(source, /context\.refresh\(\); onDone\(\)/);
  assert.match(source, /Return to application draft/);
});

test("payments use paged array requests and inquiries are a primary workspace tab", async () => {
  const resources = await read("resources.ts");
  const campaigns = await read("campaigns-panel.tsx");
  const workspace = await read("workspace.tsx");
  assert.match(resources, /billing\/payments\//);
  assert.match(resources, /paginated: true, pageSize: 200/);
  assert.doesNotMatch(campaigns, /inquiries/);
  assert.match(workspace, /workspaceTabs/);
  assert.match(workspace, /tab === "Inquiries"/);
  assert.match(workspace, /tab === "Notifications" && <ResourceGroup resources=\{\[notifications, notificationTemplates\]\}/);
});

test("outreach primary tab reuses manual outreach resources", async () => {
  const resources = await read("resources.ts");
  const workspace = await read("workspace.tsx");
  assert.match(resources, /export const outreach:/);
  assert.match(resources, /export const contacts:/);
  assert.match(resources, /export const suppression:/);
  assert.match(resources, /export const outreachTemplates:/);
  assert.match(workspace, /tab === "Outreach" && <ResourceGroup resources=\{\[outreach, contacts, suppression, outreachTemplates\]\}/);
  assert.match(resources, /This does not send a message\./);
  assert.match(resources, /Creating a template never sends outreach\./);
});
