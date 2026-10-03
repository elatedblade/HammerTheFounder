import test from "node:test";
import assert from "node:assert/strict";
import { getLifecyclePresentation } from "./lifecycle-presentation.ts";

const campaign = (status) => ({ status, plan: "NORMAL_APPLY" });
test("active campaign wins over missing inquiry/profile and never asks to choose a plan", () => {
  const result = getLifecyclePresentation({ campaigns: [campaign("ACTIVE")], inquiry: null, profile: null });
  assert.equal(result.kind, "active");
  assert.equal(result.showChoosePlan, false);
});
test("loading and errors are not interpreted as no campaigns", () => {
  assert.equal(getLifecyclePresentation({ campaignsLoading: true }).kind, "loading");
  assert.equal(getLifecyclePresentation({ campaignsError: true }).kind, "error");
  assert.equal(getLifecyclePresentation({ campaigns: null }).showChoosePlan, false);
});
test("ready and paused campaigns have lifecycle-specific copy", () => {
  assert.equal(getLifecyclePresentation({ campaigns: [campaign("READY")] }).kind, "ready");
  assert.equal(getLifecyclePresentation({ campaigns: [campaign("PAUSED")] }).kind, "paused");
  assert.equal(getLifecyclePresentation({ campaigns: [campaign("PAUSED")] }).showChoosePlan, false);
});
test("only a genuinely empty, settled campaign response offers plan acquisition", () => {
  const result = getLifecyclePresentation({ campaigns: [], inquiry: null, profile: null });
  assert.equal(result.kind, "none");
  assert.equal(result.showChoosePlan, true);
});
