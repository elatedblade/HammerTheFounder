import { SignUp } from "@clerk/nextjs";

import { clerkConfigured } from "../../../lib/auth-config";
import { SetupState } from "../../authenticated-home";

export default function SignUpPage() {
  if (!clerkConfigured) return <SetupState />;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp />
    </div>
  );
}
