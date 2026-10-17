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
  ["Tell us what you want", "Share your experience, target role, preferred location, salary range, and the kind of company you want next."],
  ["We find relevant jobs", "We search for roles that match your brief instead of sending you a long list of jobs to sort through yourself."],
  ["Humans apply carefully", "We review the role, tailor your application, and submit it with context. We do not spray the same application everywhere."],
  ["We follow up with companies", "We track what happens after an application and follow up where it makes sense."],
  ["Check replies on your dashboard", "Your dashboard shows what we found, what was applied to, and whether a company has replied."],
  ["We keep the search moving", "We review results, adjust the search when needed, and bring you the next useful update."],
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
  const whatsappMessage = "hey , i need proof, are you legit??";
  const whatsappHref = `https://wa.me/919311631709?text=${encodeURIComponent(whatsappMessage)}`;

  return (
    <div className={styles.pageShell}>
      <MarketingNav />
      <main>
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.heroInner}>
            <div className={styles.heroCopy}>
              <h1 id="hero-title">{MARKETING_COPY.title}</h1>
              <p className={styles.heroIntro}>{MARKETING_COPY.eyebrow}</p>
              <div className={styles.heroActions}>
                <Link className={styles.primaryButton} href="#plans">See the plans <span aria-hidden="true">↗</span></Link>
                <Link className={styles.textButton} href="#process">See what happens <span aria-hidden="true">↓</span></Link>
              </div>
            </div>

            <div className={styles.heroStage}>
              <div className={styles.stageRing} aria-hidden="true" />
              <span className={`${styles.orbitDot} ${styles.orbitDotOne}`} aria-hidden="true" />
              <span className={`${styles.orbitDot} ${styles.orbitDotTwo}`} aria-hidden="true" />
              <span className={`${styles.orbitDot} ${styles.orbitDotThree}`} aria-hidden="true" />
              <div className={styles.signalCore} aria-hidden="true">
                <strong>SEARCH<br />IN MOTION</strong>
              </div>
              <div className={`${styles.orbitCard} ${styles.orbitTarget}`} aria-hidden="true">
                <strong>Good match</strong>
                <small>3 roles ready to review</small>
              </div>
              <div className={`${styles.orbitCard} ${styles.orbitSent}`} aria-hidden="true">
                <strong>We’re applying</strong>
                <small>Tailored by a human</small>
              </div>
              <div className={`${styles.orbitCard} ${styles.orbitFollow}`} aria-hidden="true">
                <strong>Reply checked</strong>
                <small>Next update is queued</small>
              </div>
              <div className={styles.orbitNote} aria-hidden="true">Your attention is better spent somewhere else.</div>
              <div className={styles.guaranteeStamp} aria-hidden="true">
                <span>GET</span>
                <strong>GUARANTEED<br />CONVERSION</strong>
                <small>IN A WEEK</small>
              </div>
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
            <div className={styles.processIntro}><h2 id="process-title">Your search, handled by humans.</h2><p>We are not a recruitment agency. We work directly on your job search: finding roles, applying carefully, following up, and showing you what happened.</p></div>
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

        <section className={styles.finalCta} aria-labelledby="final-title"><h2 id="final-title">Go study. We’ll apply for you.</h2><p>Bring us your direction. We will bring the research, applications, outreach, monitoring, and updates.</p><Link className={styles.primaryButton} href="#plans">Find your plan <span aria-hidden="true">↑</span></Link></section>
      </main>
      <footer className={styles.footer}><Link className={styles.wordmark} href="/"><span className={styles.wordmarkMark}>HTF</span><span>Hammer The Founder</span></Link><p>Your direction stays yours. We handle the follow-through.</p><nav aria-label="Footer navigation"><a href="#plans">Plans</a><a href="#process">Process</a><a href="#faq">FAQ</a><Link href="/profile">Profile</Link><Link href="/dashboard">Dashboard</Link></nav><small>© 2026 Hammer The Founder. Outcomes remain with employers.</small></footer>
      <a className={styles.whatsappButton} href={whatsappHref} target="_blank" rel="noreferrer" aria-label="Message Hammer The Founder on WhatsApp">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.52 3.48A11.86 11.86 0 0 0 12.08 0C5.53 0 .2 5.33.2 11.88c0 2.1.55 4.15 1.6 5.96L.1 24l6.3-1.65a11.86 11.86 0 0 0 5.68 1.44h.01c6.55 0 11.88-5.33 11.88-11.88 0-3.18-1.24-6.17-3.45-8.43Zm-8.44 18.3h-.01a9.88 9.88 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65-.23-.37a9.88 9.88 0 0 1-1.51-5.27C2.2 6.43 6.63 2 12.08 2c2.64 0 5.12 1.03 6.98 2.9a9.82 9.82 0 0 1 2.9 6.99c0 5.45-4.43 9.89-9.88 9.89Zm5.42-7.4c-.3-.15-1.78-.88-2.05-.98-.27-.1-.47-.15-.67.15-.2.3-.77.98-.94 1.18-.17.2-.35.23-.65.08-.3-.15-1.25-.46-2.38-1.47-.88-.79-1.47-1.76-1.64-2.06-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.03-.52-.08-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.08-.79.37-.27.3-1.04 1.02-1.04 2.5s1.07 2.9 1.22 3.1c.15.2 2.1 3.2 5.1 4.49.71.3 1.27.49 1.7.63.72.23 1.37.2 1.89.12.58-.09 1.78-.73 2.03-1.43.25-.7.25-1.3.17-1.43-.07-.13-.27-.2-.56-.35Z" /></svg>
        <span>Chat with HTF</span>
      </a>
    </div>
  );
}
