"use client";

import type { ReactNode } from "react";
import { ClerkProvider } from "@clerk/nextjs";
import { clerkConfigured } from "../lib/auth-config";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
const authMode = process.env.NEXT_PUBLIC_AUTH_MODE ?? (publishableKey ? "clerk" : "unconfigured");

export { clerkConfigured };

export function AuthProvider({ children }: { children: ReactNode }) {
  if (!clerkConfigured) return children;
  return (
    <ClerkProvider
      publishableKey={publishableKey}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInFallbackRedirectUrl="/workspace"
      signUpFallbackRedirectUrl="/workspace"
      afterSignOutUrl="/"
    >
      {children}
    </ClerkProvider>
  );
}
