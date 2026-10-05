import test from "node:test";
import assert from "node:assert/strict";
import { candidateOutreachPath } from "../src/components/operations/candidate-history.ts";

test("candidate outreach history uses the scoped paginated endpoint", () => {
  assert.equal(candidateOutreachPath("candidate/42", 0), "outreach/?candidate=candidate%2F42&limit=50&offset=0");
  assert.equal(candidateOutreachPath("abc", 3), "outreach/?candidate=abc&limit=50&offset=150");
});
