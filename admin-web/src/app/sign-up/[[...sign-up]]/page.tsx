"use client";

import { SignUp } from "@clerk/nextjs";
import { clerkConfigured } from "../../auth-provider";
import { SetupState } from "../../authenticated-home";

export default function SignUpPage() {
  if (!clerkConfigured) return <SetupState />;
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </div>
  );
}
