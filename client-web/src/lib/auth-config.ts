export const clerkConfigured =
  process.env.NEXT_PUBLIC_AUTH_MODE !== "unconfigured" &&
  Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
