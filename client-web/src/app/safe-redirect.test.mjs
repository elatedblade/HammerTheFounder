import assert from "node:assert/strict";
import test from "node:test";

import { authCounterpartUrl, isSafeWhatsAppUrl, safeCustomerRedirect } from "./safe-redirect.ts";

test("safeCustomerRedirect keeps only customer destinations and valid plans", () => {
  assert.equal(safeCustomerRedirect("https://evil.example/phish"), "/dashboard");
  assert.equal(safeCustomerRedirect("/dashboard?plan=NORMAL_APPLY"), "/plans?plan=NORMAL_APPLY");
  assert.equal(safeCustomerRedirect("/dashboard?plan=NOPE"), "/dashboard");
  assert.equal(authCounterpartUrl("/sign-up", "/dashboard?plan=COLD_APPLY"), "/sign-up?redirect_url=%2Fplans%3Fplan%3DCOLD_APPLY");
});

test("isSafeWhatsAppUrl accepts only trusted wa.me https URLs", () => {
  assert.equal(isSafeWhatsAppUrl("https://wa.me/15551234567?text=hello"), true);
  assert.equal(isSafeWhatsAppUrl("http://wa.me/15551234567"), false);
  assert.equal(isSafeWhatsAppUrl("https://wa.me.evil.test/15551234567"), false);
  assert.equal(isSafeWhatsAppUrl("https://wa.me/"), false);
  assert.equal(isSafeWhatsAppUrl("https://wa.me/not-a-phone"), false);
  assert.equal(isSafeWhatsAppUrl("https://wa.me:9443/15551234567"), false);
  assert.equal(isSafeWhatsAppUrl("https://user:password@wa.me/15551234567"), false);
  assert.equal(safeCustomerRedirect("//evil.example/dashboard?plan=COLD_APPLY"), "/dashboard");
  assert.equal(safeCustomerRedirect("/profile?token=private"), "/profile");
});
