"use client";

import { useEffect, useId, useState } from "react";
import ResourcePanel from "./resource-panel";
import { aiRuns } from "./resources";
import { display, humanize, type Field, type RecordData, type WorkspaceContext } from "./types";
import { ErrorMessage, MutationForm } from "./ui";

const capabilities = ["profile_extract", "job_match", "outreach_draft", "qa"] as const;
type Capability = typeof capabilities[number];

export default function AiPanel({ context }: { context: WorkspaceContext }) {
  const id = useId();
  const { api, revision } = context;
  const [campaign, setCampaign] = useState(context.campaign);
  const [capability, setCapability] = useState<Capability>("profile_extract");
  const key = `${campaign}:${capability}:${revision}`;
  const [resumeResult, setResumeResult] = useState<{ key: string; rows: RecordData[]; error: unknown }>({ key: "", rows: [], error: null });
  const [created, setCreated] = useState<RecordData | null>(null);
  const loading = capability === "profile_extract" && Boolean(campaign) && resumeResult.key !== key;
  const error = resumeResult.key === key ? resumeResult.error : null;
  const resumes = resumeResult.key === key ? resumeResult.rows : [];
  useEffect(() => {
    if (!campaign || capability !== "profile_extract") return;
    let active = true;
    async function loadResumes() {
      try {
        const selected = await api<RecordData>(`campaigns/${campaign}/`);
        const rows = await api<RecordData[]>(`admin/candidates/${selected.candidate_id}/resumes/`);
        if (active) setResumeResult({ key, rows: rows.filter((row) => row.upload_status === "UPLOADED" && row.parse_status === "PARSED"), error: null });
      } catch (error) { if (active) setResumeResult({ key, rows: [], error }); }
    }
    void loadResumes();
    return () => { active = false; };
  }, [api, campaign, capability, key]);
  const fields: Field[] = capability === "profile_extract"
    ? [{ name: "resume_id", label: "Parsed candidate resume", lookup: "resumes", required: true, help: "Only this campaign candidate's uploaded, successfully parsed resumes are eligible. Queue parsing in Candidates first." }]
    : capability === "job_match" ? [{ name: "job_id", label: "Job to match", lookup: "jobs", required: true }]
    : capability === "outreach_draft" ? [{ name: "contact_id", label: "Contact to draft for", lookup: "contacts", required: true, help: "Suppression and authorization are checked again by the API." }]
    : [{ name: "content", label: "Content for QA review", type: "textarea", required: true, help: "Up to 16,000 characters. Candidate facts are loaded by the server; do not provide profile overrides or credentials." }];
  const lookups = { ...context.lookups, resumes: resumes.map((resume) => ({ value: String(resume.id), label: display(resume.original_filename) })) };
  return <><section className="panel"><h2>Request AI assistance</h2><p className="muted">HTF reads canonical candidate facts from the server. Choose a source record, not raw profile JSON. Proposals never automatically change profiles, applications or outreach.</p><div className="form-grid"><label htmlFor={`${id}-campaign`}>Campaign<select id={`${id}-campaign`} value={campaign} onChange={(event) => { setCampaign(event.target.value); setCreated(null); }}><option value="">Select a campaign…</option>{context.lookups.campaigns?.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}</select></label><label htmlFor={`${id}-capability`}>Capability<select id={`${id}-capability`} value={capability} onChange={(event) => { setCapability(event.target.value as Capability); setCreated(null); }}>{capabilities.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label></div>{!campaign && <p className="empty">Choose a campaign to request a proposal.</p>}{loading && <p role="status">Loading eligible parsed resumes…</p>}<ErrorMessage error={error} />{campaign && !loading && !error && (capability === "profile_extract" && !resumes.length ? <p className="empty">No eligible parsed resumes for this candidate. Upload and parse a resume before requesting profile extraction.</p> : <MutationForm key={`${campaign}-${capability}`} title={humanize(capability)} fields={fields} lookups={lookups} submitLabel="Queue proposal" confirm={aiRuns.createConfirm} onSubmit={async (input) => {
    if (capability === "qa" && String(input.content).length > 16000) throw new Error("QA content must be at most 16,000 characters.");
    const result = await api<RecordData>("ai/runs/", { method: "POST", body: JSON.stringify({ campaign, capability, input }) });
    setCreated(result); context.refresh();
  }} />)}{created && <p role="status" className="success">Run {display(created.id)} recorded · server status: {display(created.status)}. Open the run below and refresh for results.</p>}</section><div className="dashboard"><ResourcePanel key={campaign} resource={aiRuns} context={{ ...context, campaign }} /></div></>;
}
