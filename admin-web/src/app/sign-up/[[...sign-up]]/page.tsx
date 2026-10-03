import { SignUp } from "@clerk/nextjs";

import { clerkConfigured } from "../../auth-provider";
import { SetupState } from "../../authenticated-home";

export default function SignUpPage() {
  if (!clerkConfigured) return <SetupState />;
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 px-6">
      <p className="max-w-md text-center text-sm text-zinc-500">Creating an account does not grant an operational role. Ask an HTF administrator for access after signing up.</p>
      <SignUp />
    </div>
  );
}
