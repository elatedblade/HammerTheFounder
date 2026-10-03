export const LOOKUP_PAGE_SIZE = 50;
export function lookupPath(path: string, query: string, page: number) {
  return `${path}?q=${encodeURIComponent(query)}&limit=${LOOKUP_PAGE_SIZE}&offset=${page * LOOKUP_PAGE_SIZE}`;
}
export function applicationPayload(values: { campaign: string; job: string; notes: string; source_reference: string }) {
  if (!values.campaign || !values.job) throw new Error("Choose a real job and an authorized campaign first.");
  return { ...values };
}
export function jobPayload(values: { company: string; title: string; location: string; canonical_url: string }) {
  if (!values.company || !values.title.trim()) throw new Error("Choose a company and enter a job title.");
  return { ...values, title: values.title.trim(), status: "OPEN" };
}
