"use client";

import { useState } from "react";
import { Details, ErrorMessage, RecordTable, useRecords } from "./ui";
import type { RecordData, WorkspaceContext } from "./types";

export default function ReviewTasks({ context, entityType }: { context: WorkspaceContext; entityType: "applications.application" | "outreach.outreach" }) {
  const path = `admin/tasks/?limit=100${context.campaign ? `&campaign=${encodeURIComponent(context.campaign)}` : ""}`;
  const { data, loading, error } = useRecords(context.api, path, context.revision);
  const [selected, setSelected] = useState<RecordData | null>(null);
  const rows = data.filter((row) => { const payload = row.payload_json; return payload !== null && typeof payload === "object" && "entity_type" in payload && payload.entity_type === entityType; });
  const current = rows.find((row) => row.id === selected?.id);
  return <section className="panel related-tasks"><div className="panel-heading"><div><h2>Human review tasks</h2><p className="muted">Real server-generated tasks for this workflow and campaign scope, within the first 100 queue records. Use Tasks to claim, complete or browse the full queue. Creating a record, scheduling an interview, requesting review or recording failure can add tasks.</p></div><button className="secondary" onClick={context.refresh} disabled={loading}>Refresh tasks</button></div><ErrorMessage error={error} />{loading ? <p role="status">Loading review tasks…</p> : !error && <RecordTable rows={rows} columns={["task_type", "priority", "status", "assigned_to", "payload_json", "created_at"]} selected={current ? String(current.id) : undefined} onSelect={setSelected} />}{current && <div className="record-detail"><h3>Review task source reference</h3><Details row={current} /><button className="secondary" onClick={() => setSelected(null)}>Close task details</button></div>}</section>;
}
