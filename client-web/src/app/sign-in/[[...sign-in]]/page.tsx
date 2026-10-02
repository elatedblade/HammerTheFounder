import { SignIn } from "@clerk/nextjs";

import { clerkConfigured } from "../../../lib/auth-config";
import { SetupState } from "../../authenticated-home";

export default function SignInPage() {
  if (!clerkConfigured) return <SetupState />;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn />
    </div>
  );
}
