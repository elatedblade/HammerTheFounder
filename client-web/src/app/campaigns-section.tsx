"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  getCampaigns,
  type Campaign,
  type CampaignBillingStatus,
  type CampaignPlan,
  type CampaignStatus,
} from "../lib/api";

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function formatDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

function formatPlan(plan: CampaignPlan): string {
  const labels: Record<CampaignPlan, string> = {
    NORMAL_APPLY: "Normal Apply",
    COLD_APPLY: "Cold Apply",
    FULL_THROTTLE: "Full-Throttle Sprint",
  };
  return labels[plan] ?? plan;
}

function formatStatus(status: CampaignStatus): string {
  const labels: Record<CampaignStatus, string> = {
    DRAFT: "Draft",
    ONBOARDING: "Onboarding",
    READY: "Ready",
    ACTIVE: "Active",
    PAUSED: "Paused",
    COMPLETED: "Completed",
    CANCELLED: "Cancelled",
  };
  return labels[status] ?? status;
}

function formatBillingStatus(status: CampaignBillingStatus): string {
  const labels: Record<CampaignBillingStatus, string> = {
    PENDING: "Pending",
    ACTIVE: "Active",
    PAST_DUE: "Past due",
    CANCELLED: "Cancelled",
  };
  return labels[status] ?? status;
}

function statusTone(status: CampaignStatus): "positive" | "warning" | "danger" | "neutral" {
  if (status === "ACTIVE" || status === "READY" || status === "COMPLETED") return "positive";
  if (status === "DRAFT" || status === "ONBOARDING" || status === "PAUSED") return "warning";
  if (status === "CANCELLED") return "danger";
  return "neutral";
}

const availablePlans = [
  { name: "Normal Apply", code: "NORMAL_APPLY", description: "Managed job applications." },
  { name: "Cold Apply", code: "COLD_APPLY", description: "Manual founder/CXO outreach." },
  { name: "Full-Throttle Sprint", code: "FULL_THROTTLE", description: "Both managed applications and manual outreach." },
] as const;

function CampaignCard({ campaign }: { campaign: Campaign }) {
  const trialEnd = formatDate(campaign.trial_end_date);
  const startDate = formatDate(campaign.start_date);
  return (
    <li className="campaign-card">
      <div className="campaign-card-heading">
        <div>
          <h3>{formatPlan(campaign.plan)}</h3>
          <span className={`campaign-status is-${statusTone(campaign.status)}`}>{formatStatus(campaign.status)}</span>
        </div>
      </div>
      <dl className="campaign-meta">
        <div>
          <dt>Trial ends</dt>
          <dd>{trialEnd ?? "No trial end date"}</dd>
        </div>
        <div>
          <dt>Billing</dt>
          <dd>{formatBillingStatus(campaign.billing_status)}</dd>
        </div>
        {startDate ? (
          <div>
            <dt>Started</dt>
            <dd><time dateTime={campaign.start_date ?? undefined}>{startDate}</time></dd>
          </div>
        ) : null}
      </dl>
    </li>
  );
}

export default function CampaignsSection({ getToken }: { getToken: () => Promise<string | null> }) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const refreshCampaigns = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const nextCampaigns = await getCampaigns(getToken, controller.signal);
      if (controller.signal.aborted) return;
      setCampaigns(nextCampaigns);
    } catch (requestError: unknown) {
      if (isAbortError(requestError) || controller.signal.aborted) return;
      setError(requestError instanceof Error ? requestError.message : "We could not load your campaigns.");
    } finally {
      if (!controller.signal.aborted) setLoading(false);
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  }, [getToken]);

  useEffect(() => {
    // This effect synchronizes campaign metadata with the authenticated API.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshCampaigns();
    return () => controllerRef.current?.abort();
  }, [refreshCampaigns]);

  return (
    <section id="campaigns" className="panel campaign-panel" aria-labelledby="campaigns-heading">
      <div className="panel-heading">
        <div><span className="eyebrow">Your workspace</span><h2 id="campaigns-heading">Campaigns</h2></div>
        <button className="button button-secondary button-small" type="button" disabled={loading} onClick={() => void refreshCampaigns()}>
          {loading ? <><span className="button-spinner button-spinner-dark" aria-hidden="true" />Loading campaigns</> : "Refresh list"}
        </button>
      </div>
      <p className="muted">Your campaign details will appear here once HTF has set up your next search.</p>

      <section className="available-plans" aria-labelledby="available-plans-heading">
        <div className="available-plans-heading">
          <div>
            <span className="eyebrow">Service options</span>
            <h3 id="available-plans-heading">Available service plans</h3>
          </div>
          <p>Plans are reviewed and activated by the HTF team.</p>
        </div>
        <ul className="available-plans-list">
          {availablePlans.map((plan) => (
            <li className="available-plan-card" key={plan.code}>
              <strong>{plan.name}</strong>
              <span>{plan.code}</span>
              <p>{plan.description}</p>
            </li>
          ))}
        </ul>
      </section>

      <div className="campaign-records" aria-live="polite">
        <h3 className="campaign-records-heading">Your campaigns</h3>
        {loading ? <p className="muted campaign-loading" role="status">Loading your campaigns…</p> : null}
        {error ? (
          <div className="notice notice-error campaign-error" role="alert">
            <div><strong>We couldn’t load your campaigns.</strong><p>{error}</p></div>
            <button className="button button-secondary button-small" type="button" onClick={() => void refreshCampaigns()}>Try again</button>
          </div>
        ) : null}
        {!loading && !error && campaigns.length === 0 ? (
          <div className="campaign-empty">
            <strong>No campaign assigned yet</strong>
            <p>No campaign is assigned to your workspace yet. An HTF operator creates and activates one after reviewing your profile and onboarding details.</p>
          </div>
        ) : null}
        {!loading && !error && campaigns.length > 0 ? (
          <ul className="campaign-list">
            {campaigns.map((campaign) => <CampaignCard key={campaign.id} campaign={campaign} />)}
          </ul>
        ) : null}
      </div>
    </section>
  );
}
