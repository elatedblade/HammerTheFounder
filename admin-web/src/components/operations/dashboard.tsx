"use client";

import { useEffect, useState } from "react";
import { ErrorMessage, useRecords } from "./ui";
import { humanize, type RecordData, type WorkspaceContext } from "./types";

type Metrics = Record<string, Record<string, number>>;
const cards = [
  ["campaigns", "active", "Active campaigns"],
  ["campaigns", "ready", "Ready to start"],
  ["applications", "submitted", "Applications submitted"],
  ["applications", "upcoming_interviews", "Upcoming interviews"],
  ["payments", "pending", "Pending payments"],
] as const;

function metricValue(metrics: Metrics, group: string, key: string) {
  const value = metrics[group]?.[key];
  return typeof value === "number" ? value : null;
}

export default function Dashboard({ context }: { context: WorkspaceContext }) {
  const { api, campaign, revision } = context;
  const key = `${campaign}:${revision}`;
  const [result, setResult] = useState<{ key: string; metrics: Metrics | null; error: unknown }>({ key: "", metrics: null, error: null });
  const metrics = result.key === key ? result.metrics : null;
  const error = result.key === key ? result.error : null;
  const loading = result.key !== key;
  const events = useRecords(api, campaign ? `campaigns/${campaign}/events/` : "events/", revision);
  useEffect(() => {
    let active = true;
    api<Metrics>(campaign ? `campaigns/${campaign}/metrics/` : "dashboard/").then((value) => { if (active) setResult({ key, metrics: value, error: null }); }).catch((cause: unknown) => { if (active) setResult({ key, metrics: null, error: cause }); });
    return () => { active = false; };
  }, [api, campaign, key]);
  return <div className="dashboard">
    <section className="panel"><div className="panel-heading"><div><h2>{campaign ? "Campaign overview" : "Operations overview"}</h2><p className="muted">{campaign ? "Selected campaign scope" : "All visible campaign scope"}. Server-derived totals only.</p></div><button className="secondary" onClick={context.refresh} disabled={loading}>Refresh</button></div>
      <ErrorMessage error={error} />{loading && <p role="status">Loading overview…</p>}
      {metrics && <div className="metrics-grid">{cards.map(([group, name, label]) => <div className="metric-group" key={label}><h3>{label}</h3><strong className="metric-value">{metricValue(metrics, group, name) ?? "Unavailable"}</strong><p className="muted">{campaign ? "In this campaign" : "Across visible campaigns"}</p></div>)}</div>}
      {metrics && metricValue(metrics, "campaigns", "active") === 0 && (metricValue(metrics, "campaigns", "ready") ?? 0) > 0 && <p className="guidance"><strong>Ready to start:</strong> payment verification does not start a campaign. Review readiness and use the explicit Start action in Campaigns.</p>}
    </section>
    {campaign && <details className="panel"><summary>Selected campaign activity</summary><ErrorMessage error={events.error} />{events.loading ? <p role="status">Loading activity…</p> : !events.error && (events.data.length ? <ol className="timeline">{events.data.map((event: RecordData) => <li key={String(event.id)}><span className="badge">{humanize(String(event.event_type ?? "Activity"))}</span><p>{String(event.summary ?? "Recorded campaign update")}</p><small><time dateTime={String(event.created_at)}>{new Date(String(event.created_at)).toLocaleString()}</time></small></li>)}</ol> : <p className="empty">No recorded campaign activity yet.</p>)}</details>}
  </div>;
}
