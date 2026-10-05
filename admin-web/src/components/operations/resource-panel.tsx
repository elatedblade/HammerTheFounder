"use client";

import { useEffect, useState } from "react";
import { Details, ErrorMessage, MutationForm, RecordTable, useRecords } from "./ui";
import { isAdmin, type Action, type RecordData, type Resource, type WorkspaceContext } from "./types";
import ApplicationTable from "./application-table";
import OutreachCreate from "./outreach-create";
import OutreachTable from "./outreach-table";
import { outreachStatusLabel } from "./outreach-status";
import { resourceQuery } from "./resource-query";

export default function ResourcePanel({ resource, context }: { resource: Resource; context: WorkspaceContext }) {
  const { api, revision, campaign, lookups, refresh, user } = context;
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");
  const pageSize = resource.pageSize ?? 100;
  const path = resourceQuery(resource, campaign, status, query, page);
  const { data, loading, error } = useRecords(api, path, revision);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<"create" | "edit" | null>(null);
  const [action, setAction] = useState<Action | null>(null);
  const detailKey = `${selectedId}:${revision}`;
  const [detailResult, setDetailResult] = useState<{ key: string; data: RecordData | null; error: unknown }>({ key: "", data: null, error: null });
  const detail = detailResult.key === detailKey ? detailResult.data : null;
  const detailError = detailResult.key === detailKey ? detailResult.error : null;
  const [notice, setNotice] = useState("");
  const row = data.find((item) => String(item.id) === selectedId);
  const filtered = resource.path === "jobs/" ? data : data.filter((item) => resource.columns.some((column) => String(item[column] ?? "").toLowerCase().includes(query.toLowerCase())) || (resource.path === "outreach/" && outreachStatusLabel(item.status).toLowerCase().includes(query.toLowerCase())));
  useEffect(() => {
    if (!resource.fetchDetail || !selectedId) return;
    let active = true;
    api<RecordData>(`${resource.path}${selectedId}/`).then((data) => { if (active) setDetailResult({ key: detailKey, data, error: null }); }).catch((error: unknown) => { if (active) setDetailResult({ key: detailKey, data: null, error }); });
    return () => { active = false; };
  }, [api, resource.path, resource.fetchDetail, selectedId, detailKey]);
  const select = (item: RecordData) => { setSelectedId(String(item.id)); setMode(null); setAction(null); setNotice(""); };
  const mutate = async (endpoint: string, body: Record<string, unknown>, method = "POST") => { setNotice(""); const result = await api<RecordData>(endpoint, { method, body: JSON.stringify(body) }); setNotice("Change accepted by the API. Refreshing the saved records…"); refresh(); return result; };
  return <section className="panel"><div className="panel-heading"><div><h2>{resource.title}</h2>{resource.description && <p className="muted">{resource.description}</p>}</div><div className="button-row"><button className="secondary" onClick={refresh} disabled={loading}>Refresh</button>{resource.fields && <button onClick={() => { setMode("create"); setAction(null); }}>{resource.path === "outreach/" ? "Create outreach" : "Create"}</button>}</div></div>
    {resource.stageOptions && <label className="search-label">Status (all pages)<select value={status} onChange={(event) => { setStatus(event.target.value); setPage(0); setSelectedId(null); setMode(null); setAction(null); }}><option value="">{resource.path === "outreach/" ? "All outreach and history" : "All applications and history"}</option>{resource.stageOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>}
     {resource.statusOptions && <label className="search-label">Status (all pages)<select value={status} onChange={(event) => { setStatus(event.target.value); setPage(0); setSelectedId(null); setMode(null); setAction(null); }}><option value="">All states</option>{resource.statusOptions.map((value) => <option key={value} value={value}>{resource.path === "outreach/" ? outreachStatusLabel(value) : value.replaceAll("_", " ")}</option>)}</select></label>}<label className="search-label">{resource.path === "jobs/" ? "Search available jobs" : "Filter loaded records"}<input type="search" value={query} onChange={(event) => { setQuery(event.target.value); if (resource.path === "jobs/") { setPage(0); setSelectedId(null); setMode(null); setAction(null); } }} placeholder={`Search ${resource.title.toLowerCase()}`} /></label>{resource.path === "jobs/" && !loading && !error && <label className="search-label">Matching jobs<select value={data.some((item) => String(item.id) === selectedId) ? selectedId ?? "" : ""} onChange={(event) => { const item = data.find((entry) => String(entry.id) === event.target.value); if (item) select(item); else setSelectedId(null); }}><option value="">{data.length ? "Select a job…" : "No matching jobs"}</option>{data.map((item) => <option key={String(item.id)} value={String(item.id)}>{[item.title, item.company_name, item.location, item.status].filter(Boolean).join(" · ")}</option>)}</select></label>}<ErrorMessage error={error} />{notice && <p className="success" role="status">{notice}</p>}{loading ? <p className="empty" role="status">Loading {resource.title.toLowerCase()}…</p> : !error && (resource.path === "applications/" ? <ApplicationTable rows={filtered} selected={selectedId ?? undefined} onSelect={select} /> : resource.path === "outreach/" ? <OutreachTable rows={filtered} columns={resource.columns} selected={selectedId ?? undefined} onSelect={select} /> : <RecordTable rows={filtered} columns={resource.columns} selected={selectedId ?? undefined} onSelect={select} />)}
     {resource.paginated && <div className="button-row"><button className="secondary" disabled={page === 0 || loading} onClick={() => { setPage((value) => value - 1); setSelectedId(null); setAction(null); setMode(null); }}>Previous page</button><span className="muted">Page {page + 1} · up to {pageSize} records per page</span><button className="secondary" disabled={loading || data.length < pageSize} onClick={() => { setPage((value) => value + 1); setSelectedId(null); setAction(null); setMode(null); }}>Next page</button></div>}
     {mode === "create" && resource.path === "outreach/" ? <OutreachCreate context={context} onCancel={() => setMode(null)} onCreated={(record) => { setSelectedId(String(record.id)); setMode(null); setNotice("Outreach draft saved. No message was sent."); }} /> : mode === "create" && resource.fields && <MutationForm key={`create-${resource.path}-${campaign}`} title={`Create ${resource.title.toLowerCase()}`} fields={resource.fields} initial={{ campaign, priority: 3, currency: "INR" }} lookups={lookups} confirm={resource.createConfirm} submitLabel="Create record" onCancel={() => setMode(null)} onSubmit={async (body) => { const result = await mutate(resource.path, body); setSelectedId(String(result.id)); setMode(null); }} />}
    {row && <div className="record-detail"><div className="panel-heading"><h3>Record details</h3><button className="secondary" onClick={() => { setSelectedId(null); setAction(null); setMode(null); }}>Close details</button></div>{resource.fetchDetail ? <><ErrorMessage error={detailError} />{detail ? <Details row={detail} /> : !detailError && <p role="status">Loading status and result…</p>}</> : <Details row={row} />}<div className="button-row">{resource.editFields && (!resource.adminEdit || isAdmin(user)) && <button className="secondary" onClick={() => { setMode("edit"); setAction(null); }}>Edit record</button>}{resource.actions?.filter((item) => (!item.admin || isAdmin(user)) && (!item.when || item.when(row))).map((item) => <button key={item.label} className="secondary" onClick={() => { setAction(item); setMode(null); }}>{item.label}</button>)}</div>
      {mode === "edit" && resource.editFields && <MutationForm key={`edit-${row.id}`} title={`Edit ${resource.title.toLowerCase()}`} fields={typeof resource.editFields === "function" ? resource.editFields(row) : resource.editFields} initial={row} lookups={lookups} confirm="Save these edits? This updates the operational record, including any changed settings or assignment." onCancel={() => setMode(null)} onSubmit={(body) => mutate(`${resource.path}${row.id}/`, body, "PATCH")} />}
      {action && (resource.path !== "outreach/" || !action.when || action.when(row)) && <MutationForm key={`${row.id}-${action.label}-${row.status}`} title={action.label} fields={typeof action.fields === "function" ? action.fields(row) : action.fields ?? []} lookups={lookups} initial={{ notes: row.notes, interview_scheduled_at: row.interview_scheduled_at, ...action.initial?.(row) }} confirm={action.confirm ?? `Confirm ${action.label.toLowerCase()}? This updates the operational record.`} submitLabel={action.label} onCancel={() => setAction(null)} onSubmit={async (body) => { await mutate(`${resource.path}${row.id}/${action.route}`, { ...body, ...action.body }, action.method); setAction(null); }} />}
    </div>}
  </section>;
}
