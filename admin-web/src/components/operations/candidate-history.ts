export function candidateOutreachPath(id: string, page: number): string {
  return `outreach/?candidate=${encodeURIComponent(id)}&limit=50&offset=${page * 50}`;
}
