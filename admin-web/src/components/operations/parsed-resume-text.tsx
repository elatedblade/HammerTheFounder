"use client";

import { useId, useState } from "react";
import type { ApiClient, ParsedResumeTextDto } from "../../lib/api";
import { display, type RecordData } from "./types";
import { ErrorMessage } from "./ui";

export default function ParsedResumeText({ resume, api }: { resume: RecordData; api: ApiClient }) {
  const id = useId();
  const [result, setResult] = useState<ParsedResumeTextDto | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  async function load() {
    setPending(true); setError(null);
    try { setResult(await api<ParsedResumeTextDto>(`resumes/${resume.id}/parsed-text/`)); }
    catch (error) { setError(error); }
    finally { setPending(false); }
  }
  return <section className="record-detail"><h3>Parsed text · {display(resume.original_filename)}</h3><div className="button-row"><button className="secondary" disabled={pending} onClick={load}>{pending ? "Loading parsed text…" : result ? "Refresh parsed text" : "View parsed text"}</button>{result && <button className="secondary" onClick={() => setResult(null)}>Hide text</button>}</div><ErrorMessage error={error} />{result && <><p className="muted">Parsed {result.parsed_at ? new Date(result.parsed_at).toLocaleString() : "—"}. {result.truncated ? `Truncated to the first ${result.max_chars.toLocaleString()} characters.` : `Bounded to ${result.max_chars.toLocaleString()} characters.`} Review extraction accuracy before using the content.</p><label htmlFor={id}>Extracted resume text (read-only)</label><textarea id={id} readOnly value={result.text} rows={12} /></>}</section>;
}
