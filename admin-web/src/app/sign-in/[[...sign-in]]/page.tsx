import { SignIn } from "@clerk/nextjs";

import { clerkConfigured } from "../../auth-provider";
import { SetupState } from "../../authenticated-home";

export default function SignInPage() {
  if (!clerkConfigured) return <SetupState />;
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 px-6">
      <p className="max-w-md text-center text-sm text-zinc-500">Sign in with an authorized HTF operator or administrator account.</p>
      <SignIn />
    </div>
  );
}
