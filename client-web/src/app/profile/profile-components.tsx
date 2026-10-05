"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { basicsComplete, type CandidateProfile, type CandidateProfileDraft, type RemotePreference } from "../../lib/api";
import { readable } from "../candidate-progress";
import IntakeFields from "../intake-fields";
import { LOCATION_SUGGESTIONS, ROLE_SUGGESTIONS } from "./profile-suggestions";
import { appendTagValue, getTagOptions, MAX_TAG_ITEM_LENGTH, MAX_TAG_ITEMS, tagInputIssue } from "./tag-options";

type SaveState = "idle" | "saving" | "saved" | "error" | "conflict";

const MAX_NAME = 150;
const MAX_HEADLINE = 200;
const MAX_LOCATION = 200;
const MAX_EXPERIENCE = 5000;
const MAX_LIST_ITEM = MAX_TAG_ITEM_LENGTH;
const MAX_LIST_ITEMS = MAX_TAG_ITEMS;

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
    ["Target industries", draft.target_industries ?? []],
  ] as const) {
    if (values.length > MAX_LIST_ITEMS) return `${label} can include up to ${MAX_LIST_ITEMS} items.`;
    if (values.some((value) => value.length > MAX_LIST_ITEM)) {
      return `${label} entries must be ${MAX_LIST_ITEM} characters or fewer.`;
    }
  }
  for (const value of [draft.expected_ctc_min, draft.expected_ctc_max]) {
    if (value !== null && value !== undefined && (!Number.isFinite(value) || value < 0 || value > 999999999999.99)) return "Compensation must be a non-negative number no greater than 999,999,999,999.99.";
  }
  if (draft.expected_ctc_min != null && draft.expected_ctc_max != null && draft.expected_ctc_min > draft.expected_ctc_max) return "Minimum compensation cannot exceed maximum compensation.";
  if ((draft.expected_ctc_min != null || draft.expected_ctc_max != null) && !(typeof draft.preferences_json?.compensation_units === "string" && draft.preferences_json.compensation_units.trim())) return "Add compensation currency and units when specifying an expected amount.";
  return null;
}

function listIssue(values: string[], label: string): string | undefined {
  if (values.length > MAX_LIST_ITEMS) return `${label} can include up to ${MAX_LIST_ITEMS} items.`;
  if (values.some((value) => value.length > MAX_LIST_ITEM)) return `Each ${label.toLowerCase()} entry must be ${MAX_LIST_ITEM} characters or fewer.`;
  return undefined;
}

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
  suggestions: readonly string[];
  placeholder: string;
  label: string;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const optionsRef = useRef<HTMLUListElement>(null);
  const queryRef = useRef("");
  const valuesRef = useRef(values);
  const { options, matchingCount } = useMemo(() => getTagOptions(query, values, suggestions), [query, suggestions, values]);
  const queryIssue = tagInputIssue(values, query);
  const listOpen = open && options.length > 0;
  const activeOption = listOpen && activeIndex >= 0 ? options[activeIndex] : undefined;

  useEffect(() => { valuesRef.current = values; }, [values]);
  useEffect(() => {
    if (activeOption) optionsRef.current?.children[activeIndex]?.scrollIntoView({ block: "nearest" });
  }, [activeIndex, activeOption]);

  const clearQuery = useCallback(() => {
    // Clear synchronously so a click followed by blur cannot commit an old query.
    queryRef.current = "";
    setQuery("");
    setActiveIndex(-1);
  }, []);

  const addValue = useCallback((rawValue: string) => {
    const current = valuesRef.current;
    const next = appendTagValue(current, rawValue);
    if (next === current) return false;
    valuesRef.current = next;
    onChange(next);
    return true;
  }, [onChange]);

  const commitQuery = useCallback(() => {
    const pending = queryRef.current;
    if (!pending.trim()) return;
    if (addValue(pending) || valuesRef.current.some((value) => value.trim().toLowerCase() === pending.trim().toLowerCase())) clearQuery();
  }, [addValue, clearQuery]);

  const selectValue = useCallback((value: string) => {
    if (!addValue(value)) return;
    clearQuery();
    setOpen(true);
    inputRef.current?.focus();
  }, [addValue, clearQuery]);

  const handleInputChange = (value: string) => {
    queryRef.current = value;
    setQuery(value);
    setActiveIndex(-1);
    setOpen(true);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.nativeEvent.isComposing) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => options.length ? (listOpen ? Math.min(index + 1, options.length - 1) : 0) : -1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => options.length ? (listOpen && index >= 0 ? Math.max(index - 1, 0) : options.length - 1) : -1);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (activeOption) selectValue(activeOption.value);
      else commitQuery();
    } else if (event.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
    } else if (event.key === "Backspace" && !query && values.length) {
      onChange(values.slice(0, -1));
    }
  };

  return (
    <div className="tag-combobox" onBlur={(event) => {
      if (event.currentTarget.contains(event.relatedTarget)) return;
      commitQuery();
      setOpen(false);
      setActiveIndex(-1);
    }}>
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
          aria-expanded={listOpen}
          aria-controls={listOpen ? `${id}-options` : undefined}
          aria-activedescendant={activeOption ? `${id}-option-${activeIndex}` : undefined}
          aria-describedby={`${id}-hint${queryIssue ? ` ${id}-query-error` : ""}`}
          aria-invalid={Boolean(queryIssue)}
          placeholder={values.length ? "Add another…" : placeholder}
          onFocus={() => setOpen(true)}
          onChange={(event) => handleInputChange(event.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>
      <p className="field-hint" id={`${id}-hint`}>Browse suggestions or type to narrow. Press Enter to add your exact text, or use arrow keys to choose an option. Custom entries are welcome; commas stay within one entry. Up to {MAX_LIST_ITEMS} entries, {MAX_LIST_ITEM} characters each.</p>
      {queryIssue ? <p className="field-error" id={`${id}-query-error`} role="status">{queryIssue}</p> : null}
      {listOpen ? (
        <ul ref={optionsRef} className="tag-options" id={`${id}-options`} role="listbox" aria-label={`${label} suggestions`}>
          {options.map((option, index) => (
            <li key={option.value} role="option" aria-selected={index === activeIndex} id={`${id}-option-${index}`}>
              <button type="button" tabIndex={-1} onPointerDown={(event) => event.preventDefault()} onMouseDown={(event) => event.preventDefault()} onClick={() => selectValue(option.value)}>
                {option.custom ? `Add “${option.value}” (custom)` : option.value}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {listOpen && matchingCount > options.filter((option) => !option.custom).length ? <p className="field-hint" role="status">Showing {options.filter((option) => !option.custom).length} of {matchingCount} suggestions. Type to narrow the list.</p> : null}
    </div>
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

export function ProgressRail({ draft, profile }: { draft: CandidateProfileDraft; profile: CandidateProfile | null }) {
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
      {profile ? <p className="last-saved">{formatSavedAt(profile.updated_at)}</p> : null}
    </aside>
  );
}

export function ProfileForm({
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
  fieldErrors,
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
  fieldErrors: Record<string, string>;
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
      target_industries: trimList(draft.target_industries ?? []),
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
      {Object.keys(fieldErrors).length > 0 ? <ul className="api-field-errors" role="alert">{Object.entries(fieldErrors).map(([field, message]) => <li key={field}><strong>{readable(field)}:</strong> {message}</li>)}</ul> : null}
      <p className="muted">Profile review: <strong>{profile?.review_status ? readable(profile.review_status) : "Not reviewed yet"}</strong>. {profile?.review_status === "CHANGES_REQUESTED" ? "Contact HTF for requested changes, then update your profile below." : "HTF reviews your saved information before campaign execution."}</p>

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

      <div className="form-section">
        <div className="section-intro"><span className="section-number">03</span><div><h3>Direction</h3><p>Point toward the opportunities that feel worth exploring.</p></div></div>
        <Field label="Target roles" htmlFor="target-roles" error={targetRolesIssue}>
          <TagCombobox id="target-roles" label="target roles" values={draft.target_roles} onChange={(values) => update("target_roles", values)} suggestions={ROLE_SUGGESTIONS} placeholder="e.g. Product Designer" />
        </Field>
        <Field label="Preferred locations" htmlFor="preferred-locations" error={preferredLocationsIssue}>
          <TagCombobox id="preferred-locations" label="preferred locations" values={draft.preferred_locations} onChange={(values) => update("preferred_locations", values)} suggestions={LOCATION_SUGGESTIONS} placeholder="e.g. New York, NY" />
        </Field>
      </div>

      <IntakeFields draft={draft} update={update} errors={fieldErrors}/>
      <div className="form-footer">
        <p className="save-help">{profile ? "Your changes are only sent when you save." : "It’s okay to save an unfinished draft."}</p>
        <button className="button button-primary" type="submit" disabled={isSaving}>
          {isSaving ? <><span className="button-spinner" aria-hidden="true" /> Saving draft</> : "Save draft"}
        </button>
      </div>
    </form>
  );
}
