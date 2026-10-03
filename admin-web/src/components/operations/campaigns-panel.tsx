"use client";

import ResourcePanel from "./resource-panel";
import { isAdmin, type Field, type Resource, type WorkspaceContext } from "./types";

const plans: Field = { name: "plan", label: "Service plan", type: "select", required: true, options: ["NORMAL_APPLY", "COLD_APPLY", "FULL_THROTTLE"] };
const settings: Field = { name: "settings_json", label: "Campaign settings", type: "json" };
const trial: Field = { name: "trial_end_date", label: "Trial end date", type: "date", nullable: true };

export default function CampaignsPanel({ context }: { context: WorkspaceContext }) {
  const resource: Resource = {
    title: "Campaigns", path: "campaigns/", columns: ["candidate_name", "candidate_email", "plan", "status", "billing_status", "assigned_to"],
    description: "Lifecycle actions are validated by the server against intake, billing and current campaign state.",
    fields: [{ name: "candidate_id", label: "Candidate", lookup: "candidates", required: true }, plans, trial, settings],
    editFields: [plans, trial, settings, ...(isAdmin(context.user) ? [{ name: "assigned_to", label: "Assigned operator", lookup: "operators", nullable: true } satisfies Field] : [])],
    actions: [
      { label: "Start campaign", route: "start/", when: (row) => ["DRAFT", "ONBOARDING", "READY"].includes(String(row.status)), confirm: "Start this campaign? The API checks profile, resume and payment readiness." },
      { label: "Pause campaign", route: "pause/", when: (row) => row.status === "ACTIVE" },
      { label: "Resume campaign", route: "resume/", when: (row) => row.status === "PAUSED" },
      { label: "Complete campaign", route: "complete/", when: (row) => ["ACTIVE", "PAUSED"].includes(String(row.status)), confirm: "Mark this campaign complete? This ends its active operations." },
      { label: "Cancel campaign", route: "cancel/", when: (row) => !["COMPLETED", "CANCELLED"].includes(String(row.status)), confirm: "Cancel this campaign? This ends operations and cannot be undone through resume." },
    ],
  };
  return <ResourcePanel resource={resource} context={context} />;
}
