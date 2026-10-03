"use client";

import { useEffect, useId, useState } from "react";
import { ApiError, type ApiClient } from "../../lib/api";
import { display, humanize, type Field, type Option, type RecordData } from "./types";

export function ErrorMessage({ error }: { error: unknown }) {
  if (!error) return null;
  return <div className="error" role="alert"><strong>{error instanceof Error ? error.message : String(error)}</strong>{error instanceof ApiError && error.details && <ul>{Object.entries(error.details).map(([key, value]) => <li key={key}>{humanize(key)}: {display(value)}</li>)}</ul>}</div>;
}

export function useRecords(api: ApiClient, path: string, revision: number) {
  const key = `${path}:${revision}`;
  const [result, setResult] = useState<{ key: string; data: RecordData[]; error: unknown }>({ key: "", data: [], error: null });
  useEffect(() => {
    let alive = true;
    api<RecordData[]>(path).then((rows) => { if (alive) setResult({ key, data: rows, error: null }); }).catch((error: unknown) => { if (alive) setResult({ key, data: [], error }); });
    return () => { alive = false; };
  }, [api, path, key]);
  return { data: result.key === key ? result.data : [], error: result.key === key ? result.error : null, loading: result.key !== key };
}

export function Details({ row }: { row: RecordData }) {
  return <dl className="details">{Object.entries(row).map(([key, value]) => <div key={key}><dt>{humanize(key)}</dt><dd>{display(value)}</dd></div>)}</dl>;
}

export function RecordTable({ rows, columns, selected, onSelect }: { rows: RecordData[]; columns: string[]; selected?: string; onSelect?: (row: RecordData) => void }) {
  if (!rows.length) return <p className="empty">No records in this view. Try changing the filter or campaign scope, or create a record where available.</p>;
  return <div className="table-scroll"><table><thead><tr>{columns.map((column) => <th key={column} scope="col">{humanize(column)}</th>)}{onSelect && <th scope="col">Details</th>}</tr></thead><tbody>{rows.map((row) => <tr key={String(row.id)} className={selected === String(row.id) ? "selected" : ""}>{columns.map((column) => <td key={column}>{column === "status" || column.endsWith("status") ? <span className="badge">{display(row[column])}</span> : <span className="cell-content">{display(row[column])}</span>}</td>)}{onSelect && <td><button className="secondary" onClick={() => onSelect(row)} aria-label={`Open ${display(row.name ?? row.full_name ?? row.title ?? row.id)}`}>Open</button></td>}</tr>)}</tbody></table></div>;
}

export function MutationForm({ title, fields, initial = {}, lookups, submitLabel = "Save", confirm, onSubmit, onCancel }: {
  title: string; fields: Field[]; initial?: Record<string, unknown>; lookups: Record<string, Option[]>;
  submitLabel?: string; confirm?: string; onSubmit: (body: Record<string, unknown>) => Promise<unknown>; onCancel?: () => void;
}) {
  const prefix = useId();
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(fields.map((field) => {
    const value = initial[field.name];
    if (field.type === "datetime-local" && value) {
      const date = new Date(String(value));
      if (!Number.isNaN(date.valueOf())) return [field.name, new Date(date.valueOf() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)];
    }
    return [field.name, value == null ? (field.type === "json" ? "{}" : "") : field.type === "json" ? JSON.stringify(value, null, 2) : field.type === "list" && Array.isArray(value) ? value.join(", ") : String(value)];
  })));
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [done, setDone] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null); setDone(false);
    try {
      const body: Record<string, unknown> = {};
      for (const field of fields) {
        if (field.visibleWhen && !field.visibleWhen(values)) continue;
        const value = values[field.name]?.trim() ?? "";
        if ((field.required || field.requiredWhen?.(values)) && !value) throw new Error(`${field.label} is required.`);
        if (!value && field.nullable) body[field.name] = null;
        else if (field.type === "json") {
          const parsed: unknown = JSON.parse(value || "{}");
          if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error(`${field.label} must be a JSON object.`);
          body[field.name] = parsed;
        } else if (field.type === "list") {
          const items = value ? value.split(",").map((item) => item.trim()).filter(Boolean) : [];
          if (items.length > 10 || items.some((item) => item.length > 100) || new Set(items).size !== items.length) throw new Error(`${field.label}: use at most ten unique values, each at most 100 characters.`);
          body[field.name] = items;
        } else if (field.type === "number") {
          if (value) {
            const number = Number(value);
            if (!Number.isFinite(number) || (field.min !== undefined && number < field.min) || (field.max !== undefined && number > field.max)) throw new Error(`${field.label} is outside the allowed range.`);
            if (field.name === "priority" && !Number.isInteger(number)) throw new Error("Priority must be a whole number from 1 to 5.");
            body[field.name] = number;
          }
        }
        else if (field.name === "assigned_to" || field.name === "candidate_id") { if (value) body[field.name] = Number(value); }
        else if (field.type === "datetime-local") { if (value) { const date = new Date(value); if (Number.isNaN(date.valueOf()) || (field.future && date.valueOf() <= Date.now())) throw new Error(`${field.label} must be a future date and time.`); body[field.name] = date.toISOString(); } }
        else body[field.name] = value;
      }
      if (typeof body.expected_ctc_min === "number" && typeof body.expected_ctc_max === "number" && body.expected_ctc_min > body.expected_ctc_max) throw new Error("Minimum expected compensation cannot exceed the maximum.");
      if (confirm && !window.confirm(confirm)) return;
      setPending(true);
      await onSubmit(body);
      setDone(true);
    } catch (e) { setError(e); } finally { setPending(false); }
  }
  return <form className="mutation-form" aria-label={title} onSubmit={submit}><h3>{title}</h3><fieldset disabled={pending}><div className="form-grid">{fields.map((field) => {
    if (field.visibleWhen && !field.visibleWhen(values)) return null;
    const id = `${prefix}-${field.name}`;
    const fieldError = error instanceof ApiError ? error.details?.[field.name] : null;
    const options = field.lookup ? lookups[field.lookup] ?? [] : (field.options ?? []).map((option) => ({ value: option, label: humanize(option) }));
    const descriptions = [field.help ? `${id}-help` : "", fieldError ? `${id}-error` : ""].filter(Boolean).join(" ");
    const props = { id, name: field.name, value: values[field.name] ?? "", required: Boolean(field.required || field.requiredWhen?.(values)), onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setValues((current) => ({ ...current, [field.name]: event.target.value })), "aria-invalid": Boolean(fieldError), "aria-describedby": descriptions || undefined };
    return <div className={field.type === "textarea" || field.type === "json" ? "field wide" : "field"} key={field.name}><label htmlFor={id}>{field.label}{props.required ? " *" : ""}</label>{field.type === "select" || field.lookup ? <select {...props}><option value="">{field.nullable ? "Unassigned / none" : "Select…"}</option>{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : field.type === "textarea" || field.type === "json" ? <textarea {...props} rows={field.type === "json" ? 5 : 3} spellCheck={field.type !== "json"} /> : <input {...props} type={field.type === "list" ? "text" : field.type ?? "text"} min={field.min} max={field.max} step={field.type === "number" ? (field.name === "priority" ? "1" : "any") : undefined} />}{field.help && <small id={`${id}-help`}>{field.help}</small>}{fieldError && <small className="field-error" id={`${id}-error`}>{display(fieldError)}</small>}</div>;
  })}</div><ErrorMessage error={error} />{done && <p role="status" className="success">Saved. The server has accepted this change.</p>}<div className="button-row"><button type="submit">{pending ? "Saving…" : submitLabel}</button>{onCancel && <button type="button" className="secondary" onClick={onCancel}>Close</button>}</div></fieldset></form>;
}
