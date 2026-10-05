export type ServicePlan = {
  id: "NORMAL_APPLY" | "COLD_APPLY" | "FULL_THROTTLE";
  name: string;
  summary: string;
  features: string[];
  applicationsPerDay: number;
  coldMailsPerDay: number;
  pricePerWeek: number;
};

/** Public plan copy. Keep identifiers stable: workspace inquiry flow imports this list. */
export const SERVICE_PLANS: ServicePlan[] = [
  {
    id: "NORMAL_APPLY",
    name: "Normal Apply",
    summary: "Human-led applications and outreach for your next role.",
    applicationsPerDay: 10,
    coldMailsPerDay: 2,
    pricePerWeek: 349,
    features: [
      "Human-reviewed applications and cold mails",
      "Progress updates in your dashboard",
    ],
  },
  {
    id: "COLD_APPLY",
    name: "Better Apply",
    summary: "More applications and outreach, with human follow-through.",
    applicationsPerDay: 15,
    coldMailsPerDay: 5,
    pricePerWeek: 549,
    features: [
      "Human-reviewed applications and cold mails",
      "Reply and follow-up tracking",
    ],
  },
  {
    id: "FULL_THROTTLE",
    name: "Full Throttle",
    summary: "Our widest daily coverage for your search.",
    applicationsPerDay: 25,
    coldMailsPerDay: 10,
    pricePerWeek: 749,
    features: [
      "Human-reviewed applications and cold mails",
      "Coordinated progress and follow-up",
    ],
  },
];

export const MARKETING_COPY = {
  eyebrow: "Human-led applications, without the busywork",
  title: "You go chill. We’ll apply.",
  intro:
    "You bring the direction. We find the fit, tailor the work, and keep watch after send—so your search moves while your time comes back.",
};
