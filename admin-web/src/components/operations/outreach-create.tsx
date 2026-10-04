"use client";

import { MutationForm } from "./ui";
import type { Field, RecordData, WorkspaceContext } from "./types";

const newContact = (v: Record<string, string>) => v.contact_mode === "NEW";
const newCompany = (v: Record<string, string>) => newContact(v) && v.company_mode === "NEW";
const fields: Field[] = [
  { name: "campaign", label: "Campaign", lookup: "campaigns", required: true },
  { name: "contact_mode", label: "Contact", type: "select", options: ["EXISTING", "NEW"], required: true },
  { name: "contact", label: "Existing contact", lookup: "contacts", visibleWhen: (v) => !newContact(v), required: true },
  { name: "company_mode", label: "Company", type: "select", options: ["EXISTING", "NEW"], visibleWhen: newContact, required: true },
  { name: "company", label: "Existing company", lookup: "companies", visibleWhen: (v) => newContact(v) && !newCompany(v), required: true },
  { name: "company_name", label: "Company name", visibleWhen: newCompany, required: true },
  { name: "company_website", label: "Company website", type: "url", visibleWhen: newCompany },
  { name: "company_industry", label: "Industry", visibleWhen: newCompany },
  { name: "company_location", label: "Company location", visibleWhen: newCompany },
  { name: "contact_name", label: "Contact name", visibleWhen: newContact, required: true },
  { name: "contact_title", label: "Contact title", visibleWhen: newContact },
  { name: "contact_email", label: "Contact email", type: "email", visibleWhen: newContact },
  { name: "contact_profile_url", label: "Contact profile URL", type: "url", visibleWhen: newContact },
  { name: "contact_source", label: "Contact source", visibleWhen: newContact },
  { name: "channel", label: "Channel", type: "select", options: ["EMAIL", "LINKEDIN", "WHATSAPP"], required: true },
  { name: "subject", label: "Subject" },
  { name: "body", label: "Message", type: "textarea", required: true },
  { name: "notes", label: "Internal notes", type: "textarea" },
];

export function outreachCreatePayload(values: Record<string, unknown>) {
  const payload: Record<string, unknown> = { campaign: values.campaign, channel: values.channel, subject: values.subject, body: values.body, notes: values.notes };
  if (values.contact_mode === "NEW") {
    payload.contact_data = { name: values.contact_name, title: values.contact_title, email: values.contact_email, profile_url: values.contact_profile_url, source: values.contact_source };
    if (values.company_mode === "NEW") payload.company_data = { name: values.company_name, website: values.company_website, industry: values.company_industry, location: values.company_location };
    else payload.company = values.company;
  } else payload.contact = values.contact;
  return payload;
}

export default function OutreachCreate({ context, onCancel, onCreated }: { context: WorkspaceContext; onCancel: () => void; onCreated: (record: RecordData) => void }) {
  return <MutationForm title="Create outreach draft" fields={fields} lookups={context.lookups} initial={{ campaign: context.campaign, contact_mode: "EXISTING", company_mode: "NEW", channel: "EMAIL" }} submitLabel="Save outreach draft" onCancel={onCancel} onSubmit={async (values) => {
    const record = await context.api<RecordData>("outreach/create/", { method: "POST", body: JSON.stringify(outreachCreatePayload(values)) });
    context.refresh();
    onCreated(record);
  }} />;
}
