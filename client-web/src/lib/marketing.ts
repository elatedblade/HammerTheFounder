export type ServicePlan = {
  id: "NORMAL_APPLY" | "COLD_APPLY" | "FULL_THROTTLE";
  name: string;
  summary: string;
  features: string[];
};

/** Public plan copy. Keep identifiers stable: workspace inquiry flow imports this list. */
export const SERVICE_PLANS: ServicePlan[] = [
  {
    id: "NORMAL_APPLY",
    name: "Normal Apply",
    summary: "A human-run application search built around the roles you actually want.",
    features: [
      "Role and company targeting from your profile",
      "Human-reviewed job discovery and applications",
      "Clear activity and status updates in your dashboard",
    ],
  },
  {
    id: "COLD_APPLY",
    name: "Cold Apply",
    summary: "A dedicated founder and CXO outreach campaign for a more direct conversation about your next role.",
    features: [
      "Founder and CXO outreach research",
      "Human-reviewed outreach drafts and follow-up tracking",
      "Manually recorded messages and replies in your dashboard",
    ],
  },
  {
    id: "FULL_THROTTLE",
    name: "Full-Throttle Sprint",
    summary: "Managed job applications and founder/CXO outreach, coordinated together around your search direction.",
    features: [
      "Applications and founder outreach",
      "The application and outreach workflows in one campaign",
      "One place to review progress, replies, and next actions",
    ],
  },
];

export const MARKETING_COPY = {
  eyebrow: "A human-operated job search service",
  title: "Make your next move easier to find.",
  intro:
    "Hammer The Founder helps ambitious professionals run a deliberate job search across applications and founder outreach—while real people handle the work and keep you in the loop.",
  limitations:
    "We do not promise interviews or offers. Employers decide outcomes; HTF owns the quality and visibility of the search work.",
};
