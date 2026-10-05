"use client";
import Link from "next/link";
export default function PlansError({ reset }: { reset: () => void }) { return <main className="state-page"><section className="state-card" role="alert"><h1>Plans are temporarily unavailable</h1><p>Your profile and dashboard are still available. No campaign has been changed.</p><button className="button button-primary" onClick={reset}>Retry plans</button><div className="auth-actions"><Link href="/dashboard">Dashboard</Link><Link href="/profile">Profile</Link></div></section></main>; }
