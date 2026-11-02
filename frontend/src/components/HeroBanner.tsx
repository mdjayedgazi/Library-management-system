import { Link } from 'react-router'

const HeroBanner = () => {
  return (
    <section className="relative isolate mx-2 my-3 flex min-h-128 items-center overflow-hidden rounded-2xl border border-white/8 bg-[#09090b] px-5 py-16 sm:mx-4 sm:min-h-144 sm:px-8 lg:px-14 lg:mx-10">
      {/* Background image */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            'url(https://images.unsplash.com/photo-1694730750153-8b66cf3dd014?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D)',
        }}
      />

      {/* Dark overlay */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-linear-to-r from-[#09090b]/95 via-[#09090b]/75 to-[#09090b]/30"
      />

      {/* Hero content */}
      <div className="relative z-10 w-full max-w-2xl">
        <span className="inline-flex items-center rounded-full border border-white/15 bg-white/6 px-4 py-2 text-xs font-medium tracking-wider text-zinc-300 uppercase">
          Welcome to Library
        </span>

        <h1 className="mt-7 text-4xl leading-tight font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
          Discover your next
          <span className="block text-zinc-400">great read.</span>
        </h1>

        <p className="mt-6 max-w-lg text-sm leading-7 text-zinc-400 sm:text-base sm:leading-8">
          Explore a world of knowledge, discover timeless stories, and find the books that inspire
          your next chapter.
        </p>

        {/* Actions */}
        <div className="mt-9 flex flex-wrap items-center gap-4">
          <Link
            to="/books"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-sm font-semibold text-zinc-950 transition-colors hover:bg-zinc-200 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
          >
            Explore Books
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="size-4"
              aria-hidden="true"
            >
              <path d="M5 12h14m-6-6 6 6-6 6" />
            </svg>
          </Link>

          <Link
            to="/about"
            className="rounded-lg border border-white/15 bg-white/5 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
          >
            Learn More
          </Link>
        </div>
      </div>
    </section>
  )
}

export default HeroBanner
