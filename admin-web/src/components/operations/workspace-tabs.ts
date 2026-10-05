export const workspaceTabs = ["Overview", "Candidates", "Campaigns", "Applications", "Payments", "Inquiries", "Notifications", "Outreach"] as const;

export type WorkspaceTab = typeof workspaceTabs[number];

/** Campaign selection is an Overview concern; operational records stay unscoped by this UI. */
export function campaignScopeForTab(tab: WorkspaceTab, campaign: string): string {
  return tab === "Overview" ? campaign : "";
}
