"use client";
import { Suspense } from "react";
import dynamic from "next/dynamic";
import { useSession, useUser } from "@clerk/nextjs";
import { clerkConfigured } from "./auth-provider";
import SetupState from "./setup-state";
import ProfileScreen from "./profile/profile-screen";
import DashboardScreen from "./dashboard/dashboard-screen";
const PlansScreen = dynamic(() => import("./plans/plans-screen"), { loading: () => <p role="status">Loading plans…</p> });

export default function AuthenticatedRoute({ page }: { page: "profile" | "dashboard" | "plans" }) {
  if (!clerkConfigured) return <SetupState />;
  return <IdentityKeyedRoute page={page} />;
}

function IdentityKeyedRoute({ page }: { page: "profile" | "dashboard" | "plans" }) {
  const { user } = useUser();
  const { session } = useSession();
  const key = `${user?.id ?? "signed-out"}:${session?.id ?? "none"}`;
  return <Suspense fallback={<div className="state-page" aria-busy="true"><p className="muted">Loading your workspace…</p></div>}>{page === "profile" ? <ProfileScreen key={key} /> : page === "plans" ? <PlansScreen key={key} /> : <DashboardScreen key={key} />}</Suspense>;
}
