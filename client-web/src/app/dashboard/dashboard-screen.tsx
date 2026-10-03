"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useState } from "react";
import { SERVICE_PLANS } from "../../lib/marketing";
import {
  getCandidateProfile,
  getCampaigns,
  getCurrentUser,
  getInquiries,
  isSafeWhatsAppUrl,
  type Campaign,
  type Inquiry,
  type ServicePlan,
} from "../../lib/api";
import CandidateProgress, { readable } from "../candidate-progress";
import { useRequest } from "../../lib/use-request";
import { AccessDeniedState, AppHeader, LoadingSkeleton, SignedOutState } from "../customer-shell";
import { getLifecyclePresentation } from "./lifecycle-presentation";
import { bumpRefreshRevision } from "./refresh-revision";

const adminUrl = process.env.NEXT_PUBLIC_ADMIN_URL ?? "http://localhost:3001";

function planName(plan: ServicePlan) {
  return SERVICE_PLANS.find((item) => item.id === plan)?.name ?? readable(plan);
}

export default function DashboardScreen() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { user: clerkUser } = useUser();
  const [refreshRevision, setRefreshRevision] = useState(0);
  const identity = useRequest(
    useCallback((signal: AbortSignal) => getCurrentUser(getToken, signal), [getToken]),
    Boolean(isLoaded && isSignedIn && clerkUser?.id),
  );
  const isClient = identity.data?.role === "CLIENT";
  const inquiries = useRequest(
    useCallback((signal: AbortSignal) => getInquiries(getToken, signal), [getToken]),
    isClient,
  );
  const campaigns = useRequest(
    useCallback((signal: AbortSignal) => getCampaigns(getToken, signal), [getToken]),
    isClient,
  );
  const profile = useRequest(
    useCallback((signal: AbortSignal) => getCandidateProfile(getToken, signal), [getToken]),
    isClient,
  );

  if (!isLoaded || identity.loading) return <LoadingSkeleton />;
  if (!isSignedIn) return <SignedOutState redirect="/dashboard" />;
  if (identity.error) {
    return <main className="state-page"><section className="state-card" role="alert"><h1>Workspace identity unavailable</h1><p>We could not verify this account, so no dashboard records are being treated as empty.</p><button className="button button-primary" onClick={identity.retry}>Try again</button></section></main>;
  }
  if (!isClient) return <AccessDeniedState adminUrl={adminUrl} />;

  const refreshDashboard = () => {
    // Each request owns its abort controller. Bumping the generation also
    // reloads CandidateProgress' independent resource hooks, without keeping
    // records from the previous account or campaign selection on screen.
    identity.retry();
    inquiries.retry();
    campaigns.retry();
    profile.retry();
    setRefreshRevision(bumpRefreshRevision);
  };
  const refreshing = identity.loading || inquiries.loading || campaigns.loading || profile.loading;

  const latest = inquiries.data?.[0];
  const lifecycle = getLifecyclePresentation({ campaigns: campaigns.data, campaignsLoading: campaigns.loading, campaignsError: Boolean(campaigns.error), inquiry: latest, profile: profile.data });
  return <main className="app-shell"><AppHeader /><div className="content-wrap">
    <button type="button" className="button button-secondary button-small" disabled={refreshing} onClick={refreshDashboard}>Refresh dashboard status</button>
    <div className="page-intro"><span className="eyebrow">Customer dashboard</span><h1>Your search, in view<span className="accent-dot">.</span></h1><p>See real progress recorded by HTF, your inquiry status and the next useful action. Campaign work is manual and activation is handled by the HTF team.</p></div>
     <section className="panel progress-panel" aria-labelledby="status-heading"><div className="panel-heading"><div><span className="eyebrow">Campaign lifecycle</span><h2 id="status-heading">{lifecycle.headline}</h2><p className="muted">{lifecycle.detail}</p></div>{lifecycle.showProfileAction ? <Link href="/profile" className="button button-secondary button-small">Update profile</Link> : lifecycle.showPlansLink ? <Link href="/plans" className="button button-secondary button-small">View plans</Link> : null}</div>
      {lifecycle.kind === "none" && (inquiries.loading || profile.loading ? <p className="muted" role="status">Loading your workspace status…</p> : inquiries.error ? <div className="notice notice-error" role="alert"><p>{inquiries.error}</p><button type="button" className="button button-secondary button-small" onClick={inquiries.retry}>Try again</button></div> : profile.error ? <div className="notice notice-error" role="alert"><p>{profile.error}</p><button type="button" className="button button-secondary button-small" onClick={profile.retry}>Try again</button></div> : latest ? <><dl className="detail-grid"><div><dt>Plan</dt><dd>{planName(latest.plan)}</dd></div><div><dt>Inquiry status</dt><dd>{readable(latest.status)}</dd></div><div><dt>Last updated</dt><dd>{new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(latest.updated_at))}</dd></div></dl>{(latest.status === "OPEN" || latest.status === "CONTACTED") && isSafeWhatsAppUrl(latest.whatsapp_url) ? <p><a className="button button-primary button-small" href={latest.whatsapp_url}>Resume WhatsApp conversation</a></p> : null}</> : <p className="record-empty">No inquiry saved yet. Choose a plan to start a conversation with HTF.</p>)}
    </section>
     {campaigns.loading ? <p className="muted" role="status">Loading campaign status…</p> : campaigns.error ? <section className="notice notice-error" role="alert"><p>{campaigns.error}</p><button type="button" className="button button-secondary button-small" onClick={campaigns.retry}>Try again</button></section> : campaigns.data?.length ? <section className="panel progress-panel" aria-labelledby="campaign-heading"><span className="eyebrow">Campaign status</span><h2 id="campaign-heading">Your managed search</h2><ul className="campaign-list">{campaigns.data.map((campaign: Campaign) => <li className="campaign-card" key={campaign.id}><strong>{planName(campaign.plan)}</strong><span className="campaign-status is-neutral">{readable(campaign.status)}</span></li>)}</ul></section> : lifecycle.showChoosePlan ? <section className="panel progress-panel"><span className="eyebrow">Next step</span><h2>Ready to discuss your search?</h2><p className="muted">Choose a plan to start an inquiry. Your selection will not activate or modify a campaign.</p><Link className="button button-primary" href="/plans">Choose a plan</Link></section> : null}
    {isClient ? <CandidateProgress key={refreshRevision} getToken={getToken} reloadKey={refreshRevision} /> : null}
  </div></main>;
}
