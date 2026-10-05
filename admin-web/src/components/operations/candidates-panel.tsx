"use client";
import { useEffect, useState } from "react";
import { Details, ErrorMessage, MutationForm, RecordTable, useRecords } from "./ui";
import { display, type Field, type RecordData, type WorkspaceContext } from "./types";
import ParsedResumeText from "./parsed-resume-text";
import { outreachStatusLabel } from "./outreach-status";
import { candidateOutreachPath } from "./candidate-history";

const profileFields: Field[] = [
  { name: "full_name", label: "Full name", required: true }, { name: "headline", label: "Headline" }, { name: "location", label: "Location", required: true },
  { name: "experience_summary", label: "Experience summary", type: "textarea", required: true }, { name: "target_roles", label: "Target roles", type: "list" }, { name: "preferred_locations", label: "Preferred locations", type: "list" }, { name: "target_industries", label: "Target industries", type: "list" }, { name: "remote_preference", label: "Remote preference", type: "select", options: ["UNSPECIFIED", "ONSITE", "HYBRID", "REMOTE", "FLEXIBLE"], required: true }, { name: "expected_ctc_min", label: "Minimum expected compensation", type: "number", nullable: true, min: 0 }, { name: "expected_ctc_max", label: "Maximum expected compensation", type: "number", nullable: true, min: 0 }, { name: "work_authorization", label: "Work authorization" }, { name: "sponsorship_requirement", label: "Sponsorship requirement" }, { name: "notice_period", label: "Notice period" },
];

function useCandidateHistory(api: WorkspaceContext["api"], path: string, revision: number) {
  const [retry, setRetry] = useState(0);
  const key = `${path}:${revision}:${retry}`;
  const [result, setResult] = useState<{ key: string; data: RecordData[]; error: unknown }>({ key: "", data: [], error: null });
  useEffect(() => {
    let active = true;
    api<RecordData[]>(path).then((data) => { if (active) setResult({ key, data, error: null }); }).catch((error: unknown) => { if (active) setResult({ key, data: [], error }); });
    return () => { active = false; };
  }, [api, key, path]);
  return { data: result.key === key ? result.data : [], error: result.key === key ? result.error : null, loading: result.key !== key, retry: () => setRetry((value) => value + 1) };
}

function CandidateDetail({ id, context }: { id: string; context: WorkspaceContext }) {
  const { api, revision, refresh, lookups } = context;
  const key = `${id}:${revision}`;
  const [result, setResult] = useState<{ key: string; profile: RecordData | null; error: unknown }>({ key: "", profile: null, error: null });
  const profile = result.key === key ? result.profile : null;
  const profileError = result.key === key ? result.error : null;
  const resumes = useRecords(api, `admin/candidates/${id}/resumes/`, revision);
  const [applicationPage, setApplicationPage] = useState(0); const [outreachPage, setOutreachPage] = useState(0); const [paymentPage, setPaymentPage] = useState(0);
  const applications = useRecords(api, `applications/?candidate=${encodeURIComponent(id)}&limit=50&offset=${applicationPage * 50}`, revision);
  const outreach = useCandidateHistory(api, candidateOutreachPath(id, outreachPage), revision);
  const payments = useRecords(api, `billing/payments/?candidate=${encodeURIComponent(id)}&limit=50&offset=${paymentPage * 50}`, revision);
  const [editing, setEditing] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [download, setDownload] = useState<{ url: string; expires_in: number } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const campaignLabel = (row: RecordData) => { const id = String(row.campaign ?? ""); return String(row.campaign_name ?? context.lookups.campaigns?.find((option) => option.value === id)?.label ?? (id ? `Campaign ${id}` : "Unassigned")); };
  const applicationRows = applications.data.map((row) => ({ ...row, campaign_display: campaignLabel(row) }));
  const outreachRows = outreach.data.map((row) => ({ ...row, status: outreachStatusLabel(row.status), campaign_display: campaignLabel(row) }));
  const paymentRows = payments.data.map((row) => ({ ...row, campaign_display: campaignLabel(row) }));
  useEffect(() => { let active = true; api<RecordData>(`admin/candidates/${id}/`).then((value) => { if (active) setResult({ key, profile: value, error: null }); }).catch((cause: unknown) => { if (active) setResult({ key, profile: null, error: cause }); }); return () => { active = false; }; }, [api, id, key]);
  async function resumeAction(resume: RecordData, action: "download" | "parse") { if (action === "parse" && !window.confirm("Queue parsing of this uploaded resume? This will not automatically change the candidate profile.")) return; setPending(String(resume.id)); setError(null); setDownload(null); try { if (action === "download") { const value = await api<{ url: string; expires_in: number }>(`resumes/${resume.id}/download/`, { method: "POST" }); const url = new URL(value.url); if (!["https:", "http:"].includes(url.protocol)) throw new Error("The server returned an invalid download URL."); setDownload(value); } else { await api(`resumes/${resume.id}/parse/`, { method: "POST" }); refresh(); } } catch (cause) { setError(cause); } finally { setPending(null); } }
  return <div className="record-detail"><ErrorMessage error={profileError ?? error} />{!profile && !profileError && <p role="status">Loading full profile…</p>}{profile && <><h3>{display(profile.full_name)} · full profile</h3><Details row={profile} /><button className="secondary" onClick={() => setEditing(!editing)}>{editing ? "Close editor" : "Edit intake profile"}</button>{editing && <MutationForm key={`${id}-${profile.profile_version}`} title="Edit candidate intake" fields={profileFields} initial={profile} lookups={lookups} confirm="Save these candidate intake changes?" onSubmit={async (body) => { await api(`admin/candidates/${id}/`, { method: "PATCH", body: JSON.stringify({ ...body, profile_version: profile.profile_version }) }); refresh(); }} />}<MutationForm title="Candidate review" fields={[{ name: "review_status", label: "Decision", type: "select", options: ["APPROVED", "CHANGES_REQUESTED"], required: true }, { name: "review_notes", label: "Review notes", type: "textarea", required: true }]} initial={{ review_notes: profile.review_notes }} lookups={lookups} confirm="Save this candidate review decision?" submitLabel="Save review" onSubmit={async (body) => { await api(`admin/candidates/${id}/`, { method: "PATCH", body: JSON.stringify(body) }); refresh(); }} /></>}
     <h3>Applications</h3><ErrorMessage error={applications.error} />{applications.loading ? <p role="status">Loading application history…</p> : !applications.error && <><RecordTable rows={applicationRows} columns={["company_name", "job_title", "submitted_at", "status", "campaign_display", "updated_at"]} /><HistoryPager page={applicationPage} count={applications.data.length} onPage={setApplicationPage} /></>}
     <h3>Outreach history</h3><ErrorMessage error={outreach.error} />{outreach.loading ? <p role="status">Loading outreach history…</p> : outreach.error ? <button className="secondary" onClick={outreach.retry}>Retry outreach history</button> : <><RecordTable rows={outreachRows} columns={["company_name", "contact_name", "channel", "status", "sent_at", "reply_at", "campaign_display"]} /><HistoryPager page={outreachPage} count={outreach.data.length} onPage={setOutreachPage} /></>}
     <h3>Payments</h3><ErrorMessage error={payments.error} />{payments.loading ? <p role="status">Loading payment history…</p> : !payments.error && <><RecordTable rows={paymentRows} columns={["created_at", "amount", "currency", "status", "reference", "verified_at", "campaign_display"]} /><HistoryPager page={paymentPage} count={payments.data.length} onPage={setPaymentPage} /></>}
    <h3>Resume files</h3><ErrorMessage error={resumes.error} />{resumes.loading ? <p role="status">Loading resume metadata…</p> : !resumes.error && (resumes.data.length ? <ul className="record-list">{resumes.data.map((resume) => <li key={String(resume.id)}><strong>{display(resume.original_filename)}</strong><p className="muted">Upload: {display(resume.upload_status)} · Parse: {display(resume.parse_status)}</p>{Boolean(resume.parse_error_code) && <p className="field-error">Parse error: {display(resume.parse_error_code)}</p>}<div className="button-row"><button disabled={pending !== null || resume.upload_status !== "UPLOADED"} className="secondary" onClick={() => resumeAction(resume, "download")}>{pending === String(resume.id) ? "Working…" : "Get download link"}</button><button disabled={pending !== null || resume.upload_status !== "UPLOADED" || ["QUEUED", "RUNNING", "PROCESSING", "PARSED"].includes(String(resume.parse_status))} className="secondary" onClick={() => resumeAction(resume, "parse")}>Queue parse</button></div>{resume.parse_status === "PARSED" && <ParsedResumeText resume={resume} api={api} />}</li>)}</ul> : <p className="empty">No resumes uploaded.</p>)}{download && <p className="success"><a href={download.url} target="_blank" rel="noopener noreferrer">Download resume</a> · expires in {download.expires_in} seconds.</p>}</div>;
}

function HistoryPager({ page, count, onPage }: { page: number; count: number; onPage: (page: number) => void }) {
  return <div className="button-row"><button className="secondary" disabled={page === 0} onClick={() => onPage(page - 1)}>Previous</button><span className="muted">Page {page + 1}</span><button className="secondary" disabled={count < 50} onClick={() => onPage(page + 1)}>Next</button></div>;
}

export default function CandidatesPanel({ context }: { context: WorkspaceContext }) {
  const [page, setPage] = useState(0); const [selected, setSelected] = useState<string | null>(null); const [query, setQuery] = useState("");
  const { data, loading, error } = useRecords(context.api, `admin/candidates/?limit=100&offset=${page * 100}${query ? `&q=${encodeURIComponent(query)}` : ""}`, context.revision);
  return <section className="panel"><div className="panel-heading"><div><h2>Candidate intake & review</h2><p className="muted">Review profiles, resumes and authoritative application/payment history.</p></div><button className="secondary" onClick={context.refresh} disabled={loading}>Refresh</button></div><label className="search-label">Search candidates<input type="search" value={query} onChange={(event) => { setQuery(event.target.value); setPage(0); setSelected(null); }} placeholder="Name or email" /></label><ErrorMessage error={error} />{loading ? <p className="empty" role="status">Loading candidates…</p> : !error && <RecordTable rows={data} columns={["full_name", "email", "applications_submitted", "headline", "location", "review_status"]} selected={selected ?? undefined} onSelect={(row) => setSelected(String(row.id))} />}<div className="button-row"><button className="secondary" disabled={page === 0 || loading} onClick={() => { setPage((value) => value - 1); setSelected(null); }}>Previous page</button><span className="muted">Page {page + 1} · up to 100 candidates</span><button className="secondary" disabled={loading || data.length < 100} onClick={() => { setPage((value) => value + 1); setSelected(null); }}>Next page</button></div>{selected && <><button className="secondary" onClick={() => setSelected(null)}>Close candidate</button><CandidateDetail key={selected} id={selected} context={context} /></>}</section>;
}
