import test from "node:test";
import assert from "node:assert/strict";
import { getLifecyclePresentation } from "./lifecycle-presentation.ts";

const campaign = (status) => ({ status, plan: "NORMAL_APPLY" });
test("active headlines use friendly public plan names", () => {
  for (const [plan, name] of [["NORMAL_APPLY", "Normal Apply"], ["COLD_APPLY", "Better Apply"], ["FULL_THROTTLE", "Full Throttle"]]) {
    assert.equal(getLifecyclePresentation({ campaigns: [{ status: "ACTIVE", plan }] }).headline, `${name} · Active`);
  }
});
test("active campaign wins over historical and setup records", () => {
  const result = getLifecyclePresentation({ campaigns: [campaign("COMPLETED"), campaign("READY"), { status: "ACTIVE", plan: "COLD_APPLY" }] });
  assert.equal(result.headline, "Better Apply · Active");
  assert.equal(result.showPlansLink, true);
});
test("unsettled campaign requests suppress stale records and acquisition actions", () => {
  for (const state of [{ campaignsLoading: true }, { campaignsError: true }]) {
    const result = getLifecyclePresentation({ campaigns: [campaign("ACTIVE")], ...state });
    assert.notEqual(result.kind, "active");
    assert.equal(result.showChoosePlan, false);
    assert.equal(result.showPlansLink, false);
  }
});
test("historical records and saved inquiries preserve their next steps", () => {
  for (const status of ["COMPLETED", "CANCELLED"]) {
    const result = getLifecyclePresentation({ campaigns: [campaign(status)] });
    assert.equal(result.kind, "historical");
    assert.equal(result.showChoosePlan, false);
  }
  for (const status of ["OPEN", "CONTACTED", "CONVERTED"]) {
    assert.equal(getLifecyclePresentation({ campaigns: [], inquiry: { status } }).showChoosePlan, false);
  }
  assert.equal(getLifecyclePresentation({ campaigns: [], profile: { basics_complete: false } }).showProfileAction, true);
});
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
