"use client";

import { useEffect, type ReactNode } from "react";
import { ClerkProvider, useAuth } from "@clerk/nextjs";
import { clerkConfigured } from "../lib/auth-config";
import { getCurrentUser } from "../lib/api";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
export { clerkConfigured };

function IdentitySync() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    const controller = new AbortController();
    getCurrentUser(getToken, controller.signal).catch(() => {
      // The signed-in shell will surface API failures where they affect the user.
    });
    return () => controller.abort();
  }, [getToken, isLoaded, isSignedIn]);

  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  if (!clerkConfigured) {
    return children;
  }

  return (
    <ClerkProvider publishableKey={publishableKey} signInUrl="/sign-in" signUpUrl="/sign-up">
      <IdentitySync />
      {children}
    </ClerkProvider>
  );
}
