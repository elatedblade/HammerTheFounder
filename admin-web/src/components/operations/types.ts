import type { ApiClient, CurrentUser } from "../../lib/api";

export type RecordData = { id: string | number; [key: string]: unknown };
export type Option = { value: string; label: string };
export type Field = {
  name: string; label: string; type?: "text" | "email" | "url" | "number" | "date" | "datetime-local" | "textarea" | "json" | "list" | "select" | "checkbox";
  required?: boolean; options?: (string | Option)[]; lookup?: string; nullable?: boolean; min?: number; max?: number; help?: string;
  visibleWhen?: (values: Record<string, string>) => boolean;
  requiredWhen?: (values: Record<string, string>) => boolean;
  future?: boolean;
};
export type Action = {
  label: string; route: string; fields?: Field[] | ((row: RecordData) => Field[]); body?: Record<string, unknown>; method?: "POST" | "PATCH";
  confirm?: string; admin?: boolean; when?: (row: RecordData) => boolean;
  initial?: (row: RecordData) => Record<string, unknown>;
};
export type Resource = {
  title: string; path: string; columns: string[]; fields?: Field[]; editFields?: Field[] | ((row: RecordData) => Field[]); actions?: Action[];
  scoped?: boolean; description?: string; adminEdit?: boolean; fetchDetail?: boolean; createConfirm?: string; paginated?: boolean;
  statusOptions?: string[]; stageOptions?: Option[]; pageSize?: number;
};
export type WorkspaceContext = {
  api: ApiClient; user: CurrentUser; campaign: string; revision: number; refresh: () => void;
  lookups: Record<string, Option[]>;
};
export function display(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.map(display).join(", ");
  if (typeof value === "object") return "Available";
  return String(value);
}
export function humanize(name: string): string { return name.replaceAll("_", " ").replace(/^./, (s) => s.toUpperCase()); }
export function isAdmin(user: CurrentUser) { return user.role === "ADMIN" || user.role === "SUPERADMIN"; }
