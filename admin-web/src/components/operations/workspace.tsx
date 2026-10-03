"use client";

import { UserButton } from "@clerk/nextjs";
import { useEffect, useMemo, useState } from "react";
import type { ApiClient, CurrentUser } from "../../lib/api";
import CandidatesPanel from "./candidates-panel";
import CampaignsPanel from "./campaigns-panel";
import Dashboard from "./dashboard";
import ResourcePanel from "./resource-panel";
import { applications, companies, contacts, inquiries, jobs, notificationTemplates, notifications, outreach, outreachTemplates, payments, suppression } from "./resources";
import ApplicationCreate from "./application-create";
import { ErrorMessage } from "./ui";
import { display, isAdmin, type Option, type RecordData, type Resource, type WorkspaceContext } from "./types";
import { campaignScopeForTab, workspaceTabs, type WorkspaceTab } from "./workspace-tabs";

// Navigation is a presentation concern, not an authorization boundary. The hidden
// modules remain available through their APIs and the campaign request workflow.
function ResourceGroup({ resources, context }: { resources: Resource[]; context: WorkspaceContext }) {
  const [active, setActive] = useState(0);
  const [creatingApplication, setCreatingApplication] = useState(false);
  return <><nav className="subnav" aria-label="Workflow sections">{resources.map((resource, index) => <button key={resource.path} className={active === index ? "active" : "secondary"} aria-pressed={active === index} onClick={() => { setActive(index); setCreatingApplication(false); }}>{resource.title}</button>)}</nav>{resources[active].path === "applications/" && <div className="panel-heading"><p className="muted">Create through searchable company and job dependencies; review and transitions remain below.</p><button onClick={() => setCreatingApplication(true)} disabled={creatingApplication}>Record application</button></div>}{creatingApplication && resources[active].path === "applications/" && <ApplicationCreate context={context} onDone={() => setCreatingApplication(false)} />}<ResourcePanel key={`${resources[active].path}-${context.campaign}`} resource={resources[active]} context={context} /></>;
}

export default function OperationsWorkspace({ user, api }: { user: CurrentUser; api: ApiClient }) {
  const [tab, setTab] = useState<WorkspaceTab>("Overview");
  const [campaign, setCampaign] = useState("");
  const [revision, setRevision] = useState(0);
  const [lookups, setLookups] = useState<Record<string, Option[]>>({});
  const [errors, setLookupErrors] = useState<Record<string, unknown>>({});
  const lookupKey = `${tab}:${revision}`;
  const [loadedKey, setLoadedKey] = useState("");
  const lookupLoading = loadedKey !== lookupKey;
  const lookupErrors = lookupLoading ? {} : errors;
  useEffect(() => {
    let active = true;
    const requestErrors: Record<string, unknown> = {};
    const paths: Record<string, string> = { campaigns: "campaigns/" };
    if (tab === "Campaigns") paths.candidates = "admin/candidates/";
    if (tab === "Applications") paths.companies = "companies/";
    if (tab === "Applications") paths.jobs = "jobs/";
    if (isAdmin(user) && tab === "Campaigns") paths.operators = "admin/operators/";
    Promise.all(Object.entries(paths).map(async ([key, path]) => {
      try {
        const rows = await api<RecordData[]>(`${path}?limit=500`);
        if (!active) return;
        setLookups((current) => ({ ...current, [key]: rows.map((row) => ({ value: String(row.id), label: [row.full_name ?? row.candidate_name ?? row.name ?? row.title ?? row.email ?? row.id, row.company_name ?? row.candidate_email, row.plan, row.status].filter(Boolean).map(display).join(" · ") })) }));
      } catch (error) {
        if (active) { setLookups((current) => ({ ...current, [key]: [] })); requestErrors[key] = error; }
      }
    })).finally(() => { if (active) { setLookupErrors(requestErrors); setLoadedKey(lookupKey); } });
    return () => { active = false; };
  }, [api, user, tab, lookupKey]);
  const scopedCampaign = campaignScopeForTab(tab, campaign);
  const context = useMemo<WorkspaceContext>(() => ({ api, user, campaign: scopedCampaign, revision, lookups, refresh: () => setRevision((value) => value + 1) }), [api, user, scopedCampaign, revision, lookups]);
  return <main className="ops-workspace"><header className="workspace-header"><div><p className="eyebrow">Hammer The Founder</p><h1>Operations workspace</h1><p className="muted">{user.email} <span className="badge">{user.role}</span></p></div><UserButton /></header>{tab === "Overview" && <div className="workspace-toolbar"><label htmlFor="campaign-scope">Campaign scope<select id="campaign-scope" value={campaign} onChange={(event) => setCampaign(event.target.value)} disabled={lookupLoading}><option value="">All visible campaigns</option>{lookups.campaigns?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label><p className="muted">Manual-first operations. No applications, cold outreach, payments or AI runs execute automatically.</p></div>}{Object.keys(lookupErrors).length > 0 && <details className="lookup-errors"><summary>Some form options could not load ({Object.keys(lookupErrors).join(", ")})</summary>{Object.entries(lookupErrors).map(([key, error]) => <div key={key}><strong>{key}</strong><ErrorMessage error={error} /></div>)}<button className="secondary" onClick={context.refresh}>Retry loading options</button></details>}<nav className="workspace-tabs" aria-label="Operations workspace">{workspaceTabs.map((name) => <button key={name} className={tab === name ? "active" : ""} aria-current={tab === name ? "page" : undefined} onClick={() => setTab(name)}>{name}</button>)}</nav><div className="workspace-content" key={tab}>
       {tab === "Overview" && <Dashboard context={context} />}
       {tab === "Candidates" && <CandidatesPanel context={context} />}
       {tab === "Campaigns" && <CampaignsPanel context={context} />}
        {tab === "Applications" && <ResourceGroup resources={[applications, companies, jobs]} context={context} />}
        {tab === "Payments" && <ResourcePanel key={campaign} resource={payments} context={context} />}
        {tab === "Inquiries" && <ResourcePanel resource={inquiries} context={context} />}
         {tab === "Notifications" && <ResourceGroup resources={[notifications, notificationTemplates]} context={context} />}
         {tab === "Outreach" && <ResourceGroup resources={[outreach, contacts, suppression, outreachTemplates]} context={context} />}
     </div><footer className="workspace-footer">The API remains the authority for permissions, transitions and delivery status. Saved records do not imply external work is complete.</footer></main>;
}
