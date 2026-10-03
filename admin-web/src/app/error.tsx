"use client";

import { captureException } from "@sentry/react";
import { useEffect } from "react";

export default function WorkspaceError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { if (process.env.NEXT_PUBLIC_SENTRY_DSN) captureException(error); }, [error]);
  return <main className="min-h-screen bg-zinc-950 p-10 text-zinc-100"><section role="alert"><h1 className="text-2xl font-semibold">The workspace could not render.</h1><p className="my-4">Reload the saved records before retrying an uncertain action. No action is automatically repeated.</p><button type="button" className="rounded bg-amber-300 px-4 py-2 text-zinc-950" onClick={reset}>Reload workspace</button></section></main>;
}
