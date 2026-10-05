import Link from "next/link";
import { MARKETING_COPY, SERVICE_PLANS } from "../../lib/marketing";
import MarketingNav from "./MarketingNav";
import styles from "./marketing.module.css";

const searchCards = [
  {
    title: "Check the dashboard for updates.",
    body: "See what we found, what we are applying to, what came back, and what needs your decision.",
    className: styles.searchCardDashboard,
  },
  {
    title: "Go upskill.",
    body: "Use the time you would have spent searching to sharpen the skill that moves your next role forward.",
    className: styles.searchCardUpskill,
  },
  {
    title: "Go relax. Take a nap.",
    body: "We keep the search moving, monitor replies, and bring you the next useful update.",
    className: styles.searchCardRelax,
  },
];

const processSteps = [
  ["Align on the brief", "We review your profile, resume, role direction, level, location, industries, preferences, and non-negotiables."],
  ["Find the right targets", "We show you what is worth pursuing instead of dropping a generic stream of job-board links in your lap."],
  ["Tailor and apply", "A human reviews the application and adapts the materials to the opportunity. No copy-paste spray."],
  ["Reach out with intention", "Where the plan includes it, we research founder or CXO contacts and send a considered message."],
  ["Monitor and follow up", "We check updates, log replies, follow up on live conversations, and call for an update when appropriate and agreed."],
  ["Keep you aligned", "Your dashboard shows activity, outcomes, conversations, and next actions. You stay in control of the direction."],
];

const comparisonRows = [
  ["Role selection", "Broad matching and volume", "Human-reviewed targets worth pursuing"],
  ["Application", "Generated and sent at scale", "Tailored by a person for the opportunity"],
  ["Context", "One-size-fits-all prompts", "Your profile, preferences, and non-negotiables"],
  ["Follow-through", "Little ownership after send", "Replies monitored and next actions logged"],
  ["Visibility", "Activity can be hard to read", "A dashboard that shows the work and what needs your call"],
  ["Outcome", "Automation can imply certainty", "Employers decide; HTF owns search quality and visibility"],
];

export default function MarketingPage() {
  return (
    <div className={styles.pageShell}>
      <MarketingNav />
      <main>
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.heroInner}>
            <div className={styles.heroCopy}>
              <h1 id="hero-title">{MARKETING_COPY.title}</h1>
              <div className={styles.heroActions}>
                <Link className={styles.primaryButton} href="#plans">See the plans <span aria-hidden="true">↗</span></Link>
                <Link className={styles.textButton} href="#process">See what happens <span aria-hidden="true">↓</span></Link>
              </div>
            </div>

            <div className={styles.heroStage} role="img" aria-label="A human-led search moving through role fit, applications, and follow-up">
              <div className={styles.stageRing} aria-hidden="true" />
              <span className={`${styles.orbitDot} ${styles.orbitDotOne}`} aria-hidden="true" />
              <span className={`${styles.orbitDot} ${styles.orbitDotTwo}`} aria-hidden="true" />
              <span className={`${styles.orbitDot} ${styles.orbitDotThree}`} aria-hidden="true" />
              <div className={styles.signalCore} aria-hidden="true">
                <strong>SEARCH<br />IN MOTION</strong>
              </div>
              <div className={`${styles.orbitCard} ${styles.orbitTarget}`}>
                <strong>Good match</strong>
                <small>3 roles ready to review</small>
              </div>
              <div className={`${styles.orbitCard} ${styles.orbitSent}`}>
                <strong>We’re applying</strong>
                <small>Tailored by a human</small>
              </div>
              <div className={`${styles.orbitCard} ${styles.orbitFollow}`}>
                <strong>Reply checked</strong>
                <small>Next update is queued</small>
              </div>
              <div className={styles.orbitNote}>Your attention is better spent somewhere else.</div>
            </div>
          </div>
          <a className={styles.scrollCue} href="#search" aria-label="Scroll into the work"><span aria-hidden="true">↓</span></a>
        </section>

        <div className={styles.ticker} aria-label="HTF activity ticker">
          <div className={styles.tickerTrack}>
            {["Check the dashboard", "Go upskill", "Go relax", "Take a nap", "We’re on it", "Check the dashboard", "Go upskill", "Go relax", "Take a nap", "We’re on it"].map((item, index) => <span className={styles.tickerItem} key={`${item}-${index}`}>{item}</span>)}
          </div>
        </div>

        <section className={styles.searchSection} id="search" aria-labelledby="search-title">
          <div className={styles.searchIntro}>
            <div>
              <h2 id="search-title">{MARKETING_COPY.intro}</h2>
              <Link className={styles.primaryButton} href="#plans">See the plans <span aria-hidden="true">↗</span></Link>
            </div>
          </div>
          <div className={styles.searchCards}>
            {searchCards.map((card) => <Link className={`${styles.searchCard} ${card.className}`} href="/dashboard" key={card.title}>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
              <span className={styles.cardArrow} aria-hidden="true">↗</span>
            </Link>)}
          </div>
        </section>

        <section className={styles.processSection} id="process" aria-labelledby="process-title">
          <div className={styles.processLayout}>
            <div className={styles.processIntro}><h2 id="process-title">Quiet for you. Active for us.</h2><p>We treat your application like our own: specific, reviewed, tracked, and followed through.</p></div>
            <ol className={styles.processList}>{processSteps.map(([title, body]) => <li key={title}><div><h3>{title}</h3><p>{body}</p></div><span className={styles.stepMark} aria-hidden="true">↗</span></li>)}</ol>
          </div>
        </section>

        <section className={styles.plansSection} id="plans" aria-labelledby="plans-title">
          <div className={styles.sectionHeading}><h2 id="plans-title">More coverage. More follow-through.</h2></div>
          <div className={styles.planGrid}>{SERVICE_PLANS.map((plan, index) => <article className={`${styles.planCard} ${index === 1 ? styles.planFeatured : ""}`} key={plan.id}>
           <h3>{plan.name}</h3>
            <ul className={styles.planDailyCounts}>
              <li><strong>{plan.applicationsPerDay}</strong> applications per day</li>
              <li><strong>{plan.coldMailsPerDay}</strong> cold mails per day</li>
            </ul>
            <p className={styles.planPrice}><strong>₹{plan.pricePerWeek}</strong> / week</p>
            <p className={styles.planFreeWeek}>1 week free</p>
            <Link className={styles.secondaryButton} href={`/plans?plan=${plan.id}`} aria-label={`Choose ${plan.name}`}>Choose plan <span aria-hidden="true">↗</span></Link>
          </article>)}</div>
          <p className={styles.planFootnote}>Selecting a plan starts an inquiry after sign-in; it does not start or modify a campaign.</p>
        </section>

        <section className={styles.comparisonSection} aria-labelledby="comparison-title">
          <div className={styles.comparisonHead}><h2 id="comparison-title">We are better than AI.</h2></div>
          <div className={styles.comparisonTable} role="table" aria-label="Human-led versus AI autopilot comparison">
            <div className={`${styles.comparisonRow} ${styles.comparisonHeader}`} role="row"><div role="columnheader">The work</div><div role="columnheader">AI autopilot</div><div role="columnheader">HTF human-led</div></div>
            {comparisonRows.map(([topic, ai, htf]) => <div className={styles.comparisonRow} role="row" key={topic}><div role="rowheader">{topic}</div><div role="cell">{ai}</div><div role="cell">{htf}</div></div>)}
          </div>
        </section>

        <section className={styles.faqSection} id="faq" aria-labelledby="faq-title"><div className={styles.sectionHeading}><h2 id="faq-title">Before you begin.</h2></div><div className={styles.faqList}><details><summary>Does choosing a plan activate a campaign?</summary><p>No. Your selection is saved as an inquiry after you sign in. You discuss fit with HTF; an admin explicitly converts and starts a campaign later.</p></details><details><summary>Will HTF apply everywhere automatically?</summary><p>No. The service is human-operated. Operators review the search and manually submit applications or send outreach according to the agreed direction.</p></details><details><summary>Do I need a finished profile to ask about a plan?</summary><p>No. You can select a plan and start the conversation first. A profile is needed for campaign readiness, not for an inquiry.</p></details><details><summary>What happens when I click Continue to WhatsApp?</summary><p>After you confirm in your account, HTF opens its configured WhatsApp Business conversation with a plan and inquiry reference. It is not proof that a message was sent, payment was made, or work has started.</p></details></div></section>

        <section className={styles.finalCta} aria-labelledby="final-title"><h2 id="final-title">Go build, rest, think, or live.</h2><p>Bring us your direction. We will bring the research, applications, outreach, monitoring, and updates.</p><Link className={styles.primaryButton} href="#plans">Find your plan <span aria-hidden="true">↑</span></Link></section>
      </main>
      <footer className={styles.footer}><Link className={styles.wordmark} href="/"><span className={styles.wordmarkMark}>HTF</span><span>Hammer The Founder</span></Link><p>Your direction stays yours. We handle the follow-through.</p><nav aria-label="Footer navigation"><a href="#plans">Plans</a><a href="#process">Process</a><a href="#faq">FAQ</a><Link href="/profile">Profile</Link><Link href="/dashboard">Dashboard</Link></nav><small>© {new Date().getFullYear()} Hammer The Founder. Outcomes remain with employers.</small></footer>
    </div>
  );
}
