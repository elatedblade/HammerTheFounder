export type CurrentUser = {
  id: number;
  email: string;
  phone: string;
  role: "CLIENT" | "OPERATOR" | "ADMIN" | "SUPERADMIN";
  identity_provider: string;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getCurrentUser(
  getToken: () => Promise<string | null>,
): Promise<CurrentUser> {
  return createApiClient(getToken)<CurrentUser>("me/");
}

export class ApiError extends Error {
  details?: Record<string, string[] | string>;
  constructor(public status: number, message: string, details?: Record<string, string[] | string>) {
    super(message); this.name = "ApiError"; this.details = details;
  }
}

export type ApiClient = <T = unknown>(path: string, init?: RequestInit) => Promise<T>;

export type ParsedResumeTextDto = { id: string; parse_status: string; text: string; truncated: boolean; max_chars: number; parsed_at: string | null };

export function createApiClient(getToken: () => Promise<string | null>): ApiClient {
  return async <T>(path: string, init: RequestInit = {}) => {
    const token = await getToken();
    if (!token) throw new Error("Your authentication session is not available.");
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);
    if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const response = await fetch(`${apiUrl}/api/v1/${path.replace(/^\//, "")}`, { ...init, headers, cache: "no-store" });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const error = body as { message?: string; details?: Record<string, string[] | string> } | null;
      throw new ApiError(response.status, error?.message ?? `Request failed (${response.status})`, error?.details);
    }
    return body as T;
  };
}
