import { applicationColumns, applicationSubmittedDate } from "./application-helpers";
import { applicationStageLabel } from "./application-stages";
import { display, humanize, type RecordData } from "./types";

export default function ApplicationTable({ rows, selected, onSelect }: { rows: RecordData[]; selected?: string; onSelect: (row: RecordData) => void }) {
  return <>
    <p className="muted" role="status">{rows.length} matching application{rows.length === 1 ? "" : "s"} on this page · current filters only. Submission dates are UTC; exact timestamps and references are in details.</p>
    {!rows.length ? <p className="empty">No applications on this page match the selected campaign, status and search.</p> : <div className="table-scroll"><table><thead><tr>{applicationColumns.map((column) => <th key={column} scope="col">{column === "status" ? "Current stage" : column === "submitted_at" ? "Submitted date (UTC)" : humanize(column)}</th>)}<th scope="col">Details</th></tr></thead><tbody>{rows.map((row) => <tr key={String(row.id)} className={selected === String(row.id) ? "selected" : ""}>{applicationColumns.map((column) => <td key={column}>{column === "status" ? <span className="badge">{applicationStageLabel(row)}</span> : column === "submitted_at" ? row.submitted_at ? <time dateTime={String(row.submitted_at)} title={String(row.submitted_at)}>{applicationSubmittedDate(row.submitted_at)}</time> : "Not recorded" : <span className="cell-content">{display(row[column])}</span>}</td>)}<td><button className="secondary" onClick={() => onSelect(row)} aria-label={`Open application for ${display(row.candidate_name)} at ${display(row.company_name)}: ${display(row.job_title)}`}>Open</button></td></tr>)}</tbody></table></div>}
  </>;
}
