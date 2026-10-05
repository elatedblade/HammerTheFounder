"use client";

import { useEffect, useState } from "react";

export type RequestState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
};

export function useRequest<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  enabled = true,
): RequestState<T> {
  const [state, setState] = useState<Omit<RequestState<T>, "retry">>({
    data: null,
    loading: enabled,
    error: null,
  });
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({ data: null, loading: enabled, error: null });
    if (enabled) {
      void loader(controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) setState({ data, loading: false, error: null });
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            setState({
              data: null,
              loading: false,
              error: error instanceof Error ? error.message : "This information is unavailable.",
            });
          }
        });
    }
    return () => controller.abort();
  }, [enabled, loader, revision]);

  return { ...state, retry: () => setRevision((value) => value + 1) };
}
