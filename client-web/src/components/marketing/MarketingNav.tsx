"use client";

import Link from "next/link";
import { SignInButton, Show, UserButton } from "@clerk/nextjs";
import { clerkConfigured } from "../../app/auth-provider";
import styles from "./marketing.module.css";

export default function MarketingNav() {
  const account = clerkConfigured ? (
    <>
      <Show when="signed-out">
        <SignInButton mode="modal">
          <button className={styles.navSignIn} type="button">Sign in</button>
        </SignInButton>
        <Link className={styles.navAccount} href="/sign-up">Create account</Link>
      </Show>
      <Show when="signed-in">
        <Link className={styles.navAccount} href="/dashboard">Open dashboard</Link>
        <UserButton />
      </Show>
    </>
  ) : (
    <><Link className={styles.navSignIn} href="/sign-in">Sign in</Link><Link className={styles.navAccount} href="/sign-up">Create account</Link></>
  );

  return (
    <header className={styles.siteHeader}>
      <div className={styles.navWrap}>
        <Link className={styles.wordmark} href="/" aria-label="Hammer The Founder home">
          <span className={styles.wordmarkMark}>HTF</span>
          <span>Hammer The Founder</span>
        </Link>
        <details className={styles.mobileMenu}>
          <summary aria-label="Open navigation">Menu</summary>
          <nav className={styles.mobileLinks} aria-label="Mobile navigation">
            <a href="#plans">Plans</a>
            <a href="#process">How it works</a>
            <a href="#faq">FAQ</a>
            {account}
          </nav>
        </details>
        <nav className={styles.desktopLinks} aria-label="Primary navigation">
          <a href="#plans">Plans</a>
          <a href="#process">How it works</a>
          <a href="#faq">FAQ</a>
          {account}
        </nav>
      </div>
    </header>
  );
}
