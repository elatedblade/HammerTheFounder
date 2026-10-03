import { SignIn } from "@clerk/nextjs";

import { clerkConfigured } from "../../auth-provider";
import { SetupState } from "../../authenticated-home";

export default function SignInPage() {
  if (!clerkConfigured) return <SetupState />;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn />
    </div>
  );
}
