import Link from "next/link";
import { MARKETING_COPY, SERVICE_PLANS } from "../../lib/marketing";
import MarketingNav from "./MarketingNav";
import styles from "./marketing.module.css";

const fit = [
  ["You are already good at your work", "Your search deserves the same care as your craft—not a second full-time job."],
  ["You want a sharper target", "Bring a role, industry, location, or next chapter. We turn your direction into a workable search brief."],
  ["You value a human signal", "HTF is manual-first. People review the work, record what happened, and surface the next useful action."],
];

export default function MarketingPage() {
  return (
    <div className={styles.pageShell}>
      <MarketingNav />
      <main>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <p className={styles.kicker}><span className={styles.kickerDot} />{MARKETING_COPY.eyebrow}</p>
            <h1>{MARKETING_COPY.title}</h1>
            <p className={styles.heroIntro}>{MARKETING_COPY.intro}</p>
            <div className={styles.heroActions}>
              <Link className={styles.primaryButton} href="#plans">Choose your approach <span aria-hidden="true">↗</span></Link>
              <Link className={styles.textButton} href="#process">See the process <span aria-hidden="true">↓</span></Link>
            </div>
            <p className={styles.microcopy}>No automated submissions. No hidden promises. Just a managed search with a visible trail.</p>
          </div>
          <div className={styles.heroCard} aria-label="What HTF coordinates">
            <div className={styles.cardLabel}>The search, in one view</div>
            <div className={styles.signalRow}><span className={styles.signalIcon}>01</span><div><strong>Applications</strong><span>Relevant roles, reviewed by people</span></div></div>
            <div className={styles.signalRow}><span className={styles.signalIcon}>02</span><div><strong>Founder outreach</strong><span>A considered path beyond job boards</span></div></div>
            <div className={styles.signalRow}><span className={styles.signalIcon}>03</span><div><strong>Progress</strong><span>A dashboard that tells you what is next</span></div></div>
            <div className={styles.cardNote}>Your profile sets the direction. Our team coordinates the work.</div>
          </div>
        </section>

        <section className={styles.statement}>
          <p className={styles.sectionLabel}>Why HTF</p>
          <h2>A job search should feel like a considered campaign, not a pile of tabs.</h2>
          <p>HTF combines thoughtful targeting, hands-on execution, and straightforward updates. You bring the context; we help turn it into consistent momentum.</p>
        </section>

        <section className={styles.fitSection}>
          <div className={styles.sectionHeading}><p className={styles.sectionLabel}>A good fit if</p><h2>You want support without handing over your voice.</h2></div>
          <div className={styles.fitGrid}>{fit.map(([title, body]) => <article className={styles.fitCard} key={title}><span className={styles.cardIndex}>/</span><h3>{title}</h3><p>{body}</p></article>)}</div>
        </section>

        <section className={styles.plansSection} id="plans">
          <div className={styles.sectionHeading}><p className={styles.sectionLabel}>Choose your approach</p><h2>Three ways to put your search in motion.</h2><p>Start with the kind of support you need. We will discuss fit and next steps before any campaign is activated.</p></div>
          <div className={styles.planGrid}>{SERVICE_PLANS.map((plan, index) => <article className={`${styles.planCard} ${index === 1 ? styles.planFeatured : ""}`} key={plan.id}>
            {index === 1 && <span className={styles.planTag}>Founder &amp; CXO outreach</span>}
            <div className={styles.planNumber}>0{index + 1}</div><h3>{plan.name}</h3><p className={styles.planSummary}>{plan.summary}</p>
            <ul>{plan.features.map((feature) => <li key={feature}><span aria-hidden="true">✓</span>{feature}</li>)}</ul>
             <Link className={index === 1 ? styles.primaryButton : styles.secondaryButton} href={`/plans?plan=${plan.id}`}>Choose {plan.name} <span aria-hidden="true">↗</span></Link>
          </article>)}</div>
          <p className={styles.planFootnote}>Plan details and any commercial terms are discussed directly with HTF. Selecting a plan does not start a campaign.</p>
        </section>

        <section className={styles.processSection} id="process">
          <div className={styles.sectionHeading}><p className={styles.sectionLabel}>How it works</p><h2>Clear handoffs. Human decisions.</h2></div>
          <ol className={styles.processList}><li><span>01</span><div><h3>Choose a starting point</h3><p>Select the approach that matches your search. Sign in or create an account so we can save your intent.</p></div></li><li><span>02</span><div><h3>Talk to HTF on WhatsApp</h3><p>Continue to our business WhatsApp with your chosen plan and inquiry reference. Discuss fit, scope and pricing directly with us.</p></div></li><li><span>03</span><div><h3>Get your profile ready</h3><p>Save your background, preferences and resume on your profile page. HTF reviews the details and starts your campaign after confirmation.</p></div></li><li><span>04</span><div><h3>Follow the progress</h3><p>See applications, outreach and interview updates on your dashboard while our team handles the agreed search work.</p></div></li></ol>
        </section>

        <section className={styles.boundarySection}><div><p className={styles.sectionLabel}>A useful boundary</p><h2>We run the search. Employers make the decision.</h2></div><p>{MARKETING_COPY.limitations} HTF is manual-first: operators submit applications and send outreach themselves. We do not store third-party passwords or pretend that activity equals an outcome.</p></section>

        <section className={styles.faqSection} id="faq"><div className={styles.sectionHeading}><p className={styles.sectionLabel}>Questions, answered</p><h2>Before you begin.</h2></div><div className={styles.faqList}><details><summary>Does choosing a plan activate a campaign?</summary><p>No. Your selection is saved as an inquiry after you sign in. You discuss fit with HTF; an admin explicitly converts and starts a campaign later.</p></details><details><summary>Will HTF apply everywhere automatically?</summary><p>No. The service is human-operated. Operators review the search and manually submit applications or send outreach according to the agreed direction.</p></details><details><summary>Do I need a finished profile to ask about a plan?</summary><p>No. You can select a plan and start the conversation first. A profile is needed for campaign readiness, not for an inquiry.</p></details><details><summary>What happens when I click Continue to WhatsApp?</summary><p>After you confirm in your account, HTF opens its configured WhatsApp Business conversation with a plan and inquiry reference. It is not proof that a message was sent, payment was made, or work has started.</p></details></div></section>

        <section className={styles.finalCta}><p className={styles.sectionLabel}>Ready when you are</p><h2>Bring your next move into focus.</h2><p>Choose the level of support that feels right, then take the first conversation at your pace.</p><Link className={styles.primaryButton} href="#plans">Explore the plans <span aria-hidden="true">↗</span></Link></section>
      </main>
      <footer className={styles.footer}><Link className={styles.wordmark} href="/"><span className={styles.wordmarkMark}>HTF</span><span>Hammer The Founder</span></Link><p>Human-operated job search support for ambitious professionals.</p><nav aria-label="Footer navigation"><a href="#plans">Plans</a><a href="#process">Process</a><a href="#faq">FAQ</a><Link href="/profile">Profile</Link><Link href="/dashboard">Dashboard</Link></nav><small>© {new Date().getFullYear()} Hammer The Founder. Outcomes remain with employers.</small></footer>
    </div>
  );
}
