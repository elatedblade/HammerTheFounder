"use client";

import { type CandidateProfileDraft } from "../lib/api";

export default function IntakeFields({draft, update, errors}: {
  draft: CandidateProfileDraft;
  update: <K extends keyof CandidateProfileDraft>(key: K, value: CandidateProfileDraft[K]) => void;
  errors: Record<string, string>;
}) {
  const preferences = draft.preferences_json ?? {};
  const preference = (key: string) => typeof preferences[key] === "string" ? preferences[key] as string : "";
  const setPreference = (key: string, value: string) => update("preferences_json", {...preferences, [key]: value});
  return <div className="form-section form-section-last">
    <div className="section-intro"><span className="section-number">04</span><div><h3>Search constraints</h3><p>Optional details that help HTF focus your campaign.</p></div></div>
    <div className="field"><label htmlFor="target-industries">Target industries</label><input id="target-industries" value={(draft.target_industries ?? []).join(",")} onChange={event => update("target_industries", event.target.value.split(","))} aria-invalid={Boolean(errors.target_industries)} aria-describedby="target-industries-hint"/><p id="target-industries-hint" className="field-hint">Comma-separated; up to 10 industries, 100 characters each.</p>{errors.target_industries ? <p className="field-error">{errors.target_industries}</p> : null}</div>
    <p className="muted">Expected annual compensation / CTC. Specify currency and units below so your team can interpret these amounts correctly.</p>
    <div className="form-grid two-col">
      {(["expected_ctc_min", "expected_ctc_max"] as const).map(key => <div className="field" key={key}><label htmlFor={key}>{key === "expected_ctc_min" ? "Minimum expected compensation" : "Maximum expected compensation"}</label><input id={key} type="number" min="0" step="0.01" value={draft[key] ?? ""} onChange={event => update(key, event.target.value === "" ? null : Number(event.target.value))} aria-invalid={Boolean(errors[key])} aria-describedby={errors[key] ? `${key}-error` : undefined}/>{errors[key] ? <p id={`${key}-error`} className="field-error">{errors[key]}</p> : null}</div>)}
    </div>
    <div className="field"><label htmlFor="compensation-units">Compensation currency and units</label><input id="compensation-units" value={preference("compensation_units")} maxLength={200} placeholder="e.g. INR per year, full rupees (not lakhs)" onChange={event => setPreference("compensation_units", event.target.value)}/></div>
    <div className="form-grid two-col">
      {([ ["work_authorization", "Work authorization", "e.g. Authorized to work in India"], ["sponsorship_requirement", "Sponsorship requirement", "e.g. No sponsorship required"], ["notice_period", "Notice period / availability", "e.g. 30 days"] ] as const).map(([key, label, placeholder]) => <div className="field" key={key}><label htmlFor={key}>{label}</label><input id={key} value={draft[key] ?? ""} maxLength={200} placeholder={placeholder} onChange={event => update(key, event.target.value)} aria-invalid={Boolean(errors[key])} aria-describedby={errors[key] ? `${key}-error` : undefined}/>{errors[key] ? <p id={`${key}-error`} className="field-error">{errors[key]}</p> : null}</div>)}
      <div className="field"><label htmlFor="employment-preferences">Employment preferences</label><input id="employment-preferences" value={preference("employment_type")} maxLength={200} placeholder="e.g. Full-time only" onChange={event => setPreference("employment_type", event.target.value)}/></div>
    </div>
    <div className="field"><label htmlFor="company-preferences">Company preferences</label><input id="company-preferences" value={preference("company_preferences")} maxLength={1000} placeholder="e.g. Early-stage SaaS, teams of 20–100" onChange={event => setPreference("company_preferences", event.target.value)}/></div>
    <div className="field"><label htmlFor="additional-preferences">Other preferences and exclusions</label><textarea id="additional-preferences" value={preference("additional_preferences")} maxLength={3000} rows={4} placeholder="Travel, time zones, relocation, industries or companies to exclude…" onChange={event => setPreference("additional_preferences", event.target.value)}/>{errors.preferences_json ? <p className="field-error">{errors.preferences_json}</p> : null}</div>
  </div>;
}
