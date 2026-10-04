import test from "node:test";
import assert from "node:assert/strict";
import { bumpRefreshRevision } from "./refresh-revision.ts";
test("refresh revision advances", () => assert.equal(bumpRefreshRevision(3), 4));
