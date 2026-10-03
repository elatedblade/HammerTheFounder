"use client";

import { captureException } from "@sentry/react";
import { useEffect } from "react";

export default function WorkspaceError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { if (process.env.NEXT_PUBLIC_SENTRY_DSN) captureException(error); }, [error]);
  return <main className="state-page"><section className="state-card" role="alert"><h1>The workspace could not render.</h1><p>Your saved records remain on the server. Retry loading; do not repeat an uncertain payment or upload without checking its status.</p><button type="button" className="button button-primary" onClick={reset}>Reload workspace</button></section></main>;
}
