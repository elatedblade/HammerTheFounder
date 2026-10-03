"use client";

import { useRef, useState } from "react";
import { applicationPayload, jobPayload, lookupPath, LOOKUP_PAGE_SIZE } from "./application-helpers";
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
      {!data.length && <p className="empty">No {title.toLowerCase()} match this search. Create a company or job below, or change the search.</p>}
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
  const [company, setCompany] = useState<RecordData | null>(null);
  const [job, setJob] = useState<RecordData | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [mode, setMode] = useState<"application" | "company" | "job">("application");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const saving = useRef(false);
  async function save(action: "company" | "job" | "application") {
    if (saving.current) return;
    saving.current = true; setBusy(true); setError(null);
    try {
      if (action === "company") {
        if (!companyName.trim()) throw new Error("Company name is required.");
        const row = await context.api<RecordData>("companies/", { method: "POST", body: JSON.stringify({ name: companyName.trim() }) });
        setCompany(row); setMode("job");
      } else if (action === "job") {
        if (!company || !jobTitle.trim()) throw new Error("Choose a company and enter a job title.");
        const row = await context.api<RecordData>("jobs/", { method: "POST", body: JSON.stringify(jobPayload({ company: String(company.id), title: jobTitle, location: jobLocation, canonical_url: jobUrl })) });
        setJob(row); setMode("application"); context.refresh();
      } else {
        // The backend validates campaign visibility, job identity and deduplication.
        const payload = applicationPayload({ ...values, job: job ? String(job.id) : "" });
        await context.api("applications/", { method: "POST", body: JSON.stringify(payload) });
        context.refresh(); onDone();
      }
    } catch (cause) { setError(cause); } finally { saving.current = false; setBusy(false); }
  }
  return <form className="mutation-form" aria-label="Create application" onSubmit={(event) => { event.preventDefault(); void save(mode); }}>
    <h3>{mode === "application" ? "Save application record" : mode === "company" ? "Create company" : "Create job"}</h3>
    <p className="muted">Your campaign and application draft stay here while you create dependencies. Saved applications are not sent; record external submission separately.</p>
    <fieldset disabled={busy}>
      {mode === "application" && <>
        <label>Campaign<select required value={values.campaign} onChange={(event) => setValues({ ...values, campaign: event.target.value })}><option value="">Select a visible campaign…</option>{context.lookups.campaigns?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
        <CatalogLookup path="jobs/" title="Jobs" context={context} value={job} onSelect={setJob} />
        <p className="muted">Closed and archived jobs remain labeled; the API decides whether recording is allowed.</p>
        <div className="button-row"><button type="button" className="secondary" onClick={() => { setError(null); setMode("job"); }}>Create a job first</button><button type="button" className="secondary" onClick={() => { setError(null); setMode("company"); }}>Create company</button></div>
        <label>Internal notes<textarea value={values.notes} onChange={(event) => setValues({ ...values, notes: event.target.value })} /></label>
        <label>Source reference<input value={values.source_reference} onChange={(event) => setValues({ ...values, source_reference: event.target.value })} /></label>
      </>}
      {mode === "company" && <label>Company name<input required value={companyName} onChange={(event) => setCompanyName(event.target.value)} /></label>}
      {mode === "job" && <>
        <CatalogLookup path="companies/" title="Companies" context={context} value={company} onSelect={setCompany} />
        <button type="button" className="secondary" onClick={() => setMode("company")}>Create company</button>
        <label>Job title<input required value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} /></label>
        <label>Location<input value={jobLocation} onChange={(event) => setJobLocation(event.target.value)} /></label>
        <label>Canonical job URL<input type="url" value={jobUrl} onChange={(event) => setJobUrl(event.target.value)} /></label>
      </>}
      <ErrorMessage error={error} />
      <div className="button-row"><button type="submit" disabled={busy || (mode === "application" ? !values.campaign || !job : mode === "job" ? !company || !jobTitle.trim() : !companyName.trim())}>{busy ? "Saving…" : mode === "application" ? "Save unsent application" : `Save ${mode}`}</button>
        {mode !== "application" && <button type="button" className="secondary" onClick={() => { setError(null); setMode("application"); }}>Return to application draft</button>}
        <button type="button" className="secondary" onClick={onDone}>Close draft</button>
      </div>
    </fieldset>
  </form>;
}
