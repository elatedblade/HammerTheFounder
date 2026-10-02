"use client";

import { SignInButton, UserButton, useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { getCurrentUser, type CurrentUser } from "../lib/api";

function StateCard({ eyebrow, title, body }: { eyebrow: string; title: string; body: string }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-zinc-100">
      <section className="w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-900/80 p-10 shadow-2xl shadow-zinc-950/50">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">{eyebrow}</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{title}</h1>
        <p className="mt-5 max-w-xl text-lg leading-8 text-zinc-300">{body}</p>
      </section>
    </main>
  );
}

export function SetupState() {
  return <StateCard eyebrow="Authentication setup" title="Connect Clerk to open the operations workspace" body="Set NEXT_PUBLIC_AUTH_MODE=clerk and NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY in the local environment, then restart the admin service." />;
}

export default function AuthenticatedHome() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    getCurrentUser(getToken)
      .then(setUser)
      .catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : "Unable to load your account."));
  }, [getToken, isLoaded, isSignedIn]);

  if (!isLoaded) return <StateCard eyebrow="Hammer The Founder" title="Loading your workspace" body="Checking your secure session…" />;
  if (!isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-zinc-100">
        <section className="w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-900/80 p-10 shadow-2xl shadow-zinc-950/50">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">Hammer The Founder</p>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Operations workspace</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-zinc-300">Sign in with an authorized HTF operator or administrator account.</p>
          <SignInButton mode="modal"><button className="mt-8 rounded-full bg-amber-300 px-6 py-3 font-semibold text-zinc-950">Sign in</button></SignInButton>
        </section>
      </main>
    );
  }
  if (error) return <StateCard eyebrow="Admin workspace" title="We could not load your account" body={error} />;
  if (!user) return <StateCard eyebrow="Admin workspace" title="Loading your account" body="Fetching your HTF identity from the API…" />;
  if (!(user.role === "OPERATOR" || user.role === "ADMIN" || user.role === "SUPERADMIN")) {
    return <StateCard eyebrow="Access denied" title="This account is not authorized for operations" body="Ask an HTF administrator to assign an operational role." />;
  }

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-10 text-zinc-100">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        <div><p className="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">Hammer The Founder</p><h1 className="mt-3 text-4xl font-semibold tracking-tight">Operations workspace</h1></div>
        <UserButton />
      </div>
      <section className="mx-auto mt-10 max-w-5xl rounded-3xl border border-zinc-800 bg-zinc-900/80 p-8">
        <p className="text-sm text-zinc-400">Signed in as</p>
        <p className="mt-2 text-xl font-medium">{user.email || "HTF operator"}</p>
        <p className="mt-1 text-sm text-amber-300">{user.role}</p>
        <p className="mt-4 text-zinc-300">The task queue and campaign workspace will appear here next.</p>
      </section>
    </main>
  );
}
