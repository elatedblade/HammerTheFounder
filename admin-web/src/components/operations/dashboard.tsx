"use client";

import { useEffect, useState } from "react";
import { ErrorMessage, useRecords } from "./ui";
import { humanize, type RecordData, type WorkspaceContext } from "./types";
import { dashboardMetrics, metricValue, type Metrics } from "./dashboard-metrics";

export default function Dashboard({ context }: { context: WorkspaceContext }) {
  const { api, campaign, revision } = context;
  const key = `${campaign}:${revision}`;
  const [result, setResult] = useState<{ key: string; metrics: Metrics | null; error: unknown }>({ key: "", metrics: null, error: null });
  const metrics = result.key === key ? result.metrics : null;
  const error = result.key === key ? result.error : null;
  const loading = result.key !== key;
  const presentation = metrics ? dashboardMetrics(metrics) : null;
  const events = useRecords(api, campaign ? `campaigns/${campaign}/events/` : "events/", revision);
  useEffect(() => {
    let active = true;
    api<Metrics>(campaign ? `campaigns/${campaign}/metrics/` : "dashboard/").then((value) => { if (active) setResult({ key, metrics: value, error: null }); }).catch((cause: unknown) => { if (active) setResult({ key, metrics: null, error: cause }); });
    return () => { active = false; };
  }, [api, campaign, key]);
  return <div className="dashboard">
    <section className="panel"><div className="panel-heading"><div><h2>{campaign ? "Campaign overview" : "Operations overview"}</h2><p className="muted">{campaign ? "Selected campaign scope" : "All visible campaign scope"}. Server-derived totals only.</p></div><button className="secondary" onClick={context.refresh} disabled={loading}>Refresh</button></div>
      <ErrorMessage error={error} />{loading && <p role="status">Loading overview…</p>}
      <p className="muted">Outreach counts show mutually exclusive current stages: Sent includes delivered messages awaiting a response; Responded includes all reply outcomes.</p>
      {presentation && <><div className="metrics-grid">{presentation.primary.map(({label, value}) => <div className="metric-group" key={label}><h3>{label}</h3><strong className="metric-value">{value ?? "Unavailable"}</strong></div>)}</div><details><summary>Additional metrics</summary><dl className="details">{presentation.additional.map(({label, value}) => <div key={label}><dt>{humanize(label)}</dt><dd>{value}</dd></div>)}</dl></details></>}
      {metrics && metricValue(metrics, "campaigns", "active") === 0 && (metricValue(metrics, "campaigns", "ready") ?? 0) > 0 && <p className="guidance"><strong>Ready to start:</strong> payment verification does not start a campaign. Review readiness and use the explicit Start action in Campaigns.</p>}
    </section>
    {campaign && <details className="panel"><summary>Selected campaign activity</summary><ErrorMessage error={events.error} />{events.loading ? <p role="status">Loading activity…</p> : !events.error && (events.data.length ? <ol className="timeline">{events.data.map((event: RecordData) => <li key={String(event.id)}><span className="badge">{humanize(String(event.event_type ?? "Activity"))}</span><p>{String(event.summary ?? "Recorded campaign update")}</p><small><time dateTime={String(event.created_at)}>{new Date(String(event.created_at)).toLocaleString()}</time></small></li>)}</ol> : <p className="empty">No recorded campaign activity yet.</p>)}</details>}
  </div>;
}
