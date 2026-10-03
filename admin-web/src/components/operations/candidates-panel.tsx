"use client";

import { useEffect, useState } from "react";
import { Details, ErrorMessage, MutationForm, RecordTable, useRecords } from "./ui";
import { display, type Field, type RecordData, type WorkspaceContext } from "./types";
import ParsedResumeText from "./parsed-resume-text";

const profileFields: Field[] = [
  { name: "full_name", label: "Full name", required: true }, { name: "headline", label: "Headline" }, { name: "location", label: "Location", required: true },
  { name: "experience_summary", label: "Experience summary", type: "textarea", required: true },
  { name: "target_roles", label: "Target roles", type: "list", help: "Comma-separated; up to ten unique values." }, { name: "preferred_locations", label: "Preferred locations", type: "list" },
  { name: "target_industries", label: "Target industries", type: "list" }, { name: "remote_preference", label: "Remote preference", type: "select", options: ["UNSPECIFIED", "ONSITE", "HYBRID", "REMOTE", "FLEXIBLE"], required: true },
  { name: "expected_ctc_min", label: "Minimum expected compensation", type: "number", nullable: true, min: 0 }, { name: "expected_ctc_max", label: "Maximum expected compensation", type: "number", nullable: true, min: 0 },
  { name: "work_authorization", label: "Work authorization" }, { name: "sponsorship_requirement", label: "Sponsorship requirement" }, { name: "notice_period", label: "Notice period" },
];

function CandidateDetail({ id, context }: { id: string; context: WorkspaceContext }) {
  const { api, revision, refresh, lookups } = context;
  const key = `${id}:${revision}`;
  const [profileResult, setProfileResult] = useState<{ key: string; profile: RecordData | null; error: unknown }>({ key: "", profile: null, error: null });
  const profile = profileResult.key === key ? profileResult.profile : null;
  const profileError = profileResult.key === key ? profileResult.error : null;
  const [error, setError] = useState<unknown>(null);
  const [editing, setEditing] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [download, setDownload] = useState<{ url: string; expires_in: number } | null>(null);
  const [notice, setNotice] = useState("");
  const resumes = useRecords(api, `admin/candidates/${id}/resumes/`, revision);
  useEffect(() => {
    let active = true;
    api<RecordData>(`admin/candidates/${id}/`).then((profile) => { if (active) setProfileResult({ key, profile, error: null }); }).catch((error: unknown) => { if (active) setProfileResult({ key, profile: null, error }); });
    return () => { active = false; };
  }, [api, id, key]);
  async function resumeAction(resume: RecordData, action: "download" | "parse") {
    if (action === "parse" && !window.confirm("Queue parsing of this uploaded resume? This will not automatically change the candidate profile.")) return;
    setPending(String(resume.id)); setError(null); setDownload(null); setNotice("");
    try {
      if (action === "download") {
        const result = await api<{ url: string; expires_in: number }>(`resumes/${resume.id}/download/`, { method: "POST" });
        const url = new URL(result.url);
        if (!["https:", "http:"].includes(url.protocol)) throw new Error("The server returned an invalid download URL.");
        setDownload(result);
      } else { await api(`resumes/${resume.id}/parse/`, { method: "POST" }); setNotice("Parsing request accepted. Refresh to check the server's parse status."); refresh(); }
    } catch (e) { setError(e); } finally { setPending(null); }
  }
  return <div className="record-detail"><ErrorMessage error={profileError ?? error} />{!profile && !profileError && <p role="status">Loading full profile…</p>}{profile && <><h3>{display(profile.full_name)} · full profile</h3><Details row={profile} /><button className="secondary" onClick={() => setEditing(!editing)}>{editing ? "Close editor" : "Edit intake profile"}</button>{editing && <MutationForm key={`${id}-${profile.profile_version}`} title="Edit candidate intake" fields={profileFields} initial={profile} lookups={lookups} confirm="Save these candidate intake changes?" onSubmit={async (body) => { await api(`admin/candidates/${id}/`, { method: "PATCH", body: JSON.stringify({ ...body, profile_version: profile.profile_version }) }); refresh(); }} />}
      <MutationForm key={`review-${id}`} title="Candidate review" fields={[{ name: "review_status", label: "Decision", type: "select", options: ["APPROVED", "CHANGES_REQUESTED"], required: true }, { name: "review_notes", label: "Review notes", type: "textarea", required: true }]} lookups={lookups} initial={{ review_notes: profile.review_notes }} confirm="Save this candidate review decision?" submitLabel="Save review" onSubmit={async (body) => { await api(`admin/candidates/${id}/`, { method: "PATCH", body: JSON.stringify(body) }); refresh(); }} />
    </>}<h3>Resume files</h3><ErrorMessage error={resumes.error} />{resumes.loading ? <p role="status">Loading resume metadata…</p> : !resumes.error && (resumes.data.length ? <ul className="record-list">{resumes.data.map((resume) => <li key={String(resume.id)}><div><strong>{display(resume.original_filename)}</strong><p className="muted">Upload: {display(resume.upload_status)} · Parse: {display(resume.parse_status)} · {display(resume.file_size)} bytes</p>{Boolean(resume.parse_error_code) && <p className="field-error">Parse error: {display(resume.parse_error_code)}</p>}</div><div className="button-row"><button disabled={pending !== null || resume.upload_status !== "UPLOADED"} className="secondary" onClick={() => resumeAction(resume, "download")}>{pending === String(resume.id) ? "Working…" : "Get download link"}</button><button disabled={pending !== null || resume.upload_status !== "UPLOADED" || ["QUEUED", "RUNNING", "PROCESSING", "PARSED"].includes(String(resume.parse_status))} className="secondary" onClick={() => resumeAction(resume, "parse")}>Queue parse</button></div>{resume.parse_status === "PARSED" && <ParsedResumeText key={`${resume.id}-${revision}`} resume={resume} api={api} />}</li>)}</ul> : <p className="empty">No resumes uploaded.</p>)}{notice && <p role="status">{notice}</p>}{download && <p className="success"><a href={download.url} target="_blank" rel="noopener noreferrer">Download resume</a> · link expires in {download.expires_in} seconds.</p>}</div>;
}

export default function CandidatesPanel({ context }: { context: WorkspaceContext }) {
  const [page, setPage] = useState(0);
  const { data, loading, error } = useRecords(context.api, `admin/candidates/?limit=100&offset=${page * 100}`, context.revision);
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const rows = data.filter((row) => `${row.full_name} ${row.email} ${row.review_status}`.toLowerCase().includes(query.toLowerCase()));
  return <section className="panel"><div className="panel-heading"><div><h2>Candidate intake & review</h2><p className="muted">Review profiles, request changes and inspect resume metadata and parsing status.</p></div><button className="secondary" onClick={context.refresh} disabled={loading}>Refresh</button></div><label className="search-label">Find candidate on this page<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, email or review status" /></label><ErrorMessage error={error} />{loading ? <p className="empty" role="status">Loading candidates…</p> : !error && <RecordTable rows={rows} columns={["full_name", "email", "headline", "location", "review_status"]} selected={selected ?? undefined} onSelect={(row) => setSelected(String(row.id))} />}<div className="button-row"><button className="secondary" disabled={page === 0 || loading} onClick={() => { setPage((value) => value - 1); setSelected(null); }}>Previous page</button><span className="muted">Page {page + 1} · up to 100 candidates per page</span><button className="secondary" disabled={loading || data.length < 100} onClick={() => { setPage((value) => value + 1); setSelected(null); }}>Next page</button></div>{selected && <><div className="button-row"><button className="secondary" onClick={() => setSelected(null)}>Close candidate</button></div><CandidateDetail key={selected} id={selected} context={context} /></>}</section>;
}
