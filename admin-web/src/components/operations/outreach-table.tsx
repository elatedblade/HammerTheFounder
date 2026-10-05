import { outreachStatusLabel } from "./outreach-status";
import type { RecordData } from "./types";
import { RecordTable } from "./ui";

export default function OutreachTable({ rows, columns, selected, onSelect }: { rows: RecordData[]; columns: string[]; selected?: string; onSelect: (row: RecordData) => void }) {
  return <RecordTable rows={rows.map((row) => ({ ...row, status: outreachStatusLabel(row.status) }))} columns={columns} selected={selected} onSelect={(displayed) => {
    const original = rows.find((row) => String(row.id) === String(displayed.id));
    if (original) onSelect(original);
  }} />;
}
