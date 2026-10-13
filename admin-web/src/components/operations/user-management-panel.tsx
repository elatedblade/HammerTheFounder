"use client";

import { useEffect, useState } from "react";

import type { ApiClient, ManagedUser } from "../../lib/api";
import { ErrorMessage } from "./ui";

const editableRoles = ["ADMIN", "CLIENT"] as const;
type EditableRole = (typeof editableRoles)[number];

function isEditableRole(role: string): role is EditableRole {
  return editableRoles.includes(role as EditableRole);
}

function roleOptions(role: ManagedUser["role"]) {
  return [
    ...(role === "SUPERADMIN" ? [{ value: role, label: "SUPERADMIN (current)", disabled: true }] : []),
    ...(role === "OPERATOR" ? [{ value: role, label: "OPERATOR (current)", disabled: true }] : []),
    ...editableRoles.map((value) => ({ value, label: value, disabled: false })),
  ];
}

export default function UserManagementPanel({ api }: { api: ApiClient }) {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [draftRoles, setDraftRoles] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [saveError, setSaveError] = useState<unknown>(null);
  const [savedId, setSavedId] = useState<number | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    let active = true;
    api<ManagedUser[]>("admin/users/")
      .then((rows) => {
        if (!active) return;
        setUsers(rows);
        setDraftRoles(Object.fromEntries(rows.map((user) => [String(user.id), user.role])));
      })
      .catch((requestError: unknown) => {
        if (active) setError(requestError);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [api, requestVersion]);

  function retry() {
    setLoading(true);
    setError(null);
    setRequestVersion((version) => version + 1);
  }

  async function saveRole(user: ManagedUser) {
    const role = draftRoles[String(user.id)];
    if (!isEditableRole(role) || role === user.role) return;

    setSavingId(user.id);
    setSaveError(null);
    setSavedId(null);
    try {
      const updated = await api<ManagedUser>(`admin/users/${user.id}/role/`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      setUsers((current) => current.map((currentUser) => currentUser.id === updated.id ? updated : currentUser));
      setDraftRoles((current) => ({ ...current, [String(updated.id)]: updated.role }));
      setSavedId(updated.id);
    } catch (requestError: unknown) {
      setSaveError(requestError);
    } finally {
      setSavingId(null);
    }
  }

  return <section className="panel user-management" aria-labelledby="user-management-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">Superadmin controls</p>
        <h2 id="user-management-title">User management</h2>
        <p className="muted">Review local roles and assign ADMIN or CLIENT access. The API remains the authorization authority.</p>
      </div>
    </div>
    {loading && <p className="empty" role="status">Loading users…</p>}
    {!loading && error !== null && <><ErrorMessage error={error} /><p><button className="secondary" onClick={retry}>Retry</button></p></>}
    {!loading && !error && users.length === 0 && <p className="empty">No active Clerk users are available.</p>}
    {!loading && !error && users.length > 0 && <div className="table-scroll"><table>
      <caption className="sr-only">Managed users and local roles</caption>
      <thead><tr><th scope="col">Email</th><th scope="col">Current role</th><th scope="col">Status</th><th scope="col">Assign role</th><th scope="col">Action</th></tr></thead>
      <tbody>{users.map((user) => {
        const draftRole = draftRoles[String(user.id)] ?? user.role;
        const changed = draftRole !== user.role;
        const options = roleOptions(user.role);
        return <tr key={user.id}>
          <td><span className="cell-content">{user.email || "—"}</span></td>
          <td><span className="badge">{user.role}</span></td>
          <td><span className="badge">{user.status}</span></td>
          <td><label className="sr-only" htmlFor={`managed-user-role-${user.id}`}>Role for {user.email || `user ${user.id}`}</label><select id={`managed-user-role-${user.id}`} value={draftRole} onChange={(event) => { setSavedId(null); setDraftRoles((current) => ({ ...current, [String(user.id)]: event.target.value })); }}>
            {options.map((option) => <option key={option.value} value={option.value} disabled={option.disabled}>{option.label}</option>)}
          </select></td>
          <td><button onClick={() => saveRole(user)} disabled={!changed || savingId === user.id}>{savingId === user.id ? "Saving…" : "Save role"}</button>{savedId === user.id && <span className="success" role="status">Saved</span>}</td>
        </tr>;
      })}</tbody>
    </table></div>}
    {saveError !== null && <ErrorMessage error={saveError} />}
  </section>;
}
