import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("lifetime submission totals are not rendered in admin or customer overview", async () => {
  const admin = await readFile(new URL("../src/components/operations/dashboard.tsx", import.meta.url), "utf8");
  const customer = await readFile(new URL("../../client-web/src/app/candidate-progress.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(admin, /presentation\.submitted|Submitted applications \(lifetime\)/);
  assert.doesNotMatch(customer, /metrics\.submitted|Lifetime submissions/);
  const ui = await readFile(new URL("../src/components/operations/ui.tsx", import.meta.url), "utf8");
  assert.match(ui, /columns\.filter\(column => column !== "applications_submitted"\)/);
  assert.match(ui, /key !== "applications_submitted"/);
});
