import type { Field, Resource } from "./types";
import { applicationColumns, applicationOutcomeOptions, recordSubmittedAction, updateApplicationStageAction } from "./application-helpers";
import { applicationStageOptions } from "./application-stages";
import { outreachDraftStates, outreachStageOptions, outreachStatusOptions } from "./outreach-status";

const text = (name: string, label: string, required = false): Field => ({ name, label, required });
const notes: Field = { name: "notes", label: "Internal notes", type: "textarea" };
const campaign: Field = { name: "campaign", label: "Campaign", lookup: "campaigns", required: true };
const company: Field = { name: "company", label: "Company", lookup: "companies", required: true };
const assignment: Field = { name: "assigned_to", label: "Assigned operator", lookup: "operators", nullable: true };
const priority: Field = { name: "priority", label: "Priority (1 highest, 5 lowest)", type: "number", required: true, min: 1, max: 5 };
const choose = (name: string, label: string, options: string[], required = true): Field => ({ name, label, type: "select", options, required });
const templateFields = [text("name", "Template name", true), text("subject", "Subject"), { name: "body", label: "Body", type: "textarea", required: true } satisfies Field];
const companyFields: Field[] = [text("name", "Company name", true), { name: "website", label: "Website", type: "url" }, text("industry", "Industry"), text("location", "Location")];
const jobFields: Field[] = [company, text("title", "Job title", true), { name: "canonical_url", label: "Canonical job URL", type: "url" }, text("external_source", "Source"), text("external_id", "External reference"), text("location", "Location"), text("employment_type", "Employment type"), { name: "description", label: "Description", type: "textarea" }, choose("status", "Status", ["OPEN", "CLOSED", "ARCHIVED"])];
const applicationFields: Field[] = [campaign, { name: "job", label: "Job", lookup: "jobs", required: true }, notes, text("source_reference", "Submission/source reference")];
const contactFields: Field[] = [company, text("name", "Full name", true), text("title", "Title"), { name: "email", label: "Email", type: "email" }, { name: "profile_url", label: "Profile URL", type: "url" }, text("source", "Source")];
const outreachFields: Field[] = [campaign, { name: "contact", label: "Contact", lookup: "contacts", required: true }, choose("channel", "Channel", ["EMAIL", "LINKEDIN", "WHATSAPP"]), text("subject", "Subject"), { name: "body", label: "Message body", type: "textarea", required: true }, { name: "follow_up_due_at", label: "Follow-up due", type: "datetime-local", nullable: true }, text("thread_reference", "Thread reference"), notes];
const interviewDate: Field = { name: "interview_scheduled_at", label: "Interview date & time (your local timezone)", type: "datetime-local", future: true, help: "Choose a future time. HTF sends it to the API as a timezone-aware UTC timestamp." };

export const companies: Resource = { title: "Companies", path: "companies/", paginated: true, columns: ["name", "industry", "location", "website"], fields: companyFields, editFields: companyFields };
export const jobs: Resource = { title: "Jobs", path: "jobs/", paginated: true, columns: ["title", "company_name", "location", "status", "external_source"], fields: jobFields, editFields: jobFields };
export const applications: Resource = {
  title: "Applications", path: "applications/", paginated: true, stageOptions: applicationStageOptions, columns: applicationColumns, scoped: true,
  description: "Record submissions only after applying externally. Track each application through Saved, In progress, Under review, Interviews and Offers. This workspace never submits applications externally.",
  editFields: [notes, text("source_reference", "Submission/source reference")],
  actions: [recordSubmittedAction,
    updateApplicationStageAction,
    { label: "Record exception / retry", route: "transition/", when: (row) => applicationOutcomeOptions(row).length > 0, fields: (row) => [{ name: "status", label: "Outcome", type: "select", required: true, options: applicationOutcomeOptions(row) }, { ...notes, requiredWhen: (values) => values.status === "APPLICATION_FAILED", help: "Failure requires an explanation for the server-generated human review task." }] },
    { label: "Schedule interview", route: "transition/", body: { status: "INTERVIEW_SCHEDULED" }, when: (row) => row.status === "INTERVIEW", fields: [{ ...interviewDate, required: true }, notes], confirm: "Schedule this interview and record its agreed future time? The API will create an interview confirmation task." },
    { label: "Reschedule interview", route: "", method: "PATCH", when: (row) => row.status === "INTERVIEW_SCHEDULED", fields: [{ ...interviewDate, required: true }, notes], confirm: "Save this rescheduled future interview time? Confirm the change is agreed with the candidate and interviewer." }],
};
export const contacts: Resource = { title: "Contacts", path: "contacts/", paginated: true, columns: ["name", "company_name", "title", "email", "source"], fields: contactFields, editFields: contactFields };
export const outreach: Resource = {
  title: "Outreach", path: "outreach/", paginated: true, stageOptions: outreachStageOptions, columns: ["contact_name", "company_name", "channel", "status", "sent_at", "delivered_at", "bounced_at", "reply_at", "follow_up_due_at"], scoped: true,
  description: "Draft messages here; send cold outreach manually outside HTF. Check suppression before sending, then update status to Sent or Responded after it happens externally.", fields: outreachFields, editFields: (row) => outreachFields.filter((field) => !["campaign", "contact", "channel", ...(!outreachDraftStates.includes(String(row.status)) ? ["body", "subject"] : [])].includes(field.name)),
  actions: [{ label: "Update status", route: "transition/", when: (row) => outreachStatusOptions(row).length > 0, fields: (row) => [{ name: "status", label: "New status", type: "select", required: true, options: outreachStatusOptions(row) }, notes], confirm: "Record this manual outreach status? Confirm the message was sent or the response received outside HTF. This only updates the saved status. This does not send a message." }],
};
export const suppression: Resource = { title: "Suppression list", path: "suppression/", paginated: true, columns: ["email", "reason", "created_at"], description: "Do not contact these addresses. New suppression records take effect server-side.", createConfirm: "Suppress this email address? Pending outreach to this contact will be blocked.", fields: [{ name: "email", label: "Email to suppress", type: "email", required: true }, text("reason", "Reason", true)] };
export const outreachTemplates: Resource = { title: "Outreach templates", path: "outreach/templates/", paginated: true, columns: ["name", "subject", "body"], fields: templateFields, description: "Reference copy only. Creating a template never sends outreach." };
export const tasks: Resource = {
  title: "Operator tasks", path: "admin/tasks/", paginated: true, columns: ["task_type", "priority", "status", "assigned_to", "payload_json", "created_at"], scoped: true, description: "Includes server-generated fit, contact verification, failure, outreach review and interview confirmation tasks. Open a task to inspect its entity reference; review the source record before completing the task.",
  fields: [campaign, text("task_type", "Task type", true), priority, { name: "payload_json", label: "Task instructions (JSON)", type: "json", help: "Use an object such as {\"instructions\":\"Review role matches\"}." }],
  adminEdit: true, editFields: [assignment, priority],
  actions: [{ label: "Claim task", route: "claim/", when: (row) => row.status === "OPEN", confirm: "Assign this task to your account?" }, { label: "Complete task", route: "complete/", fields: [notes], when: (row) => row.status === "CLAIMED", confirm: "Mark this task completed? Confirm its work has been finished." }],
};
export const payments: Resource = {
  title: "Manual payments", path: "billing/payments/", scoped: true, paginated: true, pageSize: 200, columns: ["amount", "currency", "status", "reference", "verified_at"], description: "Record manual receipts. Showing a paged array; only administrators can verify or record refunds; HTF does not move funds.",
  fields: [campaign, { name: "amount", label: "Amount", type: "number", required: true, min: 0.01 }, choose("currency", "Currency", ["INR"]), notes],
  actions: [{ label: "Verify receipt", route: "verify/", admin: true, fields: [text("reference", "Verified receipt reference", true), notes], when: (row) => row.status === "PENDING", confirm: "Confirm you independently checked the receipt and amount?" }, { label: "Record failed payment", route: "transition/", admin: true, body: { status: "FAILED" }, fields: [notes], when: (row) => row.status === "PENDING" }, { label: "Record refund", route: "transition/", admin: true, body: { status: "REFUNDED" }, fields: [notes], when: (row) => row.status === "VERIFIED", confirm: "Confirm the refund has already been performed outside HTF? This only records the refund." }],
};
export const inquiries: Resource = {
  title: "Customer inquiries", path: "admin/inquiries/", paginated: true,
  statusOptions: ["OPEN", "CONTACTED", "CONVERTED", "CLOSED"],
  columns: ["reference", "customer_name", "customer_email", "plan", "status", "created_at", "campaign_id"],
  description: "Saved customer plan requests. Opening WhatsApp is a manual handoff; conversion never starts or charges a campaign. After conversion, use the Campaigns tab to review or start it explicitly.",
  adminEdit: true,
  editFields: [notes],
  actions: [
    { label: "Mark contacted / close", route: "", method: "PATCH", admin: false, fields: [choose("status", "Next status", ["CONTACTED", "CLOSED"]), notes], when: (row) => row.status === "OPEN" || row.status === "CONTACTED", confirm: "Record this inquiry follow-up? This does not send WhatsApp." },
    { label: "Convert to campaign", route: "convert/", admin: true, when: (row) => row.status !== "CONVERTED" && row.status !== "CLOSED", confirm: "Create the linked campaign? This will not start the campaign or charge the customer." },
  ],
};
export const notifications: Resource = {
  title: "Transactional communications", path: "notifications/", scoped: true, paginated: true, pageSize: 200, columns: ["channel", "status", "subject", "created_at", "sent_at"],
  description: "Create a notification, then explicitly send transactional email to the campaign customer's saved email or record a WhatsApp message sent manually. Not for cold outreach. Reconcile failed/unknown delivery with the provider before creating another draft.",
  fields: [campaign, choose("channel", "Channel", ["EMAIL", "WHATSAPP"]), text("recipient", "Recipient address / phone", true), text("subject", "Subject"), { name: "body", label: "Body", type: "textarea", required: true }],
  actions: [{ label: "Send transactional email", route: "send/", when: (row) => row.channel === "EMAIL" && row.status === "DRAFT", confirm: "Send this transactional email to the saved recipient now? This is an external action." }, { label: "Record manual WhatsApp send", route: "mark-sent/", when: (row) => row.channel === "WHATSAPP" && row.status === "DRAFT", confirm: "Confirm this WhatsApp message has already been sent manually?" }],
};
export const notificationTemplates: Resource = { title: "Notification templates", path: "notifications/templates/", columns: ["name", "channel", "subject", "body"], fields: [templateFields[0], choose("channel", "Channel", ["EMAIL", "WHATSAPP"]), ...templateFields.slice(1)] };
export const aiRuns: Resource = {
  title: "AI proposals", path: "ai/runs/", scoped: true, fetchDetail: true, createConfirm: "Queue this AI assistance request? It may send the supplied context to the configured AI provider and incur usage. Results will be proposals only.", columns: ["capability", "status", "created_at", "error_code"], description: "Run assistance explicitly. Results are proposals only: review them before manually applying any changes. Open a run and refresh to check queued/running results.",
};
