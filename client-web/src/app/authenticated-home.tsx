"use client";

import { SignInButton, UserButton, useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  ApiRequestError,
  basicsComplete,
  emptyCandidateProfileDraft,
  getCandidateProfile,
  getCurrentUser,
  profileToDraft,
  saveCandidateProfile,
  type CandidateProfile,
  type CandidateProfileDraft,
  type CurrentUser,
  type RemotePreference,
} from "../lib/api";

type LoadState = "loading" | "ready" | "error";
type SaveState = "idle" | "saving" | "saved" | "error" | "conflict";

const MAX_NAME = 150;
const MAX_HEADLINE = 200;
const MAX_LOCATION = 200;
const MAX_EXPERIENCE = 5000;
const MAX_LIST_ITEM = 100;
const MAX_LIST_ITEMS = 10;

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function formatSavedAt(value: string | null): string {
  if (!value) return "Not saved yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Saved";
  return `Saved ${new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date)}`;
}

function trimList(values: string[]): string[] {
  return values.map((value) => value.trim()).filter(Boolean);
}

function validateDraft(draft: CandidateProfileDraft): string | null {
  if (draft.full_name.length > MAX_NAME) return `Name must be ${MAX_NAME} characters or fewer.`;
  if (draft.headline.length > MAX_HEADLINE) return `Headline must be ${MAX_HEADLINE} characters or fewer.`;
  if (draft.location.length > MAX_LOCATION) return `Location must be ${MAX_LOCATION} characters or fewer.`;
  if (draft.experience_summary.length > MAX_EXPERIENCE) {
    return `Experience summary must be ${MAX_EXPERIENCE} characters or fewer.`;
  }
  for (const [label, values] of [
    ["Target roles", draft.target_roles],
    ["Preferred locations", draft.preferred_locations],
  ] as const) {
    if (values.length > MAX_LIST_ITEMS) return `${label} can include up to ${MAX_LIST_ITEMS} items.`;
    if (values.some((value) => value.length > MAX_LIST_ITEM)) {
      return `${label} entries must be ${MAX_LIST_ITEM} characters or fewer.`;
    }
  }
  return null;
}

function listIssue(values: string[], label: string): string | undefined {
  if (values.length > MAX_LIST_ITEMS) return `${label} can include up to ${MAX_LIST_ITEMS} items.`;
  if (values.some((value) => value.length > MAX_LIST_ITEM)) return `Each ${label.toLowerCase()} entry must be ${MAX_LIST_ITEM} characters or fewer.`;
  return undefined;
}

const ROLE_SUGGESTIONS = [
  "Product Designer",
  "Product Manager",
  "Software Engineer",
  "Frontend Engineer",
  "Backend Engineer",
  "Data Scientist",
  "UX Researcher",
  "Growth Marketing Manager",
  "Engineering Manager",
  "Chief of Staff",
];

const LOCATION_SUGGESTIONS = [
  "Remote",
  "New York, NY",
  "San Francisco, CA",
  "London, UK",
  "Toronto, Canada",
  "Berlin, Germany",
  "Singapore",
  "Bengaluru, India",
  "Mumbai, India",
  "Delhi, India",
];

function TagCombobox({
  id,
  values,
  onChange,
  suggestions,
  placeholder,
  label,
}: {
  id: string;
  values: string[];
  onChange: (values: string[]) => void;
  suggestions: string[];
  placeholder: string;
  label: string;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredSuggestions = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return suggestions
      .filter((suggestion) => !values.some((value) => value.toLowerCase() === suggestion.toLowerCase()))
      .filter((suggestion) => !normalizedQuery || suggestion.toLowerCase().includes(normalizedQuery))
      .slice(0, 6);
  }, [query, suggestions, values]);

  const addValues = useCallback((rawValues: string[]) => {
    const additions = rawValues.map((value) => value.trim()).filter(Boolean);
    if (!additions.length) return;
    const next = [...values];
    for (const value of additions) {
      if (!next.some((existing) => existing.toLowerCase() === value.toLowerCase()) && next.length < MAX_LIST_ITEMS) {
        next.push(value);
      }
    }
    onChange(next);
  }, [onChange, values]);

  const commitQuery = useCallback(() => {
    if (!query.trim()) return;
    addValues([query]);
    setQuery("");
    setActiveIndex(0);
  }, [addValues, query]);

  const selectValue = useCallback((value: string) => {
    addValues([value]);
    setQuery("");
    setActiveIndex(0);
    setOpen(true);
    inputRef.current?.focus();
  }, [addValues]);

  const handleInputChange = (value: string) => {
    if (value.includes(",")) {
      const pieces = value.split(",");
      addValues(pieces.slice(0, -1));
      setQuery(pieces.at(-1)?.trimStart() ?? "");
    } else {
      setQuery(value);
    }
    setActiveIndex(0);
    setOpen(true);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(index + 1, Math.max(filteredSuggestions.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (filteredSuggestions[activeIndex]) selectValue(filteredSuggestions[activeIndex]);
      else commitQuery();
    } else if (event.key === "Escape") {
      setOpen(false);
    } else if (event.key === "Backspace" && !query && values.length) {
      onChange(values.slice(0, -1));
    }
  };

  return (
    <div className="tag-combobox">
      <div
        className="tag-input-shell"
        onClick={() => inputRef.current?.focus()}
      >
        {values.map((value) => (
          <span className="tag-chip" key={value}>
            {value}
            <button
              type="button"
              aria-label={`Remove ${value} from ${label}`}
              onClick={() => onChange(values.filter((item) => item !== value))}
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          id={id}
          value={query}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open && filteredSuggestions.length > 0}
          aria-controls={`${id}-options`}
          aria-activedescendant={filteredSuggestions[activeIndex] ? `${id}-option-${activeIndex}` : undefined}
          placeholder={values.length ? "Add another…" : placeholder}
          onFocus={() => setOpen(true)}
          onBlur={() => window.setTimeout(() => { commitQuery(); setOpen(false); }, 120)}
          onChange={(event) => handleInputChange(event.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>
      {open && filteredSuggestions.length > 0 ? (
        <ul className="tag-options" id={`${id}-options`} role="listbox" aria-label={`${label} suggestions`}>
          {filteredSuggestions.map((suggestion, index) => (
            <li key={suggestion} role="option" aria-selected={index === activeIndex} id={`${id}-option-${index}`}>
              <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => selectValue(suggestion)}>
                {suggestion}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function StateCard({
  eyebrow,
  title,
  body,
  action,
  children,
  userMenu = false,
}: {
  eyebrow: string;
  title: string;
  body: string;
  action?: React.ReactNode;
  children?: React.ReactNode;
  userMenu?: boolean;
}) {
  return (
    <main className="state-page">
      <div className="state-topbar">
        <Link className="brand" href="/" aria-label="Hammer The Founder home">
          <span className="brand-mark">H</span>
          <span>Hammer The Founder</span>
        </Link>
        {userMenu ? <UserButton /> : null}
      </div>
      <section className="state-card" aria-live="polite">
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{body}</p>
        {action ? <div className="state-action">{action}</div> : null}
        {children ? <div className="state-action">{children}</div> : null}
      </section>
    </main>
  );
}

export function SetupState() {
  return (
    <StateCard
      eyebrow="Authentication setup"
      title="Connect Clerk to open your workspace"
      body="Set NEXT_PUBLIC_AUTH_MODE=clerk and NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY in the local environment, then restart the client service."
    />
  );
}

function LoadingSkeleton() {
  return (
    <main className="app-shell">
      <div className="app-topbar"><span className="skeleton skeleton-brand" /><span className="skeleton skeleton-avatar" /></div>
      <div className="content-wrap">
        <span className="skeleton skeleton-kicker" />
        <span className="skeleton skeleton-title" />
        <span className="skeleton skeleton-copy" />
        <div className="workspace-grid skeleton-layout">
          <section className="panel skeleton-panel"><span className="skeleton skeleton-section" /><span className="skeleton skeleton-field" /><span className="skeleton skeleton-field" /><span className="skeleton skeleton-large" /></section>
          <aside className="panel skeleton-panel"><span className="skeleton skeleton-section" /><span className="skeleton skeleton-copy" /><span className="skeleton skeleton-copy" /></aside>
        </div>
      </div>
    </main>
  );
}

function AppHeader() {
  return (
    <header className="app-topbar">
      <Link className="brand" href="/" aria-label="Hammer The Founder home">
        <span className="brand-mark">H</span>
        <span className="brand-name">Hammer The Founder</span>
      </Link>
      <div className="topbar-right">
        <span className="coming-soon">Resume tools <span>coming later</span></span>
        <UserButton />
      </div>
    </header>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="field">
      <label htmlFor={htmlFor}>{label}</label>
      {children}
      {error ? <p className="field-error" id={`${htmlFor}-error`}>{error}</p> : hint ? <p className="field-hint">{hint}</p> : null}
    </div>
  );
}

function ProgressRail({ draft, profile }: { draft: CandidateProfileDraft; profile: CandidateProfile | null }) {
  const complete = basicsComplete(draft);
  const completedSections = [Boolean(draft.full_name.trim() && draft.location.trim()), Boolean(draft.experience_summary.trim()), draft.target_roles.length > 0].filter(Boolean).length;
  return (
    <aside className="panel guide-panel">
      <div className="guide-heading">
        <span className="eyebrow">Profile guide</span>
        <span className={`status-dot ${complete ? "is-complete" : ""}`} aria-hidden="true" />
      </div>
      <h2>{complete ? "Your essentials are in place" : "Start with the essentials"}</h2>
      <p className="muted">A clear snapshot helps us understand the work you want next. You can fill this in over time.</p>
      <div className="progress-block" aria-label={`${completedSections} of 3 essentials completed`}>
        <div className="progress-label"><span>Essentials</span><strong>{completedSections}/3</strong></div>
        <div className="progress-track"><span style={{ width: `${(completedSections / 3) * 100}%` }} /></div>
      </div>
      <ol className="guide-list">
        <li className={draft.full_name.trim() && draft.location.trim() ? "done" : ""}><span>01</span><div><strong>Basics</strong><small>Name and where you work</small></div></li>
        <li className={draft.experience_summary.trim() ? "done" : ""}><span>02</span><div><strong>Experience</strong><small>A concise career snapshot</small></div></li>
        <li className={draft.target_roles.length ? "done" : ""}><span>03</span><div><strong>Direction</strong><small>Roles and places to explore</small></div></li>
      </ol>
      <div className="guide-note">
        <span className="note-mark" aria-hidden="true">i</span>
        <p>Resume and review tools will be added later. For now, focus on making this profile yours.</p>
      </div>
      {profile ? <p className="last-saved">{formatSavedAt(profile.updated_at)}</p> : null}
    </aside>
  );
}

function ProfileForm({
  draft,
  setDraft,
  profile,
  saveState,
  savedAt,
  error,
  onSave,
  onEdit,
  onReload,
  onRetry,
}: {
  draft: CandidateProfileDraft;
  setDraft: React.Dispatch<React.SetStateAction<CandidateProfileDraft>>;
  profile: CandidateProfile | null;
  saveState: SaveState;
  savedAt: string | null;
  error: string | null;
  onSave: (nextDraft?: CandidateProfileDraft) => void;
  onEdit: () => void;
  onReload: () => void;
  onRetry: () => void;
}) {
  const [validationError, setValidationError] = useState<string | null>(null);
  const update = <K extends keyof CandidateProfileDraft>(key: K, value: CandidateProfileDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
    onEdit();
    if (validationError) setValidationError(null);
  };
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = {
      ...draft,
      full_name: draft.full_name.trim(),
      headline: draft.headline.trim(),
      location: draft.location.trim(),
      experience_summary: draft.experience_summary.trim(),
      target_roles: trimList(draft.target_roles),
      preferred_locations: trimList(draft.preferred_locations),
    };
    const issue = validateDraft(normalized);
    if (issue) {
      setValidationError(issue);
      return;
    }
    setDraft(normalized);
    onSave(normalized);
  };
  const isSaving = saveState === "saving";
  const targetRolesIssue = listIssue(draft.target_roles, "Target roles");
  const preferredLocationsIssue = listIssue(draft.preferred_locations, "Preferred locations");
  return (
    <form className="panel profile-panel" onSubmit={handleSubmit} noValidate>
      <div className="panel-heading">
        <div><span className="eyebrow">Your profile</span><h2>A focused introduction</h2></div>
        <span className={`save-status ${saveState}`} role="status" aria-live="polite">
          <span className="status-dot" aria-hidden="true" />
          {saveState === "saving" ? "Saving" : saveState === "saved" ? formatSavedAt(savedAt) : saveState === "conflict" ? "Needs review" : saveState === "error" ? "Not saved" : profile ? "Saved" : "Draft"}
        </span>
      </div>
      {saveState === "conflict" ? (
        <div className="notice notice-warning" role="alert">
          <div><strong>This profile changed elsewhere.</strong><p>Your local edits are still here. Reload the saved version only if you want to replace this draft.</p></div>
          <button type="button" className="button button-secondary button-small" onClick={onReload}>Reload saved version</button>
        </div>
      ) : null}
      {saveState === "error" ? (
        <div className="notice notice-error" role="alert">
          <div><strong>We couldn’t save this draft.</strong><p>{error ?? "Check your connection and try again."}</p></div>
          <button type="button" className="button button-secondary button-small" onClick={onRetry}>Try again</button>
        </div>
      ) : null}
      {validationError ? <div className="notice notice-error" role="alert"><strong>{validationError}</strong></div> : null}

      <div className="form-section">
        <div className="section-intro"><span className="section-number">01</span><div><h3>Basics</h3><p>Start with the details people will use to place you.</p></div></div>
        <div className="form-grid two-col">
          <Field label="Full name" htmlFor="full-name" hint={`${draft.full_name.length}/${MAX_NAME}`}>
            <input id="full-name" value={draft.full_name} maxLength={MAX_NAME} onChange={(event) => update("full_name", event.target.value)} placeholder="e.g. Alex Morgan" autoComplete="name" />
          </Field>
          <Field label="Headline" htmlFor="headline" hint="A short line about your work">
            <input id="headline" value={draft.headline} maxLength={MAX_HEADLINE} onChange={(event) => update("headline", event.target.value)} placeholder="e.g. Product designer for early-stage teams" />
          </Field>
        </div>
        <div className="form-grid two-col">
          <Field label="Current location" htmlFor="location" hint={`${draft.location.length}/${MAX_LOCATION}`}>
            <input id="location" value={draft.location} maxLength={MAX_LOCATION} onChange={(event) => update("location", event.target.value)} placeholder="e.g. Brooklyn, NY" autoComplete="address-level2" />
          </Field>
          <Field label="Work preference" htmlFor="remote-preference" hint="You can change this later">
            <select id="remote-preference" value={draft.remote_preference} onChange={(event) => update("remote_preference", event.target.value as RemotePreference)}>
              <option value="UNSPECIFIED">Not sure yet</option><option value="ONSITE">On-site</option><option value="HYBRID">Hybrid</option><option value="REMOTE">Remote</option><option value="FLEXIBLE">Flexible</option>
            </select>
          </Field>
        </div>
      </div>

      <div className="form-section">
        <div className="section-intro"><span className="section-number">02</span><div><h3>Experience</h3><p>Give a little context to the work behind your next move.</p></div></div>
        <Field label="Experience summary" htmlFor="experience-summary" hint={`${draft.experience_summary.length}/${MAX_EXPERIENCE}`}>
          <textarea id="experience-summary" value={draft.experience_summary} maxLength={MAX_EXPERIENCE} onChange={(event) => update("experience_summary", event.target.value)} placeholder="Share the kinds of problems you solve, the teams you’ve worked with, and the impact you’re proud of." rows={7} />
        </Field>
      </div>

      <div className="form-section form-section-last">
        <div className="section-intro"><span className="section-number">03</span><div><h3>Direction</h3><p>Point toward the opportunities that feel worth exploring.</p></div></div>
        <Field label="Target roles" htmlFor="target-roles" error={targetRolesIssue} hint={targetRolesIssue ? undefined : "Type to search suggestions, then press Enter or choose an option · up to 10"}>
          <TagCombobox id="target-roles" label="target roles" values={draft.target_roles} onChange={(values) => update("target_roles", values)} suggestions={ROLE_SUGGESTIONS} placeholder="e.g. Product Designer" />
        </Field>
        <Field label="Preferred locations" htmlFor="preferred-locations" error={preferredLocationsIssue} hint={preferredLocationsIssue ? undefined : "Type to search suggestions, then press Enter or choose an option · up to 10"}>
          <TagCombobox id="preferred-locations" label="preferred locations" values={draft.preferred_locations} onChange={(values) => update("preferred_locations", values)} suggestions={LOCATION_SUGGESTIONS} placeholder="e.g. New York, NY" />
        </Field>
      </div>

      <div className="form-footer">
        <p className="save-help">{profile ? "Your changes are only sent when you save." : "It’s okay to save an unfinished draft."}</p>
        <button className="button button-primary" type="submit" disabled={isSaving}>
          {isSaving ? <><span className="button-spinner" aria-hidden="true" /> Saving draft</> : "Save draft"}
        </button>
      </div>
    </form>
  );
}

function CandidateWorkspace({ getToken }: { getToken: () => Promise<string | null> }) {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [draft, setDraft] = useState<CandidateProfileDraft>({ ...emptyCandidateProfileDraft });
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);
  const versionRef = useRef(0);
  const saveControllerRef = useRef<AbortController | null>(null);
  const profileControllerRef = useRef<AbortController | null>(null);

  useEffect(() => () => {
    saveControllerRef.current?.abort();
    profileControllerRef.current?.abort();
  }, []);

  const loadProfile = useCallback(async (signal: AbortSignal, apply: boolean) => {
    const nextProfile = await getCandidateProfile(getToken, signal);
    if (apply) {
      setProfile(nextProfile);
      setDraft(profileToDraft(nextProfile));
      versionRef.current = nextProfile?.profile_version ?? 0;
      setSavedAt(nextProfile?.updated_at ?? null);
    }
    return nextProfile;
  }, [getToken]);

  useEffect(() => {
    profileControllerRef.current?.abort();
    const controller = new AbortController();
    profileControllerRef.current = controller;
    // The async request synchronizes this screen with the API; its state updates happen after the response.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadProfile(controller.signal, true)
      .then(() => { if (!controller.signal.aborted) setLoadState("ready"); })
      .catch((requestError: unknown) => {
        if (isAbortError(requestError) || controller.signal.aborted) return;
        setError(errorMessage(requestError, "We could not load your profile."));
        setLoadState("error");
      });
    return () => {
      controller.abort();
      if (profileControllerRef.current === controller) profileControllerRef.current = null;
    };
  }, [loadProfile, retryKey]);

  const save = useCallback(async (nextDraft?: CandidateProfileDraft) => {
    setSaveState("saving");
    setError(null);
    saveControllerRef.current?.abort();
    const controller = new AbortController();
    saveControllerRef.current = controller;
    try {
      const saved = await saveCandidateProfile(getToken, nextDraft ?? draft, versionRef.current, controller.signal);
      setProfile(saved);
      setDraft(profileToDraft(saved));
      versionRef.current = saved.profile_version;
      setSavedAt(saved.updated_at);
      setSaveState("saved");
    } catch (requestError: unknown) {
      if (isAbortError(requestError)) return;
      if (requestError instanceof ApiRequestError && requestError.status === 409) {
        setSaveState("conflict");
      } else {
        setError(errorMessage(requestError, "We could not save your profile."));
        setSaveState("error");
      }
    }
  }, [draft, getToken]);

  const reloadSavedVersion = useCallback(() => {
    setLoadState("loading");
    profileControllerRef.current?.abort();
    const controller = new AbortController();
    profileControllerRef.current = controller;
    void loadProfile(controller.signal, true)
      .then(() => {
        if (!controller.signal.aborted) {
          setSaveState("idle");
          setLoadState("ready");
        }
      })
      .catch((requestError: unknown) => {
        if (isAbortError(requestError)) return;
        setError(errorMessage(requestError, "We could not reload your profile."));
        setSaveState("error");
        setLoadState("ready");
      });
  }, [loadProfile]);

  const ready = loadState === "ready";
  const draftIsComplete = useMemo(() => basicsComplete(draft), [draft]);
  if (loadState === "loading") return <LoadingSkeleton />;
  if (loadState === "error") {
    return <StateCard eyebrow="Candidate profile" title="Your profile is taking a moment" body={error ?? "We could not reach the HTF API."} userMenu action={<button className="button button-primary" type="button" onClick={() => setRetryKey((key) => key + 1)}>Try again</button>} />;
  }
  if (!ready) return null;

  return (
    <main className="app-shell">
      <AppHeader />
      <div className="content-wrap">
        <div className="page-intro">
          <span className="eyebrow">Candidate profile</span>
          <h1>Make your next move legible<span className="accent-dot">.</span></h1>
          <p>Tell us enough about your experience and direction to make the right opportunities easier to recognize.</p>
        </div>
        <div className="workspace-grid">
          <ProfileForm draft={draft} setDraft={setDraft} profile={profile} saveState={saveState} savedAt={savedAt} error={error} onSave={save} onEdit={() => setSaveState((state) => state === "saved" ? "idle" : state)} onReload={reloadSavedVersion} onRetry={() => save()} />
          <ProgressRail draft={draft} profile={profile} />
        </div>
        <p className="privacy-note"><span aria-hidden="true">↗</span> You’re in control of this profile. Edit or update it whenever your direction changes.</p>
        <span className="sr-only">{draftIsComplete ? "Your profile essentials are complete." : "Your profile is an in-progress draft."}</span>
      </div>
    </main>
  );
}

export default function AuthenticatedHome() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [identityState, setIdentityState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    const controller = new AbortController();
    void getCurrentUser(getToken, controller.signal)
      .then((currentUser) => {
        if (controller.signal.aborted) return;
        setUser(currentUser);
        setIdentityState("ready");
      })
      .catch((requestError: unknown) => {
        if (isAbortError(requestError) || controller.signal.aborted) return;
        setError(errorMessage(requestError, "Unable to load your account."));
        setIdentityState("error");
      });
    return () => controller.abort();
  }, [getToken, isLoaded, isSignedIn, retryKey]);

  if (!isLoaded) return <LoadingSkeleton />;
  if (!isSignedIn) {
    return (
      <StateCard eyebrow="Hammer The Founder" title="Your next move, with a clearer starting point" body="Sign in to shape your candidate profile and keep your direction in one place.">
        <SignInButton mode="modal"><button className="button button-primary" type="button">Sign in</button></SignInButton>
      </StateCard>
    );
  }
  if (identityState === "loading") return <LoadingSkeleton />;
  if (identityState === "error") {
    return <StateCard eyebrow="Account connection" title="We could not load your account" body={error ?? "The HTF API did not respond."} userMenu action={<button className="button button-primary" type="button" onClick={() => setRetryKey((key) => key + 1)}>Try again</button>} />;
  }
  if (!user) return null;
  if (user.role !== "CLIENT") {
    return <StateCard eyebrow="HTF workspace" title="This workspace is for candidates" body={`You’re signed in with the ${user.role.toLowerCase()} role. Candidate profile editing is available to CLIENT accounts; no candidate profile was loaded.`} userMenu />;
  }
  return <CandidateWorkspace key={user.id} getToken={getToken} />;
}
