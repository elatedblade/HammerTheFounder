"use client";

import { useEffect, useState } from "react";
import { ErrorMessage, useRecords } from "./ui";
import { display, humanize, type WorkspaceContext } from "./types";

type Metrics = Record<string, Record<string, number>>;

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
    api<Metrics>(campaign ? `campaigns/${campaign}/metrics/` : "dashboard/").then((metrics) => { if (active) setResult({ key, metrics, error: null }); }).catch((error: unknown) => { if (active) setResult({ key, metrics: null, error }); });
    return () => { active = false; };
  }, [api, campaign, key]);
  return <div className="dashboard"><section className="panel"><div className="panel-heading"><div><h2>{campaign ? "Campaign overview" : "Operations overview"}</h2><p className="muted">Live server totals within your account&apos;s scope.</p></div><button className="secondary" onClick={context.refresh} disabled={loading}>Refresh</button></div><ErrorMessage error={error} />{loading && <p role="status">Loading metrics…</p>}{metrics && <div className="metrics-grid">{Object.entries(metrics).map(([group, values]) => <div className="metric-group" key={group}><h3>{humanize(group)}</h3>{typeof values === "object" && values !== null ? Object.entries(values).map(([label, value]) => <div className="metric" key={label}><span>{humanize(label)}</span><strong>{display(value)}</strong></div>) : <strong>{display(values)}</strong>}</div>)}</div>}</section><section className="panel"><h2>Campaign event timeline</h2><p className="muted">Recorded activity, not automated promises. Select a campaign to focus its timeline.</p><ErrorMessage error={events.error} />{events.loading ? <p role="status">Loading events…</p> : !events.error && (events.data.length ? <ol className="timeline">{events.data.map((event) => <li key={String(event.id)}><span className="badge">{humanize(display(event.event_type))}</span><p>{display(event.summary)}</p><small><time dateTime={String(event.created_at)}>{new Date(String(event.created_at)).toLocaleString()}</time>{!campaign ? ` · Campaign ${display(event.campaign)}` : ""}</small></li>)}</ol> : <p className="empty">No recorded campaign events yet.</p>)}</section></div>;
}
