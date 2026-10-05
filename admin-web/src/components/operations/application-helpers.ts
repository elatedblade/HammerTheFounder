import type { Action } from "./types";
// @ts-expect-error Explicit TS extension supports Node strip-types regression tests.
import { applicationStageOptions } from "./application-stages.ts";

export const applicationColumns = ["candidate_name", "candidate_email", "company_name", "job_title", "status", "submitted_at"];
export const applicationTransitions: Record<string, string[]> = {
  SAVED: ["DISCOVERED", "SHORTLISTED", "READY", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"],
  DISCOVERED: ["SHORTLISTED", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"],
  SHORTLISTED: ["QUEUED", "READY", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"],
  QUEUED: ["IN_PROGRESS", "WITHDRAWN"],
  IN_PROGRESS: ["SUBMITTED", "APPLICATION_FAILED", "WITHDRAWN"],
  APPLICATION_FAILED: ["QUEUED", "WITHDRAWN"],
  READY: ["QUEUED", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"],
  SUBMITTED: ["IN_REVIEW", "RECRUITER_CONTACTED", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  IN_REVIEW: ["RECRUITER_CONTACTED", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  RECRUITER_CONTACTED: ["INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  INTERVIEW: ["INTERVIEW_SCHEDULED", "OFFER", "REJECTED", "WITHDRAWN"],
  INTERVIEW_SCHEDULED: ["INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  OFFER: ["WITHDRAWN"], REJECTED: [], WITHDRAWN: [],
};

export function applicationStatusOptions() {
  return applicationStageOptions;
}

export const updateApplicationStageAction: Action = {
  label: "Update application status", route: "stage/",
  when: (row) => !["REJECTED", "WITHDRAWN", "APPLICATION_FAILED"].includes(String(row.status)) && (applicationStageOptions.some(option => option.value === row.stage) || Boolean(applicationTransitions[String(row.status)])),
  initial: (row) => ({ stage: applicationStageOptions.some(option => option.value === row.stage) ? row.stage : "", submission_confirmed: false }),
  fields: (row) => {
    const needsConfirmation = (values: Record<string, string>) => !row.submitted_at && ["UNDER_REVIEW", "INTERVIEWS", "OFFERS"].includes(values.stage);
    return [
      { name: "stage", label: "New status", type: "select", required: true, options: applicationStatusOptions(), help: "Backward changes are rejected by the server to preserve application history." },
      { name: "submission_confirmed", label: "Confirm application was submitted externally", type: "checkbox", visibleWhen: needsConfirmation, requiredWhen: needsConfirmation, help: "Check only after confirming an external submission. This records its date and does not send an application." },
      { name: "notes", label: "Internal notes (optional)", type: "textarea" },
    ];
  },
  confirm: "Record this application stage? Confirm the external outcome has already occurred.",
};

export function applicationOutcomeOptions(row: Record<string, unknown>) {
  return (applicationTransitions[String(row.status)] ?? []).filter(value => ["APPLICATION_FAILED", "REJECTED", "WITHDRAWN", "QUEUED"].includes(value)).map(value => ({ value, label: value === "QUEUED" ? "Retry application" : value.toLowerCase().replaceAll("_", " ").replace(/^./, letter => letter.toUpperCase()) }));
}

export function canRecordSubmitted(row: Record<string, unknown>) {
  return !row.submitted_at && (applicationTransitions[String(row.status)] ?? []).includes("SUBMITTED");
}

export const recordSubmittedAction: Action = {
  label: "Record submitted", route: "transition/", body: { status: "SUBMITTED" }, when: canRecordSubmitted,
  fields: [{ name: "notes", label: "Submission notes (optional)", type: "textarea", help: "Add evidence or context. Use Edit record to save an optional submission/source reference separately. The server checks active campaign, open job and service plan readiness." }],
  confirm: "Confirm this application has already been submitted externally for this candidate and job? This only records the submission; it does not send an application.",
};

export function applicationSubmittedDate(value: unknown) {
  if (!value) return "Not recorded";
  const date = new Date(String(value));
  if (Number.isNaN(date.valueOf())) return "Unavailable";
  return date.toISOString().slice(0, 10);
}

export const LOOKUP_PAGE_SIZE = 50;
export function lookupPath(path: string, query: string, page: number) {
  return `${path}?q=${encodeURIComponent(query)}&limit=${LOOKUP_PAGE_SIZE}&offset=${page * LOOKUP_PAGE_SIZE}`;
}
export function applicationPayload(values: { campaign: string; job: string; notes: string; source_reference: string }) {
  if (!values.campaign || !values.job) throw new Error("Choose a real job and an authorized campaign first.");
  return { ...values };
}
export function jobPayload(values: { company: string; title: string; location: string; canonical_url: string }) {
  if (!values.company || !values.title.trim()) throw new Error("Choose a company and enter a job title.");
  return { ...values, title: values.title.trim(), status: "OPEN" };
}

export function oneStepApplicationPayload(values: { campaign: string; notes: string; source_reference: string }, job: string | null, draft: { company_name: string; title: string; location: string; canonical_url: string }) {
  if (!values.campaign) throw new Error("Choose an authorized campaign first.");
  if (job) return { ...values, job };
  if (!draft.company_name.trim() || !draft.title.trim()) throw new Error("Enter a company name and job title.");
  return { ...values, new_job: { ...draft, company_name: draft.company_name.trim(), title: draft.title.trim() } };
}
