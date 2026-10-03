"use client";
import { SignIn } from "@clerk/nextjs";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { clerkConfigured } from "../../auth-provider";
import SetupState from "../../setup-state";
import { authCounterpartUrl, intentRedirectFromParams } from "../../safe-redirect";

function SignInForm() {
  const params = useSearchParams();
  const redirectUrl = intentRedirectFromParams(params);
  if (!clerkConfigured) return <SetupState />;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn forceRedirectUrl={redirectUrl} fallbackRedirectUrl={redirectUrl} signUpUrl={authCounterpartUrl("/sign-up", redirectUrl)} />
    </div>
  );
}

export default function SignInPage() { return <Suspense fallback={<div className="state-page" aria-busy="true" />}><SignInForm /></Suspense>; }
