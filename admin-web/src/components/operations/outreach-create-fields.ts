import type { Field, Option } from "./types";

export function outreachCreateForm(lookups: Record<string, Option[]>, campaign: string) {
  const contacts = lookups.contacts ?? [];
  const companies = lookups.companies ?? [];
  const campaigns = lookups.campaigns ?? [];
  const newContact = (values: Record<string, string>) => !contacts.length || values.contact_mode === "NEW";
  const newCompany = (values: Record<string, string>) => newContact(values) && (!companies.length || values.company_mode === "NEW");
  const fields: Field[] = [
    { name: "campaign", label: "Campaign for this draft", lookup: "campaigns", required: true, help: campaigns.length ? "Choose the campaign this outreach belongs to." : "No campaigns are available. Create a campaign or retry loading options before saving." },
    { name: "contact_mode", label: "Who is this draft for?", lookup: "outreach_contact_modes", required: true, visibleWhen: () => contacts.length > 0, help: "Reuse a saved contact or create one here with this draft." },
    { name: "contact", label: "Saved contact", lookup: "contacts", visibleWhen: (values) => !newContact(values), required: true, help: "The draft uses this contact and their existing company." },
    { name: "company_mode", label: "Company for the new contact", lookup: "outreach_company_modes", visibleWhen: (values) => newContact(values) && companies.length > 0, required: true, help: "Reuse a saved company to avoid duplicates, or create one here." },
    { name: "company", label: "Saved company", lookup: "companies", visibleWhen: (values) => newContact(values) && !newCompany(values), required: true },
    { name: "company_name", label: "New company name", visibleWhen: newCompany, required: true, help: companies.length ? "This company will be saved with the contact and draft." : "No saved companies are available. Create the company here with this draft." },
    { name: "company_website", label: "Company website", type: "url", visibleWhen: newCompany },
    { name: "company_industry", label: "Company industry", visibleWhen: newCompany },
    { name: "company_location", label: "Company location", visibleWhen: newCompany },
    { name: "contact_name", label: "New contact name", visibleWhen: newContact, required: true, help: contacts.length ? "This contact will be saved with the draft." : "No saved contacts are available. Create the contact here with this draft." },
    { name: "contact_title", label: "Contact job title", visibleWhen: newContact },
    { name: "contact_email", label: "Contact email", type: "email", visibleWhen: newContact },
    { name: "contact_profile_url", label: "Contact profile URL", type: "url", visibleWhen: newContact },
    { name: "contact_source", label: "Contact source", visibleWhen: newContact, help: "Optional: where you found this contact." },
    { name: "channel", label: "Intended channel", type: "select", options: ["EMAIL", "LINKEDIN", "WHATSAPP"], required: true, help: "For planning only. Saving this draft does not send a message." },
    { name: "subject", label: "Draft subject (optional)" },
    { name: "body", label: "Draft message", type: "textarea", required: true, help: "Save text for operator review. No external message is sent." },
    { name: "notes", label: "Internal notes (optional)", type: "textarea" },
  ];
  return {
    fields,
    lookups: {
      ...lookups,
      outreach_contact_modes: [...(contacts.length ? [{ value: "EXISTING", label: "Use a saved contact" }] : []), { value: "NEW", label: "Create a contact here" }],
      outreach_company_modes: [...(companies.length ? [{ value: "EXISTING", label: "Use a saved company" }] : []), { value: "NEW", label: "Create a company here" }],
    },
    initial: {
      campaign: campaign || (campaigns.length === 1 ? campaigns[0].value : ""),
      contact_mode: contacts.length ? "EXISTING" : "NEW",
      contact: contacts.length === 1 ? contacts[0].value : "",
      company_mode: companies.length ? "EXISTING" : "NEW",
      company: companies.length === 1 ? companies[0].value : "",
      channel: "EMAIL",
    },
  };
}

export function outreachCreatePayload(values: Record<string, unknown>) {
  const payload: Record<string, unknown> = { campaign: values.campaign, channel: values.channel, subject: values.subject, body: values.body, notes: values.notes };
  if (values.contact_mode === "NEW") {
    payload.contact_data = { name: values.contact_name, title: values.contact_title, email: values.contact_email, profile_url: values.contact_profile_url, source: values.contact_source };
    if (values.company_mode === "NEW") payload.company_data = { name: values.company_name, website: values.company_website, industry: values.company_industry, location: values.company_location };
    else payload.company = values.company;
  } else payload.contact = values.contact;
  return payload;
}
