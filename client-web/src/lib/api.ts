export type CurrentUser = {
  id: number;
  email: string;
  phone: string;
  role: "CLIENT" | "OPERATOR" | "ADMIN" | "SUPERADMIN";
  identity_provider: string;
};

export type RemotePreference = "UNSPECIFIED" | "ONSITE" | "HYBRID" | "REMOTE" | "FLEXIBLE";

export type CandidateProfile = {
  id: number;
  full_name: string;
  headline: string;
  location: string;
  experience_summary: string;
  target_roles: string[];
  preferred_locations: string[];
  remote_preference: RemotePreference;
  profile_version: number;
  created_at: string;
  updated_at: string;
  basics_complete: boolean;
  target_industries?: string[];
  expected_ctc_min?: number | string | null;
  expected_ctc_max?: number | string | null;
  work_authorization?: string;
  sponsorship_requirement?: string;
  notice_period?: string;
  preferences_json?: Record<string, unknown>;
  review_status?: "PENDING" | "APPROVED" | "CHANGES_REQUESTED";
};

export type CandidateProfileDraft = Pick<
  CandidateProfile,
  | "full_name"
  | "headline"
  | "location"
  | "experience_summary"
  | "target_roles"
  | "preferred_locations"
  | "remote_preference"
  | "target_industries"
  | "work_authorization"
  | "sponsorship_requirement"
  | "notice_period"
  | "preferences_json"
> & { expected_ctc_min: number | null; expected_ctc_max: number | null };

export type ResumeMetadata = {
  id: number | string;
  original_filename: string;
  content_type: string;
  file_size: number;
  upload_status?: string;
  parse_status?: string;
  version?: number;
  created_at?: string;
  updated_at?: string;
  uploaded_at?: string;
};

export type ResumeUploadAuthorization = {
  id: number | string;
  upload_url: string;
  upload_headers: Record<string, string>;
  expires_at: string;
  resume: ResumeMetadata;
};

export type ResumeUploadRequest = {
  original_filename: string;
  content_type: string;
  file_size: number;
};

export type Dashboard = { applications: Record<string, number>; outreach: Record<string, number>; campaigns: Record<string, number>; tasks: { open: number } };
export const APPLICATION_STATUSES = ["SAVED", "READY", "DISCOVERED", "SHORTLISTED", "QUEUED", "IN_PROGRESS", "APPLICATION_FAILED", "SUBMITTED", "IN_REVIEW", "RECRUITER_CONTACTED", "INTERVIEW", "INTERVIEW_SCHEDULED", "OFFER", "REJECTED", "WITHDRAWN"] as const;
export const OUTREACH_STATUSES = ["DRAFT", "READY", "TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED", "SENT", "DELIVERED", "REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY", "BOUNCED", "CLOSED", "SUPPRESSED"] as const;
export type Application = { id: string|number; campaign: string; job: string; company_name: string; job_title: string; status: string; submitted_at: string|null; interview_scheduled_at: string|null; created_at: string; updated_at: string };
export type Outreach = { id: string|number; campaign: string; company_name: string; contact_name: string; channel: string; status: string; sent_at: string|null; delivered_at: string|null; bounced_at: string|null; reply_at: string|null; follow_up_due_at: string|null; };
export type CampaignEvent = { id: string|number; event_type: string; summary: string; created_at: string; campaign: string|null };
export type Notification = { id: string|number; campaign: string|null; channel: string; status: string; subject: string; body: string; created_at: string; sent_at: string|null };
export type Payment = { id: string|number; campaign: string; amount: string; currency: string; status: string; verified_at: string|null; created_at: string };
export type PaymentInstructions = { configured: boolean; upi_id: string|null; payee_name: string|null; instructions: string|null };
export type ServicePlan = "NORMAL_APPLY" | "COLD_APPLY" | "FULL_THROTTLE";
export type InquiryStatus = "OPEN" | "CONTACTED" | "CONVERTED" | "CLOSED";
export type Inquiry = { id: string; reference: string; plan: ServicePlan; status: InquiryStatus; created_at: string; updated_at: string; campaign_id: string | null; whatsapp_url: string | null };
export type PublicContact = { whatsapp_configured: boolean; support_email: string | null };

async function getJson<T>(getToken: () => Promise<string|null>, path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${apiUrl}/api/v1/${path}`, { headers: await authorizationHeaders(getToken, signal), cache: "no-store", signal });
  if (!response.ok) throw await responseError(response, "We could not load this information.");
  return (await response.json()) as T;
}
export const getDashboard = (token: () => Promise<string|null>, signal?: AbortSignal) => getJson<Dashboard>(token, "dashboard/", signal);
export const getApplications = (token: () => Promise<string|null>, query = "", signal?: AbortSignal) => getJson<Application[]>(token, `applications/${query ? `?${query}` : ""}`, signal);
export const getOutreach = (token: () => Promise<string|null>, query = "", signal?: AbortSignal) => getJson<Outreach[]>(token, `outreach/${query ? `?${query}` : ""}`, signal);
export const getEvents = (token: () => Promise<string|null>, query = "", signal?: AbortSignal) => getJson<CampaignEvent[]>(token, `events/${query ? `?${query}` : ""}`, signal);
export const getNotifications = (token: () => Promise<string|null>, signal?: AbortSignal, campaign = "", limit = 50, offset = 0) => getJson<Notification[]>(token, `notifications/?${new URLSearchParams({ ...(campaign ? {campaign} : {}), limit: String(limit), offset: String(offset) })}`, signal);
export const getPayments = (token: () => Promise<string|null>, signal?: AbortSignal, campaign = "", limit = 50, offset = 0) => {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (campaign) query.set("campaign", campaign);
  return getJson<Payment[]>(token, `billing/payments/?${query}`, signal);
};
export const getPaymentInstructions = (token: () => Promise<string|null>, signal?: AbortSignal) => getJson<PaymentInstructions>(token, "billing/instructions/", signal);
export const getInquiries = (token: () => Promise<string|null>, signal?: AbortSignal) => getJson<Inquiry[]>(token, "candidate/inquiries/", signal);
export const getPublicContact = (signal?: AbortSignal) => fetch(`${apiUrl}/api/v1/public/contact/`, { cache: "no-store", signal }).then(async response => { if (!response.ok) throw await responseError(response, "Contact options are unavailable."); return await response.json() as PublicContact; });
export async function createInquiry(token: () => Promise<string|null>, plan: ServicePlan, signal?: AbortSignal): Promise<Inquiry> {
  const response = await fetch(`${apiUrl}/api/v1/candidate/inquiries/`, { method: "POST", headers: { ...(await authorizationHeaders(token, signal)), "Content-Type": "application/json" }, body: JSON.stringify({ plan }), cache: "no-store", signal });
  if (!response.ok) throw await responseError(response, "We could not save your plan selection.");
  return await response.json() as Inquiry;
}
export { isSafeWhatsAppUrl } from "../app/safe-redirect";
export async function downloadResume(token: () => Promise<string|null>, id: string|number): Promise<{url:string; expires_in:number}> {
  const response = await fetch(`${apiUrl}/api/v1/resumes/${id}/download/`, {method: "POST", headers: await authorizationHeaders(token), cache: "no-store"});
  if (!response.ok) throw await responseError(response, "We could not authorize the resume download.");
  return await response.json();
}

export type CampaignPlan = "NORMAL_APPLY" | "COLD_APPLY" | "FULL_THROTTLE";
export type CampaignStatus = "DRAFT" | "ONBOARDING" | "READY" | "ACTIVE" | "PAUSED" | "COMPLETED" | "CANCELLED";
export type CampaignBillingStatus = "PENDING" | "ACTIVE" | "PAST_DUE" | "CANCELLED";

export type Campaign = {
  id: string;
  candidate_id: number;
  plan: CampaignPlan;
  status: CampaignStatus;
  start_date: string | null;
  trial_end_date: string | null;
  billing_status: CampaignBillingStatus;
  settings_json: Record<string, unknown>;
  version: number;
  created_at: string;
  updated_at: string;
};

type ApiError = {
  code?: string;
  message?: string;
  details?: unknown;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function responseError(response: Response, fallback: string): Promise<ApiRequestError> {
  const error = (await response.json().catch(() => null)) as ApiError | null;
  return new ApiRequestError(error?.message ?? fallback, response.status, error?.code, error?.details);
}

export function apiFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiRequestError) || !error.details || typeof error.details !== "object") return {};
  return Object.fromEntries(Object.entries(error.details).map(([key, value]) => [key, Array.isArray(value) ? value.join(" ") : typeof value === "string" ? value : JSON.stringify(value)]));
}

async function authorizationHeaders(getToken: () => Promise<string | null>, signal?: AbortSignal): Promise<HeadersInit> {
  const token = await getToken();
  if (signal?.aborted) {
    throw new DOMException("The request was cancelled.", "AbortError");
  }
  if (!token) {
    throw new Error("Your authentication session is not available. Please sign in again.");
  }
  return { Authorization: `Bearer ${token}` };
}

export async function getCurrentUser(
  getToken: () => Promise<string | null>,
  signal?: AbortSignal,
): Promise<CurrentUser> {
  const headers = await authorizationHeaders(getToken, signal);
  const response = await fetch(`${apiUrl}/api/v1/me/`, {
    headers,
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "The HTF API rejected the request.");
  }

  return (await response.json()) as CurrentUser;
}

export async function getCandidateProfile(
  getToken: () => Promise<string | null>,
  signal?: AbortSignal,
): Promise<CandidateProfile | null> {
  const response = await fetch(`${apiUrl}/api/v1/candidate/profile/`, {
    headers: await authorizationHeaders(getToken, signal),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "We could not load your candidate profile.");
  }

  return (await response.json()) as CandidateProfile | null;
}

export async function saveCandidateProfile(
  getToken: () => Promise<string | null>,
  draft: CandidateProfileDraft,
  profileVersion: number,
  signal?: AbortSignal,
): Promise<CandidateProfile> {
  const response = await fetch(`${apiUrl}/api/v1/candidate/profile/`, {
    method: "PATCH",
    headers: { ...(await authorizationHeaders(getToken, signal)), "Content-Type": "application/json" },
    body: JSON.stringify({ ...draft, profile_version: profileVersion }),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "We could not save your candidate profile.");
  }

  return (await response.json()) as CandidateProfile;
}

export async function getCandidateResumes(
  getToken: () => Promise<string | null>,
  signal?: AbortSignal,
): Promise<ResumeMetadata[]> {
  const response = await fetch(`${apiUrl}/api/v1/candidate/resumes/`, {
    headers: await authorizationHeaders(getToken, signal),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "We could not load your resumes.");
  }

  const resumes = await response.json();
  return Array.isArray(resumes) ? (resumes as ResumeMetadata[]) : [];
}

export async function getCampaigns(
  getToken: () => Promise<string | null>,
  signal?: AbortSignal,
): Promise<Campaign[]> {
  const response = await fetch(`${apiUrl}/api/v1/campaigns/`, {
    headers: await authorizationHeaders(getToken, signal),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "We could not load your campaigns.");
  }

  const campaigns = await response.json();
  return Array.isArray(campaigns) ? (campaigns as Campaign[]) : [];
}

export async function requestCandidateResumeUpload(
  getToken: () => Promise<string | null>,
  input: ResumeUploadRequest,
  signal?: AbortSignal,
): Promise<ResumeUploadAuthorization> {
  const response = await fetch(`${apiUrl}/api/v1/candidate/resumes/`, {
    method: "POST",
    headers: { ...(await authorizationHeaders(getToken, signal)), "Content-Type": "application/json" },
    body: JSON.stringify(input),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "We could not prepare your resume upload.");
  }

  return (await response.json()) as ResumeUploadAuthorization;
}

export async function completeCandidateResumeUpload(
  getToken: () => Promise<string | null>,
  resumeId: string | number,
  signal?: AbortSignal,
): Promise<ResumeMetadata> {
  const response = await fetch(`${apiUrl}/api/v1/candidate/resumes/${resumeId}/complete/`, {
    method: "POST",
    headers: await authorizationHeaders(getToken, signal),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw await responseError(response, "We could not verify the uploaded resume.");
  }

  return (await response.json()) as ResumeMetadata;
}

export const emptyCandidateProfileDraft: CandidateProfileDraft = {
  full_name: "",
  headline: "",
  location: "",
  experience_summary: "",
  target_roles: [],
  preferred_locations: [],
  remote_preference: "UNSPECIFIED",
  target_industries: [], expected_ctc_min: null, expected_ctc_max: null, work_authorization: "", sponsorship_requirement: "", notice_period: "", preferences_json: {},
};

export function profileToDraft(profile: CandidateProfile | null): CandidateProfileDraft {
  if (!profile) return { ...emptyCandidateProfileDraft };
  return {
    full_name: profile.full_name ?? "",
    headline: profile.headline ?? "",
    location: profile.location ?? "",
    experience_summary: profile.experience_summary ?? "",
    target_roles: profile.target_roles ?? [],
    preferred_locations: profile.preferred_locations ?? [],
    remote_preference: profile.remote_preference ?? "UNSPECIFIED",
    target_industries: profile.target_industries ?? [], expected_ctc_min: profile.expected_ctc_min == null ? null : Number(profile.expected_ctc_min), expected_ctc_max: profile.expected_ctc_max == null ? null : Number(profile.expected_ctc_max),
    work_authorization: profile.work_authorization ?? "", sponsorship_requirement: profile.sponsorship_requirement ?? "", notice_period: profile.notice_period ?? "", preferences_json: profile.preferences_json ?? {},
  };
}

export function parseCommaSeparated(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinCommaSeparated(value: string[]): string {
  return value.join(", ");
}

export function basicsComplete(draft: CandidateProfileDraft): boolean {
  return Boolean(
    draft.full_name.trim() &&
      draft.location.trim() &&
      draft.experience_summary.trim() &&
      draft.target_roles.some((role) => role.trim()),
  );
}
