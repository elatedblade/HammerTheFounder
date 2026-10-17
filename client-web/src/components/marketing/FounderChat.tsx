import { Fragment, type CSSProperties } from "react";
import styles from "./marketing.module.css";

const messages = [
  {
    sender: "founder",
    label: "Hammer The Founder",
    text: "gm ☀️ applied to 15+ jobs that actually fit you",
    time: "10:42 AM",
  },
  {
    sender: "founder",
    label: "Hammer The Founder",
    text: "We also cold mailed 10+ startups. One replied — screening call scheduled.",
    time: "10:43 AM",
  },
  {
    sender: "customer",
    label: "You",
    text: "yeah, I’m checking the dashboard now. thank you 🙌",
    time: "10:44 AM",
  },
  {
    sender: "founder",
    label: "Hammer The Founder",
    text: "Say less. We’ll keep the search moving.",
    time: "10:45 AM",
  },
] as const;

export default function FounderChat() {
  return (
    <section className={styles.founderChat} aria-labelledby="founder-chat-title">
      <div className={styles.phoneSpeaker} aria-hidden="true" />
      <div className={styles.chatStatusBar} aria-hidden="true">
        <strong>9:41</strong>
        <span>▮▮▮ ◒ ▰</span>
      </div>
      <header className={styles.chatHeader}>
        <span className={styles.chatBack} aria-hidden="true">‹</span>
        <span className={styles.chatAvatar} aria-hidden="true">HTF</span>
        <div className={styles.chatIdentity}>
          <h2 id="founder-chat-title">Hammer The Founder</h2>
          <p><span className={styles.chatOnlineDot} aria-hidden="true" />Active now</p>
        </div>
        <span className={styles.chatHeaderGlyph} aria-hidden="true">◉</span>
      </header>
      <p className={styles.chatDate}>Today · 10:45 AM</p>
      <ol className={styles.chatMessages} aria-label="A conversation about today's job search progress">
        {messages.map((message, index) => (
          <Fragment key={`${message.sender}-${message.text}`}>
            <li
              className={`${styles.chatMessage} ${message.sender === "customer" ? styles.chatMessageCustomer : ""}`}
              style={{ "--chat-message-delay": `${0.8 + index * 2.65}s` } as CSSProperties}
            >
              <div className={styles.chatBubble}>
                <span className={styles.chatVisuallyHidden}>{message.label}: </span>
                <p>{message.text}</p>
                <time>{message.time}</time>
              </div>
            </li>
            {message.sender === "customer" && index < messages.length - 1 ? (
              <li
                className={styles.chatTyping}
                aria-label="Hammer The Founder is typing"
                role="status"
                style={{ "--chat-typing-delay": `${2.1 + Math.floor(index / 2) * 5.3}s` } as CSSProperties}
              >
                <span className={styles.chatTypingBubble} aria-hidden="true">
                  <i /><i /><i />
                </span>
              </li>
            ) : null}
          </Fragment>
        ))}
      </ol>

      <footer className={styles.chatFooter}>
        <span className={styles.chatPlus} aria-hidden="true">+</span>
        <span className={styles.chatComposer}>Message</span>
        <span className={styles.chatMic} aria-hidden="true">◦</span>
        <span className={styles.chatDelivered}><span aria-hidden="true">✓</span> Delivered</span>
      </footer>
    </section>
  );
}
