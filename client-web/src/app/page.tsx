export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-100">
      <section className="w-full max-w-2xl rounded-3xl border border-slate-800 bg-slate-900/80 p-10 shadow-2xl shadow-slate-950/50">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-cyan-300">
          Hammer The Founder
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Client workspace
        </h1>
        <p className="mt-5 max-w-xl text-lg leading-8 text-slate-300">
          The client web foundation is ready for local development.
        </p>
      </section>
    </main>
  );
}
