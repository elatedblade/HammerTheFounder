"use client";

import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import { usePathname } from "next/navigation";

export function LoadingSkeleton() {
  return <main className="app-shell" aria-busy="true"><div className="app-topbar"><span className="skeleton skeleton-brand" /><span className="skeleton skeleton-avatar" /></div><div className="content-wrap"><span className="skeleton skeleton-kicker" /><span className="skeleton skeleton-title" /><span className="skeleton skeleton-copy" /><div className="workspace-grid skeleton-layout"><section className="panel skeleton-panel"><span className="skeleton skeleton-section" /><span className="skeleton skeleton-field" /><span className="skeleton skeleton-field" /></section><aside className="panel skeleton-panel" /></div></div></main>;
}

export function AppHeader() {
  const pathname = usePathname();
  return <header className="app-topbar"><Link className="brand" href="/" aria-label="Hammer The Founder home"><span className="brand-mark">H</span><span className="brand-name">Hammer The Founder</span></Link><nav className="signed-in-nav" aria-label="Customer navigation">{[["/", "Home"], ["/profile", "Profile"], ["/dashboard", "Dashboard"]].map(([href,label]) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}>{label}</Link>)}</nav><div className="topbar-right"><UserButton /></div></header>;
}

export function SetupState() {
  return <main className="state-page"><div className="state-topbar"><Link className="brand" href="/"><span className="brand-mark">H</span><span>Hammer The Founder</span></Link></div><section className="state-card"><span className="eyebrow">Authentication setup</span><h1>Connect Clerk to open your workspace</h1><p>Configure Clerk for this client, then restart the client service.</p></section></main>;
}

export function SignedOutState({ redirect = "/dashboard" }: { redirect?: string }) {
  return <main className="state-page"><div className="state-topbar"><Link className="brand" href="/"><span className="brand-mark">H</span><span>Hammer The Founder</span></Link></div><section className="state-card"><span className="eyebrow">Hammer The Founder</span><h1>Sign in to continue</h1><p>Your customer workspace is private. Sign in or create an account to continue.</p><div className="auth-actions"><Link className="button button-primary" href={`/sign-in?redirect_url=${encodeURIComponent(redirect)}`}>Sign in</Link><Link className="button button-secondary" href={`/sign-up?redirect_url=${encodeURIComponent(redirect)}`}>Create account</Link></div></section></main>;
}

export function AccessDeniedState({ adminUrl }: { adminUrl: string }) {
  return <main className="state-page"><div className="state-topbar"><Link className="brand" href="/"><span className="brand-mark">H</span><span>Hammer The Founder</span></Link></div><section className="state-card"><span className="eyebrow">Operations workspace</span><h1>Open the admin workspace</h1><p>This customer page is limited to client accounts.</p><a className="button button-primary" href={adminUrl}>Open admin workspace</a></section></main>;
}
