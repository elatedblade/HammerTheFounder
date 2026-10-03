export type IntentPlan = "NORMAL_APPLY" | "COLD_APPLY" | "FULL_THROTTLE";
const plans = new Set<IntentPlan>(["NORMAL_APPLY", "COLD_APPLY", "FULL_THROTTLE"]);

export function safeCustomerRedirect(value: string | null | undefined): string {
  if (!value) return "/dashboard";
  try {
    const url = new URL(value, "https://local.invalid");
    if (url.origin !== "https://local.invalid" || !["/dashboard", "/profile"].includes(url.pathname)) return "/dashboard";
    const plan = url.searchParams.get("plan");
    return url.pathname + (plan && plans.has(plan as IntentPlan) ? `?plan=${encodeURIComponent(plan)}` : "");
  } catch { return "/dashboard"; }
}

export function intentRedirectFromParams(params: URLSearchParams): string {
  return safeCustomerRedirect(params.get("redirect_url") ?? (params.get("plan") ? `/dashboard?plan=${params.get("plan")}` : "/dashboard"));
}

export function authCounterpartUrl(path: "/sign-in" | "/sign-up", redirect: string): string {
  return `${path}?redirect_url=${encodeURIComponent(safeCustomerRedirect(redirect))}`;
}

export function isSafeWhatsAppUrl(value: unknown): value is string {
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.hostname === "wa.me" && !url.port
      && /^\/[1-9][0-9]{7,14}$/.test(url.pathname) && !url.username && !url.password;
  } catch { return false; }
}
