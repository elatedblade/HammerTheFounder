import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("user management is gated by the local SUPERADMIN role", async () => {
  const source = await readFile(new URL("../src/components/operations/workspace.tsx", import.meta.url), "utf8");
  assert.match(source, /user\.role === "SUPERADMIN"/);
  assert.match(source, /tab === "Users" && canManageUsers/);
  assert.match(source, /canManageUsers && <button/);
});

test("user management uses the protected list and role mutation endpoints", async () => {
  const source = await readFile(new URL("../src/components/operations/user-management-panel.tsx", import.meta.url), "utf8");
  assert.match(source, /api<ManagedUser\[\]\>\("admin\/users\/"\)/);
  assert.match(source, /`admin\/users\/\$\{user\.id\}\/role\/`/);
  assert.match(source, /JSON\.stringify\(\{ role \}\)/);
  assert.match(source, /const editableRoles = \["ADMIN", "CLIENT"\]/);
  assert.doesNotMatch(source, /editableRoles = .*SUPERADMIN/);
});
