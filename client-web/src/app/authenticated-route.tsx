"use client";
import { Suspense } from "react";
import { useSession, useUser } from "@clerk/nextjs";
import { clerkConfigured } from "./auth-provider";
import SetupState from "./setup-state";
import ProfileScreen from "./profile/profile-screen";
import DashboardScreen from "./dashboard/dashboard-screen";

export default function AuthenticatedRoute({ page }: { page: "profile" | "dashboard" }) {
  if (!clerkConfigured) return <SetupState />;
  return <IdentityKeyedRoute page={page} />;
}

function IdentityKeyedRoute({ page }: { page: "profile" | "dashboard" }) {
  const { user } = useUser();
  const { session } = useSession();
  const key = `${user?.id ?? "signed-out"}:${session?.id ?? "none"}`;
  return <Suspense fallback={<div className="state-page" aria-busy="true"><p className="muted">Loading your workspace…</p></div>}>{page === "profile" ? <ProfileScreen key={key} /> : <DashboardScreen key={key} />}</Suspense>;
}
