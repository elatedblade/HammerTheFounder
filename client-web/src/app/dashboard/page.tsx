import { redirect } from "next/navigation";
import AuthenticatedRoute from "../authenticated-route";
import { selectedPlan } from "../plans/plan-helpers";

export default async function DashboardPage({ searchParams }: { searchParams: Promise<{ plan?: string }> }) {
  const plan = selectedPlan((await searchParams).plan ?? null);
  if (plan) redirect(`/plans?plan=${plan}`);
  return <AuthenticatedRoute page="dashboard" />;
}
