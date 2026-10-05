"use client";
import { useAuth, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SERVICE_PLANS } from "../../lib/marketing";
import { createInquiry, getCampaigns, getCurrentUser, getInquiries, getPublicContact, isSafeWhatsAppUrl, type Campaign, type Inquiry, type PublicContact, type ServicePlan } from "../../lib/api";
import { activeCampaigns, selectedPlan, supportMailto } from "./plan-helpers";
import { useRequest } from "../../lib/use-request";
import { AccessDeniedState, AppHeader, LoadingSkeleton, SignedOutState } from "../customer-shell";
import { readable } from "../candidate-progress";
import styles from "./plans-cards.module.css";

export function AvailablePlanCards({ selected, onSelect }: { selected: ServicePlan | null; onSelect: (plan: ServicePlan) => void }) {
  return <div className={styles.planGrid}>{SERVICE_PLANS.map((plan, index) => {
    const isSelected = selected === plan.id;
    return <article className={`${styles.planCard} ${index === 1 ? styles.planFeatured : ""} ${isSelected ? styles.planSelected : ""}`} key={plan.id}>
      <span className={styles.planNumber}>0{index + 1}</span>
      <h3>{plan.name}</h3>
      <p className={styles.planSummary}>{plan.summary}</p>
      <ul className={styles.planDailyCounts}>
        <li><strong>{plan.applicationsPerDay}</strong> applications per day</li>
        <li><strong>{plan.coldMailsPerDay}</strong> cold mails per day</li>
      </ul>
      <p className={styles.planPrice}><strong>₹{plan.pricePerWeek}</strong> / week</p>
      <p className={styles.planFreeWeek}>1 week free</p>
      <button type="button" className={styles.selectButton} onClick={() => onSelect(plan.id)} aria-label={`Select ${plan.name}`} aria-pressed={isSelected}>{isSelected ? <><span aria-hidden="true">✓ </span>Selected</> : "Select plan"}</button>
    </article>;
  })}</div>;
}

export default function PlansScreen() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();
  const params = useSearchParams();
  const [selected, setSelected] = useState<ServicePlan | null>(() => selectedPlan(params.get("plan")));
  const [inquiryError, setInquiryError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);
  const mutation = useRef<AbortController | null>(null);
  const userRequest = useRequest(useCallback((signal: AbortSignal) => getCurrentUser(getToken, signal), [getToken]), Boolean(isLoaded && isSignedIn && user?.id));
  const role = userRequest.data?.role ?? "CLIENT";
  const accountReady = userRequest.data?.role === "CLIENT";
  const inquiries = useRequest(useCallback((signal: AbortSignal) => getInquiries(getToken, signal), [getToken]), accountReady);
  const campaigns = useRequest(useCallback((signal: AbortSignal) => getCampaigns(getToken, signal), [getToken]), accountReady);
  const contact = useRequest<PublicContact>(useCallback((signal: AbortSignal) => getPublicContact(signal), []), true);
  useEffect(() => () => mutation.current?.abort(), []);

  const submit = async () => {
    if (!selected || submittingRef.current || !accountReady || contact.data?.whatsapp_configured !== true) return;
    if (!window.confirm("Save this plan as an inquiry and open HTF's configured WhatsApp conversation? This does not activate a campaign.")) return;
    submittingRef.current = true; setSubmitting(true); setInquiryError(null);
    const controller = new AbortController(); mutation.current = controller;
    try {
      const inquiry = await createInquiry(getToken, selected, controller.signal);
      if (controller.signal.aborted) return;
      if (!isSafeWhatsAppUrl(inquiry.whatsapp_url)) throw new Error("WhatsApp is not configured for this workspace yet.");
      if (!controller.signal.aborted) window.location.assign(inquiry.whatsapp_url);
    }
    catch (error) { if (!controller.signal.aborted) { setInquiryError(error instanceof Error ? error.message : "We could not save your inquiry."); setSubmitting(false); submittingRef.current = false; } }
  };

  if (!isLoaded || userRequest.loading) return <LoadingSkeleton />;
  if (!isSignedIn) return <SignedOutState redirect={selected ? `/plans?plan=${selected}` : "/plans"} />;
  if (userRequest.error) return <main className="state-page"><section className="state-card" role="alert"><h1>Workspace identity unavailable</h1><p>We could not verify this account. Plans are visible, but no inquiry can be submitted until identity is confirmed.</p><button className="button button-primary" onClick={userRequest.retry}>Try again</button></section></main>;
  if (role !== "CLIENT") return <AccessDeniedState adminUrl={process.env.NEXT_PUBLIC_ADMIN_URL ?? "http://localhost:3001"} />;
  const active = activeCampaigns(campaigns.data ?? []);
  const mailto = supportMailto(contact.data?.support_email);
  return <main className="app-shell"><AppHeader /><div className="content-wrap"><div className="page-intro"><span className="eyebrow">Plans</span><h1>Choose the support that fits your search<span className="accent-dot">.</span></h1><p>Selecting a plan starts an inquiry only. HTF reviews fit with you; no choice on this page activates or changes a campaign.</p></div>
    <section className="panel progress-panel" aria-labelledby="plans-heading"><div className={styles.plansHeading}><h2 id="plans-heading">Available plans</h2><Link className="button button-secondary button-small" href="/dashboard">View dashboard</Link></div><AvailablePlanCards selected={selected} onSelect={setSelected} /></section>
    <section className="panel progress-panel" aria-labelledby="status-heading"><span className="eyebrow">Current status</span><h2 id="status-heading">{campaigns.loading ? "Loading active campaigns…" : "Your active campaigns"}</h2>{campaigns.error ? <div className="notice notice-error" role="alert"><p>{campaigns.error}</p><button className="button button-secondary button-small" onClick={campaigns.retry}>Try again</button></div> : active.length ? <ul className="campaign-list">{active.map(campaign => <li className="campaign-card" key={campaign.id}><strong>{SERVICE_PLANS.find(plan => plan.id === campaign.plan)?.name ?? campaign.plan}</strong><span className="campaign-status is-neutral">{readable(campaign.status)}</span></li>)}</ul> : !campaigns.loading ? <p className="record-empty">No active campaign is recorded. Draft, onboarding, ready, paused and completed records are not shown as active.</p> : null}</section>
    <section className="panel progress-panel" aria-labelledby="inquiry-heading"><span className="eyebrow">Inquiry handoff</span><h2 id="inquiry-heading">Discuss a plan with HTF</h2><p className="muted">{selected ? `You selected ${SERVICE_PLANS.find(plan => plan.id === selected)?.name}.` : "Select a plan above to continue."} Requesting another plan is an inquiry only and never modifies an active campaign.</p>{inquiries.loading ? <p role="status" className="muted">Loading your inquiry history…</p> : inquiries.error ? <div className="notice notice-error" role="alert"><p>{inquiries.error}</p><button className="button button-secondary button-small" onClick={inquiries.retry}>Try again</button></div> : inquiries.data?.length ? <p className="muted">You have {inquiries.data.length} saved {inquiries.data.length === 1 ? "inquiry" : "inquiries"}; choose another plan to start a new discussion.</p> : null}{contact.error ? <div className="notice notice-warning" role="status"><p>Contact options are temporarily unavailable. Your plan choices remain available.</p><button className="button button-secondary button-small" onClick={contact.retry}>Retry contact options</button></div> : null}{contact.data?.whatsapp_configured === false ? <p className="muted">WhatsApp is not configured yet. {mailto ? <a href={mailto}>Email HTF support</a> : "Please try again later."}</p> : null}{inquiryError ? <div className="notice notice-error" role="alert"><p>{inquiryError}</p></div> : null}<button type="button" className="button button-primary" disabled={!selected || submitting || contact.data?.whatsapp_configured !== true || Boolean(inquiries.error)} onClick={() => void submit()}>{submitting ? "Saving inquiry…" : "Confirm inquiry and continue to WhatsApp"}</button></section>
    <section className="panel progress-panel" aria-labelledby="help-heading"><span className="eyebrow">Help</span><h2 id="help-heading">Need help choosing?</h2>{contact.error ? <p className="muted">Support contact details are unavailable right now. Retry contact options above.</p> : mailto ? <p className="muted">Questions about fit or next steps? <a href={mailto}>Email HTF support</a>.</p> : <p className="muted">Support email is not configured yet. Please retry contact options later.</p>}</section>
  </div></main>;
}
