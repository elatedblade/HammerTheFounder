"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiRequestError, apiFieldErrors, emptyCandidateProfileDraft, getCandidateProfile, getCurrentUser, profileToDraft, saveCandidateProfile, type CandidateProfile, type CandidateProfileDraft } from "../../lib/api";
import { AccessDeniedState, AppHeader, LoadingSkeleton, SignedOutState } from "../customer-shell";
import { ProfileForm, ProgressRail } from "./profile-components";
import ResumeSection from "../resume-section";

export default function ProfileScreen() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { user: clerkUser } = useUser();
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [draft, setDraft] = useState<CandidateProfileDraft>({ ...emptyCandidateProfileDraft });
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error" | "conflict">("idle");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [role, setRole] = useState("CLIENT");
  const version = useRef(0);
  const draftRef = useRef(draft);
  const loadController = useRef<AbortController | null>(null);
  const saveController = useRef<AbortController | null>(null);
  useEffect(() => { draftRef.current = draft; }, [draft]);
  const load = useCallback(async (signal: AbortSignal) => {
    const user = await getCurrentUser(getToken, signal);
    setRole(user.role);
    if (user.role !== "CLIENT") { setState("ready"); return; }
    const value = await getCandidateProfile(getToken, signal); setProfile(value); setDraft(profileToDraft(value)); version.current = value?.profile_version ?? 0;
  }, [getToken]);
  // The request callback synchronizes this account's server snapshot; the keyed route prevents cross-account reuse.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (!isLoaded || !isSignedIn || !clerkUser?.id) return; loadController.current?.abort(); saveController.current?.abort(); const controller = new AbortController(); loadController.current = controller; void load(controller.signal).then(() => { if (!controller.signal.aborted) setState("ready"); }).catch((e) => { if (!controller.signal.aborted) { setError(e instanceof Error ? e.message : "We could not load your profile."); setState("error"); } }); return () => { controller.abort(); saveController.current?.abort(); }; }, [isLoaded, isSignedIn, clerkUser?.id, load]);
  const save = async (next?: CandidateProfileDraft) => { if (saveController.current) return; const snapshot = next ?? draftRef.current; setSaveState("saving"); setError(null); setFieldErrors({}); const controller = new AbortController(); saveController.current = controller; try { const value = await saveCandidateProfile(getToken, snapshot, version.current, controller.signal); setProfile(value); if (JSON.stringify(draftRef.current) === JSON.stringify(snapshot)) setDraft(profileToDraft(value)); version.current = value.profile_version; setSaveState("saved"); } catch (e) { if (controller.signal.aborted) return; if (e instanceof ApiRequestError && e.status === 409) setSaveState("conflict"); else { setError(e instanceof Error ? e.message : "We could not save your profile."); setFieldErrors(apiFieldErrors(e)); setSaveState("error"); } } finally { if (saveController.current === controller) saveController.current = null; } };
  const reloadSaved = () => { if (saveController.current) return; setSaveState("idle"); setError(null); setFieldErrors({}); const controller = new AbortController(); loadController.current?.abort(); loadController.current = controller; setState("loading"); void load(controller.signal).then(() => { if (!controller.signal.aborted) setState("ready"); }).catch((e) => { if (!controller.signal.aborted) { setError(e instanceof Error ? e.message : "We could not reload your profile."); setState("error"); } }); };
  if (!isLoaded) return <LoadingSkeleton />;
  if (!isSignedIn) return <SignedOutState redirect="/profile" />;
  if (state === "loading") return <LoadingSkeleton />;
  if (state === "error") return <main className="state-page"><section className="state-card"><span className="eyebrow">Candidate profile</span><h1>Profile unavailable</h1><p>{error}</p><div className="auth-actions"><button className="button button-primary" type="button" onClick={reloadSaved}>Try again</button><Link className="button button-secondary" href="/dashboard">Go to dashboard</Link></div></section></main>;
  if (role !== "CLIENT") return <AccessDeniedState adminUrl={process.env.NEXT_PUBLIC_ADMIN_URL ?? "http://localhost:3001"} />;
  return <main className="app-shell"><AppHeader /><div className="content-wrap"><div className="page-intro"><span className="eyebrow">Candidate profile</span><h1>Keep your direction current<span className="accent-dot">.</span></h1><p>Your intake, preferences and resume are private to your profile. HTF reviews saved information before campaign execution.</p></div><nav className="workspace-jump" aria-label="Profile sections"><a href="#profile">Intake and preferences</a><a href="#documents">Resume</a><Link href="/dashboard">View dashboard</Link></nav><div className="workspace-grid" id="profile"><ProfileForm draft={draft} setDraft={setDraft} profile={profile} saveState={saveState} savedAt={profile?.updated_at ?? null} error={error} fieldErrors={fieldErrors} onSave={save} onEdit={() => setSaveState(s => s === "saved" ? "idle" : s)} onReload={reloadSaved} onRetry={() => void save()} /><ProgressRail draft={draft} profile={profile} /></div><ResumeSection getToken={getToken} /><p className="privacy-note">Profile information is not shown on the progress dashboard.</p></div></main>;
}
