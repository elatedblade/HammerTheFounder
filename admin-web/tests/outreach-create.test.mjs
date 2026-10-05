import test from "node:test";
import assert from "node:assert/strict";
import { outreachCreateForm, outreachCreatePayload } from "../src/components/operations/outreach-create-fields.ts";

const id = (suffix) => `550e8400-e29b-41d4-a716-44665544000${suffix}`;
const option = (suffix, label) => ({ value: id(suffix), label });
const common = { campaign: id(0), channel: "EMAIL", subject: "Hello", body: "A considered draft", notes: "Internal" };
const serialize = values => JSON.parse(JSON.stringify(outreachCreatePayload(values)));

test("empty lookups start with inline contact and company creation", () => {
  const form = outreachCreateForm({ campaigns: [option(0, "Campaign")] }, "");
  assert.equal(form.initial.campaign, id(0));
  assert.equal(form.initial.contact_mode, "NEW");
  assert.equal(form.initial.company_mode, "NEW");
  const visible = form.fields.filter(field => !field.visibleWhen || field.visibleWhen(form.initial)).map(field => field.name);
  assert.ok(visible.includes("company_name"));
  assert.ok(visible.includes("contact_name"));
  assert.ok(!visible.includes("contact"));
  assert.ok(!visible.includes("company"));
});

test("saved contacts and companies remain reusable without another workspace section", () => {
  const form = outreachCreateForm({ campaigns: [option(0, "Campaign")], contacts: [option(1, "Contact")], companies: [option(2, "Company")] }, "");
  assert.equal(form.initial.contact_mode, "EXISTING");
  assert.equal(form.initial.contact, id(1));
  assert.equal(form.initial.company_mode, "EXISTING");
  assert.equal(form.initial.company, id(2));
  assert.deepEqual(serialize({ ...common, ...form.initial }), { ...common, contact: id(1) });
  const newContact = { ...form.initial, contact_mode: "NEW" };
  assert.ok(form.fields.find(field => field.name === "company").visibleWhen(newContact));
  assert.ok(!form.fields.find(field => field.name === "company_name").visibleWhen(newContact));
});

test("new contacts can reuse a company or create one atomically with the draft", () => {
  const base = { ...common, contact_mode: "NEW", contact_name: "Alex", contact_email: "alex@example.com" };
  assert.deepEqual(serialize({ ...base, company_mode: "EXISTING", company: id(2) }), {
    ...common, company: id(2), contact_data: { name: "Alex", email: "alex@example.com" },
  });
  const payload = serialize({ ...base, company_mode: "NEW", company_name: "Example Ltd", contact: id(1), company: id(2) });
  assert.deepEqual(payload, { ...common, contact_data: { name: "Alex", email: "alex@example.com" }, company_data: { name: "Example Ltd" } });
  assert.ok(!("status" in payload));
  assert.ok(!("sent_at" in payload));
});

test("multiple campaigns require an explicit selection and required fields stay required", () => {
  const form = outreachCreateForm({ campaigns: [option(0, "First"), option(1, "Second")] }, "");
  assert.equal(form.initial.campaign, "");
  for (const name of ["campaign", "body", "contact_name", "company_name"]) {
    assert.equal(form.fields.find(field => field.name === name).required, true);
  }
  assert.equal(outreachCreateForm({}, id(3)).initial.campaign, id(3));
});
