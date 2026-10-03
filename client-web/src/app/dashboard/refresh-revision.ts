/** Return the next immutable refresh generation for independently loaded resources. */
export function bumpRefreshRevision(revision: number): number {
  return revision + 1;
}
