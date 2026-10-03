import type { Campaign, CandidateProfile, Inquiry } from "../../lib/api";

export type LifecyclePresentation = {
  kind: "loading" | "error" | "none" | "active" | "ready" | "onboarding" | "draft" | "paused" | "historical";
  headline: string;
  detail: string;
  showChoosePlan: boolean;
  showPlansLink: boolean;
  showProfileAction: boolean;
};

type Input = {
  campaigns?: Campaign[] | null;
  campaignsLoading?: boolean;
  campaignsError?: boolean;
  inquiry?: Inquiry | null;
  profile?: CandidateProfile | null;
};

/** Campaign state is authoritative over acquisition/profile prompts. */
export function getLifecyclePresentation(input: Input): LifecyclePresentation {
  if (input.campaignsLoading) return { kind: "loading", headline: "Loading campaign status", detail: "Your campaign records are being loaded.", showChoosePlan: false, showPlansLink: false, showProfileAction: false };
  if (input.campaignsError) return { kind: "error", headline: "Campaign status unavailable", detail: "We could not load campaign status. Try again; this is not treated as an empty workspace.", showChoosePlan: false, showPlansLink: false, showProfileAction: false };
  if (!input.campaigns) return { kind: "loading", headline: "Loading campaign status", detail: "Waiting for verified campaign records.", showChoosePlan: false, showPlansLink: false, showProfileAction: false };
  const campaigns = input.campaigns ?? [];
  const active = campaigns.find((campaign) => campaign.status === "ACTIVE");
  if (active) return { kind: "active", headline: `${active.plan.replaceAll("_", " ")} · Active`, detail: "Status: active. Progress and submitted records are shown below; choosing a plan cannot change this campaign.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  const current = ["READY", "ONBOARDING", "DRAFT", "PAUSED"].map((status) => campaigns.find((campaign) => campaign.status === status)).find(Boolean);
  if (current?.status === "READY") return { kind: "ready", headline: "Your campaign is ready to start", detail: "HTF has the campaign ready. Start remains an explicit team action after readiness checks.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  if (current?.status === "ONBOARDING") return { kind: "onboarding", headline: "Your campaign is being set up", detail: "The HTF team is completing onboarding before work begins.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  if (current?.status === "DRAFT") return { kind: "draft", headline: "Your campaign is being prepared", detail: "The HTF team will confirm the next setup step with you.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  if (current?.status === "PAUSED") return { kind: "paused", headline: "Your campaign is paused", detail: "HTF has paused this campaign. Contact the team to discuss resuming it; this page will not start a new inquiry.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  const historical = campaigns.find((campaign) => ["COMPLETED", "CANCELLED"].includes(campaign.status));
  if (historical) return { kind: "historical", headline: "Your previous campaign is on record", detail: "You can review its history or discuss another search with HTF.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  if (input.inquiry?.status === "OPEN") return { kind: "none", headline: "Continue your search conversation", detail: "Your saved inquiry is ready for the next conversation with HTF.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  if (input.inquiry && ["CONTACTED", "CONVERTED"].includes(input.inquiry.status)) return { kind: "none", headline: "HTF is handling your request", detail: "Your plan discussion or campaign setup is in progress. This is not an active campaign until HTF explicitly starts it.", showChoosePlan: false, showPlansLink: true, showProfileAction: false };
  if (input.profile && !input.profile.basics_complete) return { kind: "none", headline: "Complete your profile", detail: "Add your search direction so HTF can prepare the right next step.", showChoosePlan: false, showPlansLink: true, showProfileAction: true };
  return { kind: "none", headline: "Choose a plan to discuss your search", detail: "Your selection starts an inquiry only. It does not activate or modify a campaign.", showChoosePlan: true, showPlansLink: true, showProfileAction: false };
}
