import test from "node:test";
import assert from "node:assert/strict";
import { bumpRefreshRevision } from "./refresh-revision.ts";

test("refresh generations are monotonic and do not reuse stale resource generations", () => {
  assert.equal(bumpRefreshRevision(0), 1);
  assert.equal(bumpRefreshRevision(41), 42);
});
