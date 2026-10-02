export const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export const clerkConfigured =
  process.env.NEXT_PUBLIC_AUTH_MODE !== "unconfigured" && Boolean(publishableKey);
