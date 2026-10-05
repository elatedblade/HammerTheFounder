"use client";

import { MutationForm } from "./ui";
import { outreachCreateForm, outreachCreatePayload } from "./outreach-create-fields";
import type { RecordData, WorkspaceContext } from "./types";

export { outreachCreatePayload } from "./outreach-create-fields";

export default function OutreachCreate({ context, onCancel, onCreated }: { context: WorkspaceContext; onCancel: () => void; onCreated: (record: RecordData) => void }) {
  const form = outreachCreateForm(context.lookups, context.campaign);
  return <><p className="muted">Create a draft using a saved contact, or add the contact and company here. Saving creates records for review only; no external message is sent.</p><MutationForm title="Create outreach draft" {...form} submitLabel="Save outreach draft" onCancel={onCancel} onSubmit={async (values) => {
    // Unavailable existing choices are hidden, so their modes are omitted by MutationForm.
    const payload = outreachCreatePayload({ ...values, contact_mode: values.contact_mode ?? "NEW", company_mode: values.company_mode ?? "NEW" });
    const record = await context.api<RecordData>("outreach/create/", { method: "POST", body: JSON.stringify(payload) });
    context.refresh();
    onCreated(record);
  }} /></>;
}
