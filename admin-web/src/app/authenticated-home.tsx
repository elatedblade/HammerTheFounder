"use client";

import { SignInButton, SignUpButton, UserButton, useAuth } from "@clerk/nextjs";
import { useEffect, useMemo, useState } from "react";

import { createApiClient, getCurrentUser, type CurrentUser } from "../lib/api";
import OperationsWorkspace from "../components/operations/workspace";

function StateCard({ eyebrow, title, body, children }: { eyebrow: string; title: string; body: string; children?: React.ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-zinc-100">
      <section className="w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-900/80 p-10 shadow-2xl shadow-zinc-950/50">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">{eyebrow}</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{title}</h1>
        <p className="mt-5 max-w-xl text-lg leading-8 text-zinc-300">{body}</p>
        {children && <div className="mt-6 flex items-center gap-5">{children}</div>}
      </section>
    </main>
  );
}

export function SetupState() {
  return <StateCard eyebrow="Authentication setup" title="Connect Clerk to open the operations workspace" body="Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY (and optionally NEXT_PUBLIC_AUTH_MODE=clerk) in the local environment, then restart the admin service." />;
}

export default function AuthenticatedHome() {
  const { getToken, isLoaded, isSignedIn, userId } = useAuth();
  const api = useMemo(() => createApiClient(getToken), [getToken]);
  const [retry, setRetry] = useState(0);
  const requestKey = `${userId}:${retry}:${isSignedIn}:${isLoaded}`;
  const [account, setAccount] = useState<{ key: string; user: CurrentUser | null; error: string | null }>({ key: "", user: null, error: null });
  const user = account.key === requestKey ? account.user : null;
  const error = account.key === requestKey ? account.error : null;

  useEffect(() => {
    let active = true;
    if (!isLoaded || !isSignedIn) return;
    getCurrentUser(getToken)
      .then((user) => { if (active) setAccount({ key: requestKey, user, error: null }); })
      .catch((requestError: unknown) => { if (active) setAccount({ key: requestKey, user: null, error: requestError instanceof Error ? requestError.message : "Unable to load your account." }); });
    return () => { active = false; };
  }, [getToken, isLoaded, isSignedIn, requestKey]);

  if (!isLoaded) return <StateCard eyebrow="Hammer The Founder" title="Loading your workspace" body="Checking your secure session…" />;
  if (!isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-zinc-100">
        <section className="w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-900/80 p-10 shadow-2xl shadow-zinc-950/50">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">Hammer The Founder</p>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Operations workspace</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-zinc-300">Sign in with an authorized HTF operator or administrator account.</p>
           <div className="mt-8 flex flex-wrap gap-4">
             <SignInButton mode="modal"><button className="rounded-full bg-amber-300 px-6 py-3 font-semibold text-zinc-950">Sign in</button></SignInButton>
             <SignUpButton mode="modal"><button className="rounded-full border border-zinc-600 px-6 py-3 font-semibold text-zinc-100">Create account</button></SignUpButton>
           </div>
           <p className="mt-5 text-sm text-zinc-400">Creating an account does not grant an operational role. Access still requires authorization from an HTF administrator.</p>
        </section>
      </main>
    );
  }
  if (error) return <StateCard eyebrow="Admin workspace" title="We could not load your account" body={error}><button onClick={() => setRetry((value) => value + 1)} className="rounded bg-amber-300 px-4 py-2 font-semibold text-zinc-950">Retry</button><UserButton /></StateCard>;
  if (!user) return <StateCard eyebrow="Admin workspace" title="Loading your account" body="Fetching your HTF identity from the API…" />;
  if (!(user.role === "OPERATOR" || user.role === "ADMIN" || user.role === "SUPERADMIN")) {
    return <StateCard eyebrow="Access denied" title="This account is not authorized for operations" body="Ask an HTF administrator to assign an operational role."><UserButton /></StateCard>;
  }

  return <OperationsWorkspace key={user.id} user={user} api={api} />;
}
