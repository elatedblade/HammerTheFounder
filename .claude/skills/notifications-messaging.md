---
name: notifications-messaging
description: Design notification systems for email, push, in-app, and SMS channels.
---

# Notifications & Messaging

Act as a messaging architect. Design the notification system for [PRODUCT].
Channels: [email, push, in-app, SMS, Slack/webhook — specify].
Deliver:
1. Notification taxonomy — which events trigger which notification types.
2. Per-channel architecture:
   - Email: transactional provider (SendGrid/SES/Resend), templates, DKIM/SPF.
   - Push: FCM/APNs setup, service worker, permission flow.
   - In-app: real-time delivery (WebSocket/SSE), notification center UI.
   - SMS: provider, opt-in compliance, rate limits.
3. User preference management — per-channel opt-in/out, frequency controls.
4. Template system — reusable templates with variable substitution.
5. Delivery pipeline: event → queue → processor → provider → delivery tracking.
6. Retry and failure handling per channel.
7. Notification grouping/batching (digest mode).
8. Read/unread tracking and badge counts.
9. Unsubscribe flow — one-click unsubscribe (CAN-SPAM compliance).
10. Testing: preview mode, test delivery, staging environment isolation.
Never send a notification without the user's consent. Every notification
must be unsubscribable (except critical security alerts).
