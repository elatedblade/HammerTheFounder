export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-zinc-100">
      <section className="w-full max-w-2xl rounded-3xl border border-zinc-800 bg-zinc-900/80 p-10 shadow-2xl shadow-zinc-950/50">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
          Hammer The Founder
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Admin workspace
        </h1>
        <p className="mt-5 max-w-xl text-lg leading-8 text-zinc-300">
          The admin web foundation is ready for local development.
        </p>
      </section>
    </main>
  );
}
