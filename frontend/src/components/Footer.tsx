import { Link } from 'react-router'

export default function Footer() {
  return (
    <footer className="border-t p border-white/8 bg-[#09090b] text-zinc-400">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
        {/* Main footer */}
        <div className="grid grid-cols-1 gap-12 py-14 sm:grid-cols-2 lg:grid-cols-[1.5fr_1fr_1fr_1fr] lg:gap-16 lg:py-20">
          {/* Brand section */}
          <div className="max-w-sm">
            <Link to="/" className="group inline-flex items-center gap-3">
              <span className="flex size-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white transition-colors group-hover:bg-white/[0.10]">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  className="size-5"
                  aria-hidden="true"
                >
                  <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
                  <path d="M4 5.5v16M8 7h8M8 11h7" />
                </svg>
              </span>

              <span className="text-lg font-semibold tracking-tight text-white">
                Library<span className="text-zinc-500">.</span>
              </span>
            </Link>

            <p className="mt-5 text-sm leading-7 text-zinc-500">
              A quiet place for curious minds. Discover books, explore new ideas, and find your next
              favorite read.
            </p>

            <Link
              to="/books"
              className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-zinc-300 transition-colors hover:text-white focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
            >
              Explore our collection
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                className="size-4 transition-transform group-hover:translate-x-1"
                aria-hidden="true"
              >
                <path d="M5 12h14m-6-6 6 6-6 6" />
              </svg>
            </Link>
          </div>

          {/* Explore */}
          <nav aria-label="Explore">
            <h2 className="mb-5 text-xs font-semibold tracking-[0.16em] text-white uppercase">
              Explore
            </h2>

            <ul className="space-y-4 text-sm">
              <li>
                <Link to="/books" className="transition-colors hover:text-white">
                  All Books
                </Link>
              </li>
              <li>
                <Link to="/categories" className="transition-colors hover:text-white">
                  Categories
                </Link>
              </li>
              <li>
                <Link to="/about" className="transition-colors hover:text-white">
                  About Us
                </Link>
              </li>
            </ul>
          </nav>

          {/* Resources */}
          <nav aria-label="Resources">
            <h2 className="mb-5 text-xs font-semibold tracking-[0.16em] text-white uppercase">
              Resources
            </h2>

            <ul className="space-y-4 text-sm">
              <li>
                <Link to="/contact" className="transition-colors hover:text-white">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link to="/help" className="transition-colors hover:text-white">
                  Help Center
                </Link>
              </li>
              <li>
                <Link to="/faq" className="transition-colors hover:text-white">
                  FAQs
                </Link>
              </li>
            </ul>
          </nav>

          {/* Account */}
          <nav aria-label="Account">
            <h2 className="mb-5 text-xs font-semibold tracking-[0.16em] text-white uppercase">
              Account
            </h2>

            <ul className="space-y-4 text-sm">
              <li>
                <Link to="/login" className="transition-colors hover:text-white">
                  Sign In
                </Link>
              </li>
              <li>
                <Link to="/register" className="transition-colors hover:text-white">
                  Create Account
                </Link>
              </li>
            </ul>
          </nav>
        </div>

        {/* Bottom footer */}
        <div className="flex flex-col items-center justify-between gap-4 border-t border-white/[0.08] py-7 text-center sm:flex-row sm:text-left">
          <p className="text-xs text-zinc-600">
            © {new Date().getFullYear()} Library. All rights reserved.
          </p>

          <p className="text-xs text-zinc-600">Made for people who love reading.</p>
        </div>
      </div>
    </footer>
  )
}
