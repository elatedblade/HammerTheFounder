"use client";

import type { ReactNode } from "react";
import { ClerkProvider } from "@clerk/nextjs";

import { clerkConfigured, publishableKey } from "../lib/auth-config";

export { clerkConfigured } from "../lib/auth-config";

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
