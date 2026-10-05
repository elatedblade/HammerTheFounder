"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  getApplications, getCampaigns, getDashboard, getEvents, getNotifications,
  getOutreach, getPaymentInstructions, getPayments,
  type Application, type Outreach,
} from "../lib/api";
import { selectOverviewMetrics } from "./overview-metrics";
import { OUTREACH_STATUS_OPTIONS, outreachQuery, presentOutreachRow, presentOutreachStatus } from "./outreach-presentation";
import { applicationStageOptions, applicationStageLabel, applicationQuery } from "./application-stages";

type Token = () => Promise<string | null>;
type View = "overview" | "applications" | "outreach" | "interviews" | "activity" | "notifications" | "payments";
const views: View[] = ["overview", "applications", "outreach", "interviews", "activity", "notifications", "payments"];
const interviewStatuses = ["RECRUITER_CONTACTED", "INTERVIEW", "INTERVIEW_SCHEDULED"];
export function readable(value: string) { return value.toLowerCase().replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase()); }
export function dateTime(value?: string | null) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not recorded" : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function useResource<T>(loader: (signal: AbortSignal) => Promise<T>, reloadKey = 0) {
  const [state, setState] = useState<{data: T | null; loading: boolean; error: string | null}>({ data: null, loading: true, error: null });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    // Reset stale scoped records before loading the newly selected campaign.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({data: null, loading: true, error: null});
    loader(controller.signal).then(data => {
      if (!controller.signal.aborted) setState({ data, loading: false, error: null });
    }).catch(error => {
      if (!controller.signal.aborted) setState({data: null, loading: false, error: error instanceof Error ? error.message : "This information is unavailable."});
    });
    return () => controller.abort();
  }, [loader, revision, reloadKey]);
  return {...state, retry: () => setRevision(current => current + 1)};
}
function ResourceState({loading, error, retry}: {loading: boolean; error: string|null; retry: () => void}) {
  if (loading) return <p className="muted" role="status">Loading your records…</p>;
  if (error) return <div className="notice notice-error" role="alert"><p>{error}</p><button type="button" className="button button-secondary" onClick={retry}>Try again</button></div>;
  return null;
}
function Badge({value}: {value: string}) { return <span className="record-badge">{readable(value)}</span>; }
function Empty({children}: {children: React.ReactNode}) { return <p className="record-empty">{children}</p>; }
function Paging({offset, count, disabled, setOffset, hasMore = count >= 50}: {offset: number; count: number; disabled: boolean; setOffset: (value: number) => void; hasMore?: boolean}) {
  return <div className="record-paging"><button type="button" className="button button-secondary button-small" disabled={disabled || offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous page</button><span>Page {offset / 50 + 1} · {count} records loaded</span><button type="button" className="button button-secondary button-small" disabled={disabled || !hasMore} onClick={() => setOffset(offset + 50)}>Next page</button></div>;
}

function Overview({getToken, reloadKey}: {getToken: Token; reloadKey?: number}) {
  const loader = useCallback((signal: AbortSignal) => getDashboard(getToken, signal), [getToken]);
  const resource = useResource(loader, reloadKey);
  const metrics = resource.data ? selectOverviewMetrics(resource.data) : null;
  return <>
    <ResourceState {...resource}/>
    <p className="muted">Outreach counts show mutually exclusive current stages: Sent includes delivered messages awaiting a response; Responded includes all reply outcomes.</p>
    {metrics ? <><dl className="metric-grid">{metrics.primary.map(({label, value}) => <div key={label}><dt>{label}</dt><dd>{value === null ? "Unavailable" : value}</dd></div>)}</dl><details className="record-details"><summary>Additional metrics</summary><dl>{metrics.additional.map(({label, value}) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></details></> : null}
    <button className="button button-secondary button-small" type="button" disabled={resource.loading} onClick={resource.retry}>Refresh overview</button>
  </>;
}

function ApplicationDetails({row}: {row: Application}) {
  return <details className="record-details"><summary>View details</summary><dl>
    <div><dt>Campaign</dt><dd>{row.campaign}</dd></div><div><dt>Created</dt><dd>{dateTime(row.created_at)}</dd></div>
     <div><dt>Last update</dt><dd>{dateTime(row.updated_at)}</dd></div>
    <div><dt>Recorded outcome</dt><dd>{readable(row.status)}</dd></div>
    <div><dt>Interview scheduled</dt><dd>{row.interview_scheduled_at ? <time dateTime={row.interview_scheduled_at}>{dateTime(row.interview_scheduled_at)} ({Intl.DateTimeFormat().resolvedOptions().timeZone})</time> : "Not scheduled"}</dd></div>
  </dl></details>;
}
type CustomerOutreach = ReturnType<typeof presentOutreachRow>;
function Applications({getToken, campaign, interviews = false, reloadKey}: {getToken: Token; campaign: string; interviews?: boolean; reloadKey?: number}) {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const loader = useCallback((signal: AbortSignal) => {
    const query = new URLSearchParams(applicationQuery(campaign, interviews ? "" : status, offset));
    if (interviews && status) query.set("status", status);
    if (interviews && !status) {
      return Promise.all(interviewStatuses.map(stage => {
        const scopedQuery = new URLSearchParams(query); scopedQuery.set("status", stage);
        return getApplications(getToken, scopedQuery.toString(), signal);
      })).then(pages => pages.flat().sort((a, b) => b.created_at.localeCompare(a.created_at)));
    }
    return getApplications(getToken, query.toString(), signal);
  }, [getToken, campaign, status, interviews, offset]);
  const resource = useResource(loader, reloadKey);
  const rows = (resource.data ?? []).filter(row => `${row.company_name} ${row.job_title}`.toLowerCase().includes(search.toLowerCase()));
  return <>
    {interviews ? <p className="muted">Recruiter contact and interview-stage applications. Recorded interview times are shown in your local timezone ({Intl.DateTimeFormat().resolvedOptions().timeZone}); missing dates are not assumed.</p> : null}
    <div className="record-filters">
      <div className="field"><label htmlFor="application-search">Search company or role on this page</label><input id="application-search" value={search} onChange={event => setSearch(event.target.value)}/></div>
      <div className="field"><label htmlFor="application-status">{interviews ? "Interview pipeline status" : "Application status"}</label><select id="application-status" value={status} onChange={event => {setStatus(event.target.value); setOffset(0);}}><option value="">{interviews ? "All interview pipeline stages" : "All applications and history"}</option>{(interviews ? interviewStatuses.map(value => ({ value, label: readable(value) })) : applicationStageOptions).map(({ value, label }) => <option key={value} value={value}>{label}</option>)}</select></div>
    </div>
    <ResourceState {...resource}/>
    {resource.data && !rows.length ? <Empty>{interviews ? "No interviews recorded for this selection." : "No applications match this selection."}</Empty> : null}
    {rows.length ? <div className="table-scroll" tabIndex={0} aria-label="Application records"><table className="records-table"><caption className="sr-only">{interviews ? "Interview-stage applications" : "Your applications"}</caption><thead><tr><th scope="col">Company / role</th><th scope="col">{interviews ? "Interview scheduled" : "Submitted"}</th><th scope="col">Status</th><th scope="col">Details</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td><strong>{row.company_name}</strong><span>{row.job_title}</span></td><td>{interviews ? row.interview_scheduled_at ? <time dateTime={row.interview_scheduled_at}>{dateTime(row.interview_scheduled_at)}</time> : "Not scheduled" : dateTime(row.submitted_at)}</td><td><Badge value={applicationStageLabel(row)}/></td><td><ApplicationDetails row={row}/></td></tr>)}</tbody></table></div> : null}
    <button type="button" disabled={resource.loading} className="button button-secondary button-small" onClick={resource.retry}>Refresh records</button>
    <Paging offset={offset} count={resource.data?.length ?? 0} disabled={resource.loading || Boolean(resource.error)} setOffset={setOffset} hasMore={interviews && !status ? interviewStatuses.some(stage => (resource.data ?? []).filter(row => row.status === stage).length === 50) : (resource.data?.length ?? 0) >= 50}/>
  </>;
}

function OutreachDetails({row}: {row: CustomerOutreach}) {
  return <details className="record-details"><summary>View details</summary><dl><div><dt>Channel</dt><dd>{readable(row.channel)}</dd></div>
    <div><dt>Reply recorded</dt><dd>{dateTime(row.reply_at)}</dd></div><div><dt>Follow-up due</dt><dd>{dateTime(row.follow_up_due_at)}</dd></div>
    <div><dt>Delivered</dt><dd>{dateTime(row.delivered_at)}</dd></div><div><dt>Bounced</dt><dd>{dateTime(row.bounced_at)}</dd></div>
    <div><dt>Campaign</dt><dd>{row.campaign}</dd></div></dl></details>;
}
function OutreachRecords({getToken, campaign, reloadKey}: {getToken: Token; campaign: string; reloadKey?: number}) {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const loader = useCallback((signal: AbortSignal) => {
    return getOutreach(getToken, outreachQuery(campaign, status, offset), signal);
  }, [getToken, campaign, status, offset]);
  const resource = useResource(loader, reloadKey);
  const rows = (resource.data ?? []).map(presentOutreachRow).filter(row => `${row.company_name} ${row.contact_name}`.toLowerCase().includes(search.toLowerCase()));
  return <><p className="muted">Outreach is handled manually by HTF. This view shows recorded progress; it does not send messages.</p>
    <div className="record-filters"><div className="field"><label htmlFor="outreach-search">Search company or contact on this page</label><input id="outreach-search" value={search} onChange={event => setSearch(event.target.value)}/></div><div className="field"><label htmlFor="outreach-status">Outreach status</label><select id="outreach-status" value={status} onChange={event => {setStatus(event.target.value); setOffset(0);}}><option value="">All statuses</option>{OUTREACH_STATUS_OPTIONS.map(({value, label}) => <option key={value} value={value}>{label}</option>)}</select></div></div>
    <ResourceState {...resource}/>
    {resource.data && !rows.length ? <Empty>No outreach matches this selection.</Empty> : null}
    {rows.length ? <div className="table-scroll" tabIndex={0} aria-label="Outreach records"><table className="records-table"><caption className="sr-only">Your outreach</caption><thead><tr><th scope="col">Company / contact</th><th scope="col">Sent</th><th scope="col">Status</th><th scope="col">Details</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td><strong>{row.company_name}</strong><span>{row.contact_name}</span></td><td>{dateTime(row.sent_at)}</td><td><Badge value={presentOutreachStatus(row.status)}/></td><td><OutreachDetails row={row}/></td></tr>)}</tbody></table></div> : null}
    <button type="button" disabled={resource.loading} className="button button-secondary button-small" onClick={resource.retry}>Refresh records</button>
    <Paging offset={offset} count={resource.data?.length ?? 0} disabled={resource.loading || Boolean(resource.error)} setOffset={setOffset}/>
  </>;
}
function Activity({getToken, campaign, reloadKey}: {getToken: Token; campaign: string; reloadKey?: number}) {
  const [offset, setOffset] = useState(0);
  const loader = useCallback((signal: AbortSignal) => {
    const query = new URLSearchParams({limit: "50", offset: String(offset)});
    if (campaign) query.set("campaign", campaign);
    return getEvents(getToken, query.toString(), signal);
  }, [getToken, campaign, offset]);
  const resource = useResource(loader, reloadKey);
  const rows = [...(resource.data ?? [])].sort((a, b) => b.created_at.localeCompare(a.created_at));
  return <><ResourceState {...resource}/>{resource.data && !rows.length ? <Empty>No campaign activity recorded yet.</Empty> : null}
    <ol className="activity-timeline">{rows.map(row => <li key={row.id}><time dateTime={row.created_at}>{dateTime(row.created_at)}</time><strong>{row.summary}</strong><span>{readable(row.event_type)}</span></li>)}</ol>
    <button type="button" disabled={resource.loading} className="button button-secondary button-small" onClick={resource.retry}>Refresh activity</button><Paging offset={offset} count={resource.data?.length ?? 0} disabled={resource.loading || Boolean(resource.error)} setOffset={setOffset}/></>;
}
function Notifications({getToken, campaign, reloadKey}: {getToken: Token; campaign: string; reloadKey?: number}) {
  const [offset, setOffset] = useState(0);
  const loader = useCallback((signal: AbortSignal) => getNotifications(getToken, signal, campaign, 50, offset), [getToken, campaign, offset]);
  const resource = useResource(loader, reloadKey);
  const rows = (resource.data ?? []).filter(row => !campaign || row.campaign === campaign);
  return <><ResourceState {...resource}/>{resource.data && !rows.length ? <Empty>No notifications for this selection.</Empty> : null}
    <ul className="message-list">{rows.map(row => <li key={row.id}><div className="message-heading"><h3>{row.subject || readable(row.channel)}</h3><Badge value={row.status}/></div><p className="message-body">{row.body}</p><p className="muted">{readable(row.channel)} · Created {dateTime(row.created_at)}{row.sent_at ? ` · Sent ${dateTime(row.sent_at)}` : ""}</p></li>)}</ul>
    <button type="button" disabled={resource.loading} className="button button-secondary button-small" onClick={resource.retry}>Refresh notifications</button><Paging offset={offset} count={resource.data?.length ?? 0} disabled={resource.loading || Boolean(resource.error)} setOffset={setOffset}/></>;
}
function Payments({getToken, campaign, reloadKey}: {getToken: Token; campaign: string; reloadKey?: number}) {
  const [offset, setOffset] = useState(0);
  const loader = useCallback((signal: AbortSignal) => getPayments(getToken, signal, campaign, 50, offset), [getToken, campaign, offset]);
  const instructionLoader = useCallback((signal: AbortSignal) => getPaymentInstructions(getToken, signal), [getToken]);
  const resource = useResource(loader, reloadKey);
  const instructions = useResource(instructionLoader, reloadKey);
  const rows = (resource.data ?? []).filter(row => !campaign || row.campaign === campaign);
  return <><p className="muted">Payments are collected manually and verified by HTF. This page does not initiate a payment. A pending record is not proof of payment.</p>
    <section className="payment-instructions" aria-labelledby="upi-heading"><h3 id="upi-heading">UPI payment instructions</h3><ResourceState {...instructions}/>
      {instructions.data?.configured ? <><dl className="detail-grid"><div><dt>UPI ID</dt><dd>{instructions.data.upi_id || "Not provided"}</dd></div><div><dt>Payee</dt><dd>{instructions.data.payee_name || "Not provided"}</dd></div></dl><p className="message-body">{instructions.data.instructions}</p><p className="muted">Check the payee and agreed amount before paying in your UPI app. Share your reference with HTF for manual verification.</p></> : instructions.data ? <p className="muted">Payment instructions are not configured. Contact HTF before making a payment.</p> : null}
    </section><ResourceState {...resource}/>{resource.data && !rows.length ? <Empty>No payment records for this selection.</Empty> : null}
    {rows.length ? <div className="table-scroll" tabIndex={0} aria-label="Payment records"><table className="records-table"><caption className="sr-only">Manual payment records</caption><thead><tr><th scope="col">Amount</th><th scope="col">Status</th><th scope="col">Verified</th><th scope="col">Created</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td>{row.currency} {row.amount}</td><td><Badge value={row.status}/></td><td>{dateTime(row.verified_at)}</td><td>{dateTime(row.created_at)}</td></tr>)}</tbody></table></div> : null}
     <button type="button" disabled={resource.loading} className="button button-secondary button-small" onClick={() => {resource.retry(); instructions.retry();}}>Refresh billing</button><Paging offset={offset} count={resource.data?.length ?? 0} disabled={resource.loading || Boolean(resource.error)} setOffset={setOffset}/></>;
}

export default function CandidateProgress({getToken, reloadKey = 0}: {getToken: Token; reloadKey?: number}) {
  const [view, setView] = useState<View>("overview");
  const [campaign, setCampaign] = useState("");
  const loader = useCallback((signal: AbortSignal) => getCampaigns(getToken, signal), [getToken]);
  const campaigns = useResource(loader, reloadKey);
  return <section id="progress" className="panel progress-panel" aria-labelledby="progress-heading">
    <div className="panel-heading"><div><span className="eyebrow">Your search</span><h2 id="progress-heading">Campaign progress</h2></div><Link className="button button-secondary button-small" href="/profile">Edit profile</Link></div>
    <nav className="workspace-tabs" aria-label="Campaign progress views">{views.map(tab => <button type="button" key={tab} className={view === tab ? "is-selected" : ""} aria-pressed={view === tab} onClick={() => setView(tab)}>{readable(tab)}</button>)}</nav>
     {view !== "overview" ? <><ResourceState loading={campaigns.loading} error={campaigns.error} retry={campaigns.retry}/><div className="field campaign-scope"><label htmlFor="campaign-scope">Campaign</label><select id="campaign-scope" value={campaign} disabled={campaigns.loading || Boolean(campaigns.error)} onChange={event => setCampaign(event.target.value)}><option value="">All my campaigns</option>{campaigns.data?.map(row => <option key={row.id} value={row.id}>{readable(row.plan)} · {readable(row.status)}</option>)}</select></div></> : null}
    <div className="progress-view" key={`${view}-${campaign}`} aria-labelledby="view-heading"><h3 id="view-heading" className="view-heading">{readable(view)}</h3>
      {view === "overview" ? <Overview getToken={getToken} reloadKey={reloadKey}/> : null}
      {view === "applications" || view === "interviews" ? <Applications getToken={getToken} campaign={campaign} interviews={view === "interviews"} reloadKey={reloadKey}/> : null}
      {view === "outreach" ? <OutreachRecords getToken={getToken} campaign={campaign} reloadKey={reloadKey}/> : null}
      {view === "activity" ? <Activity getToken={getToken} campaign={campaign} reloadKey={reloadKey}/> : null}
      {view === "notifications" ? <Notifications getToken={getToken} campaign={campaign} reloadKey={reloadKey}/> : null}
      {view === "payments" ? <Payments getToken={getToken} campaign={campaign} reloadKey={reloadKey}/> : null}
    </div>
  </section>;
}
