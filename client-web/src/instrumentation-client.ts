import * as Sentry from "@sentry/react";

// Opt-in runtime error reporting. No replay, input values, user identity or URLs.
if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    defaultIntegrations: false,
    tracesSampleRate: 0,
    integrations: [],
    beforeSend(event) {
      delete event.request;
      delete event.user;
      delete event.breadcrumbs;
      delete event.extra;
      delete event.message;
      for (const exception of event.exception?.values ?? []) {
        exception.value = "Runtime exception details withheld.";
      }
      return event;
    },
  });
  window.addEventListener("error", (event) => Sentry.captureException(event.error));
  window.addEventListener("unhandledrejection", (event) => Sentry.captureException(event.reason));
}
