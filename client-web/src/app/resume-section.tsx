"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import {
  ApiRequestError,
  getCandidateResumes,
  requestCandidateResumeUpload,
  type ResumeMetadata,
} from "../lib/api";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const FILE_TYPES: Record<string, string> = {
  pdf: "application/pdf",
  doc: "application/msword",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

type UploadState = "idle" | "authorizing" | "uploading" | "refreshing" | "success" | "error";

function contentType(file: File): string | undefined {
  return FILE_TYPES[file.name.split(".").at(-1)?.toLowerCase() ?? ""];
}

function validateFile(file: File): string | null {
  const expectedType = contentType(file);
  if (!expectedType) return "Choose a PDF, DOC, or DOCX file.";
  // Some operating systems leave the MIME type empty or use the generic binary type.
  if (file.type && file.type !== "application/octet-stream" && file.type !== expectedType) {
    return "The file type does not match its extension. Choose a PDF, DOC, or DOCX file.";
  }
  if (file.size === 0) return "This file is empty. Choose a resume with content.";
  if (file.size > MAX_FILE_SIZE) return "Your resume must be 10 MB or smaller.";
  return null;
}

function formatSize(bytes: number): string {
  return bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.ceil(bytes / 1024))} KB`;
}

function formatDate(value?: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

function storageNotConfigured(error: unknown): boolean {
  return error instanceof ApiRequestError && error.status === 503 && error.code === "STORAGE_NOT_CONFIGURED";
}

export default function ResumeSection({ getToken }: { getToken: () => Promise<string | null> }) {
  const [resumes, setResumes] = useState<ResumeMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [setupRequired, setSetupRequired] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [message, setMessage] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const listController = useRef<AbortController | null>(null);
  const uploadController = useRef<AbortController | null>(null);
  const busy = ["authorizing", "uploading", "refreshing"].includes(uploadState);

  const refreshResumes = useCallback(async (): Promise<boolean> => {
    listController.current?.abort();
    const controller = new AbortController();
    listController.current = controller;
    setLoading(true);
    setListError(null);
    try {
      const next = await getCandidateResumes(getToken, controller.signal);
      if (controller.signal.aborted) return false;
      setResumes(next);
      setSetupRequired(false);
      return true;
    } catch (error: unknown) {
      if (controller.signal.aborted) return false;
      if (storageNotConfigured(error)) setSetupRequired(true);
      else setListError(error instanceof Error ? error.message : "We could not load your resume records.");
      return false;
    } finally {
      if (!controller.signal.aborted) setLoading(false);
      if (listController.current === controller) listController.current = null;
    }
  }, [getToken]);

  useEffect(() => {
    // This effect synchronizes resume metadata with the authenticated API.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshResumes();
    return () => {
      listController.current?.abort();
      uploadController.current?.abort();
    };
  }, [refreshResumes]);

  const clearFile = () => {
    setFile(null);
    setFileError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const reset = () => {
    const wasBusy = busy;
    uploadController.current?.abort();
    uploadController.current = null;
    clearFile();
    setUploadState("idle");
    setMessage(wasBusy ? "Upload cancelled in this browser. A resume record may remain if authorization had completed." : "");
    if (wasBusy) void refreshResumes();
    inputRef.current?.focus();
  };

  const upload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (uploadController.current) return;
    if (!file) {
      setFileError("Choose a resume to upload.");
      inputRef.current?.focus();
      return;
    }
    const issue = validateFile(file);
    if (issue) {
      setFileError(issue);
      return;
    }
    const controller = new AbortController();
    uploadController.current = controller;
    setFileError(null);
    setSetupRequired(false);
    setUploadState("authorizing");
    setMessage("Preparing a secure upload…");
    let uploaded = false;
    try {
      const authorization = await requestCandidateResumeUpload(getToken, {
        original_filename: file.name,
        content_type: contentType(file)!,
        file_size: file.size,
      }, controller.signal);
      if (controller.signal.aborted) return;
      setUploadState("uploading");
      setMessage("Uploading directly to secure storage…");
      const response = await fetch(authorization.upload_url, {
        method: "PUT",
        headers: authorization.upload_headers,
        body: file,
        signal: controller.signal,
        credentials: "omit",
      });
      if (!response.ok) throw new Error("Storage did not accept the upload. Choose Upload resume to request a new upload link and try again.");
      if (controller.signal.aborted) return;
      uploaded = true;
      clearFile();
      setUploadState("refreshing");
      setMessage("Upload complete. Refreshing your resume records…");
      const refreshed = await refreshResumes();
      if (controller.signal.aborted) return;
      if (!refreshed) {
        setUploadState("error");
        setMessage("Your resume was uploaded, but the list could not be refreshed. Refresh the list to check your records.");
        return;
      }
      setUploadState("success");
      setMessage("Your resume was uploaded successfully.");
    } catch (error: unknown) {
      if (controller.signal.aborted) return;
      setUploadState("error");
      if (storageNotConfigured(error)) {
        setSetupRequired(true);
        setMessage("");
      } else if (error instanceof ApiRequestError && error.status === 400) {
        setFileError(error.message);
        setMessage("");
      } else {
        setMessage(uploaded ? "Your resume was uploaded, but the list could not be refreshed. Refresh the list to check your records." : error instanceof ApiRequestError ? error.message : "The upload could not be completed. Check your connection, then choose Upload resume to try again.");
      }
    } finally {
      if (uploadController.current === controller) uploadController.current = null;
    }
  };

  return (
    <section className="panel resume-panel" aria-labelledby="resume-heading">
      <div className="panel-heading">
        <div><span className="eyebrow">Your documents</span><h2 id="resume-heading">Resume</h2></div>
        <span className="resume-format-note">PDF, DOC or DOCX · up to 10 MB</span>
      </div>
      <p className="muted">Add the resume you want us to work with. Upload one document at a time.</p>

      {setupRequired ? (
        <div className="notice notice-warning" role="status">
          <div><strong>Resume storage needs setup.</strong><p>Uploads will be available once the HTF team connects document storage. You can keep editing your profile and try the upload again later.</p></div>
        </div>
      ) : null}

      <form className="resume-upload-form" onSubmit={upload} noValidate>
        <div className="field">
          <label htmlFor="resume-file">Choose a resume</label>
          <input
            ref={inputRef}
            id="resume-file"
            type="file"
            accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            disabled={busy}
            aria-invalid={Boolean(fileError)}
            aria-describedby={`resume-file-hint${fileError ? " resume-file-error" : ""}`}
            onChange={(event) => {
              const selected = event.target.files?.[0] ?? null;
              setFile(selected);
              setFileError(selected ? validateFile(selected) : null);
              setUploadState("idle");
              setMessage("");
            }}
          />
          <p id="resume-file-hint" className="field-hint">{file ? `${file.name} · ${formatSize(file.size)}` : "Your file uploads directly to document storage."}</p>
          {fileError ? <p id="resume-file-error" className="field-error" role="alert">{fileError}</p> : null}
        </div>
        <div className="resume-actions">
          <button className="button button-primary" type="submit" disabled={busy || !file || Boolean(fileError)}>
            {busy ? <><span className="button-spinner" aria-hidden="true" />{uploadState === "authorizing" ? "Preparing upload" : uploadState === "refreshing" ? "Refreshing records" : "Uploading resume"}</> : "Upload resume"}
          </button>
          {file || busy ? <button className="button button-secondary" type="button" onClick={reset}>{busy ? "Cancel" : "Reset"}</button> : null}
        </div>
        <p className={`resume-upload-status ${uploadState}`} role="status" aria-live="polite" aria-atomic="true">{message}</p>
      </form>

      <div className="resume-records" aria-labelledby="resume-records-heading">
        <div className="resume-records-heading">
          <h3 id="resume-records-heading">Your resume records</h3>
          <button className="button button-secondary button-small" type="button" disabled={loading || busy} onClick={() => void refreshResumes()}>Refresh list</button>
        </div>
        {loading ? <p className="muted" role="status">Loading your resumes…</p> : null}
        {listError ? <p className="field-error" role="alert">{listError} Use Refresh list to try again.</p> : null}
        {!loading && !listError && !setupRequired && resumes.length === 0 ? <p className="resume-empty">No resume records yet. Choose a file above to get started.</p> : null}
        {resumes.length > 0 ? (
          <>
            <ul className="resume-list">
              {resumes.map((resume) => {
                const dateValue = resume.created_at ?? resume.uploaded_at;
                const date = formatDate(dateValue);
                return (
                  <li key={resume.id}>
                    <strong>{resume.original_filename}</strong>
                    <span>{formatSize(resume.file_size)} · {resume.content_type}{resume.upload_status ? ` · ${resume.upload_status}` : null}{date ? <> · Added <time dateTime={dateValue}>{date}</time></> : null}</span>
                  </li>
                );
              })}
            </ul>
            <p className="field-hint">Records are created when an upload is authorized. A record alone does not confirm that the file finished uploading.</p>
          </>
        ) : null}
      </div>
    </section>
  );
}
