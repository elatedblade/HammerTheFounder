"use client";
import { SignUp } from "@clerk/nextjs";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { clerkConfigured } from "../../auth-provider";
import SetupState from "../../setup-state";
import { authCounterpartUrl, intentRedirectFromParams } from "../../safe-redirect";

function SignUpForm() {
  const params = useSearchParams();
  const redirectUrl = intentRedirectFromParams(params);
  if (!clerkConfigured) return <SetupState />;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp forceRedirectUrl={redirectUrl} fallbackRedirectUrl={redirectUrl} signInUrl={authCounterpartUrl("/sign-in", redirectUrl)} />
    </div>
  );
}

export default function SignUpPage() { return <Suspense fallback={<div className="state-page" aria-busy="true" />}><SignUpForm /></Suspense>; }
