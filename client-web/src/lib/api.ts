export type CurrentUser = {
  id: number;
  email: string;
  phone: string;
  role: "CLIENT" | "OPERATOR" | "ADMIN" | "SUPERADMIN";
  identity_provider: string;
};

type ApiError = {
  code?: string;
  message?: string;
  details?: unknown;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getCurrentUser(
  getToken: () => Promise<string | null>,
): Promise<CurrentUser> {
  const token = await getToken();
  if (!token) {
    throw new Error("Your authentication session is not available.");
  }

  const response = await fetch(`${apiUrl}/api/v1/me/`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!response.ok) {
    const error = (await response.json().catch(() => null)) as ApiError | null;
    throw new Error(error?.message ?? "The HTF API rejected the request.");
  }

  return (await response.json()) as CurrentUser;
}
