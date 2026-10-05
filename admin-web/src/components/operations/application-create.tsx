"use client";

import { useRef, useState } from "react";
import { oneStepApplicationPayload, lookupPath, LOOKUP_PAGE_SIZE } from "./application-helpers";
import { ErrorMessage, useRecords } from "./ui";
import type { RecordData, WorkspaceContext } from "./types";

function CatalogLookup({ path, title, context, value, onSelect }: {
  path: string; title: string; context: WorkspaceContext; value: RecordData | null; onSelect: (row: RecordData) => void;
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [retry, setRetry] = useState(0);
  const { data, error, loading } = useRecords(context.api, lookupPath(path, query, page), context.revision + retry);
  return <fieldset><legend>{title}</legend>
    <label>Search {title.toLowerCase()}<input type="search" value={query} onChange={(event) => { setQuery(event.target.value); setPage(0); }} /></label>
    <ErrorMessage error={error} />{Boolean(error) && <button type="button" className="secondary" onClick={() => setRetry((n) => n + 1)}>Retry {title.toLowerCase()}</button>}
    {loading ? <p role="status">Loading {title.toLowerCase()}…</p> : !error && <>
      {!data.length && <p className="empty">No {title.toLowerCase()} match this search. Choose New job above, or change the search.</p>}
      <label>Choose {title.toLowerCase()}<select value={value ? String(value.id) : ""} onChange={(event) => { const row = data.find((item) => String(item.id) === event.target.value); if (row) onSelect(row); }}>
        <option value="">Select…</option>
        {value && !data.some((row) => row.id === value.id) && <option value={String(value.id)}>{String(value.title ?? value.name)} (selected)</option>}
        {data.map((row) => <option key={String(row.id)} value={String(row.id)}>{[row.title ?? row.name, row.company_name, row.location, row.status].filter(Boolean).join(" · ")}</option>)}
      </select></label>
      <div className="button-row"><button type="button" className="secondary" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous {title.toLowerCase()}</button><span>Page {page + 1}</span><button type="button" className="secondary" disabled={data.length < LOOKUP_PAGE_SIZE} onClick={() => setPage(page + 1)}>Next {title.toLowerCase()}</button></div>
    </>}
  </fieldset>;
}

export default function ApplicationCreate({ context, onDone }: { context: WorkspaceContext; onDone: () => void }) {
  const [values, setValues] = useState({ campaign: context.campaign, notes: "", source_reference: "" });
  const [job, setJob] = useState<RecordData | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [mode, setMode] = useState<"existing" | "new">("existing");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const saving = useRef(false);
  async function save() {
    if (saving.current) return;
    saving.current = true; setBusy(true); setError(null);
    try {
      const payload = oneStepApplicationPayload(values, mode === "existing" && job ? String(job.id) : null, { company_name: companyName, title: jobTitle, location: jobLocation, canonical_url: jobUrl });
      await context.api("applications/create/", { method: "POST", body: JSON.stringify(payload) });
      context.refresh(); onDone();
    } catch (cause) { setError(cause); } finally { saving.current = false; setBusy(false); }
  }
  return <form className="mutation-form" aria-label="Create application" onSubmit={(event) => { event.preventDefault(); void save(); }}>
    <h3>Save application record</h3>
    <p className="muted">Select an existing job or enter a new job below. One save creates any missing records. This does not send an application.</p>
    <fieldset disabled={busy}>
      <label>Campaign<select required value={values.campaign} onChange={(event) => setValues({ ...values, campaign: event.target.value })}><option value="">Select a visible campaign…</option>{context.lookups.campaigns?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
      <label>Job selection<select value={mode} onChange={(event) => { setMode(event.target.value as "existing" | "new"); setError(null); }}><option value="existing">Existing job</option><option value="new">New job</option></select></label>
      {mode === "existing" ? <CatalogLookup path="jobs/" title="Jobs" context={context} value={job} onSelect={setJob} /> : <>
        <label>Company name<input required value={companyName} onChange={(event) => setCompanyName(event.target.value)} /></label>
        <label>Job title<input required value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} /></label>
        <label>Location (optional)<input value={jobLocation} onChange={(event) => setJobLocation(event.target.value)} /></label>
        <label>Job URL (optional)<input type="url" value={jobUrl} onChange={(event) => setJobUrl(event.target.value)} /></label>
      </>}
      <label>Internal notes<textarea value={values.notes} onChange={(event) => setValues({ ...values, notes: event.target.value })} /></label>
      <label>Source reference<input value={values.source_reference} onChange={(event) => setValues({ ...values, source_reference: event.target.value })} /></label>
      <ErrorMessage error={error} />
      <div className="button-row"><button type="submit" disabled={busy || !values.campaign || (mode === "existing" ? !job : !companyName.trim() || !jobTitle.trim())}>{busy ? "Saving…" : "Save unsent application"}</button><button type="button" className="secondary" onClick={onDone}>Close draft</button></div>
    </fieldset>
  </form>;
}
