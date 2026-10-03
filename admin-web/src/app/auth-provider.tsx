"use client";

import type { ReactNode } from "react";
import { ClerkProvider } from "@clerk/nextjs";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
const authMode = process.env.NEXT_PUBLIC_AUTH_MODE ?? (publishableKey ? "clerk" : "unconfigured");

export const clerkConfigured = authMode === "clerk" && Boolean(publishableKey);

export function AuthProvider({ children }: { children: ReactNode }) {
  if (!clerkConfigured) return children;
  return <ClerkProvider publishableKey={publishableKey}>{children}</ClerkProvider>;
}
