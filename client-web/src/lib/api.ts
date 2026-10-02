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
>;

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

type ApiError = {
  code?: string;
  message?: string;
  details?: unknown;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

async function responseError(response: Response, fallback: string): Promise<ApiRequestError> {
  const error = (await response.json().catch(() => null)) as ApiError | null;
  return new ApiRequestError(error?.message ?? fallback, response.status, error?.code);
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
