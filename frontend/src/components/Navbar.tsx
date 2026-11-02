import { useState } from 'react'
import { Link, NavLink } from 'react-router'

const navigation = [
  { name: 'Home', path: '/' },
  { name: 'Books', path: '/books' },
  { name: 'Categories', path: '/categories' },
  { name: 'About', path: '/about' },
]

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-white/8 bg-[#09090b]/90 backdrop-blur-xl">
      <nav
        aria-label="Main navigation"
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8 lg:h-19 lg:px-10"
      >
        {/* Brand */}
        <Link to="/" onClick={() => setIsOpen(false)} className="group flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl border border-white/10 bg-white/6 text-white transition-colors group-hover:bg-white/10">
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

          <span className="text-[17px] font-semibold tracking-tight text-white">
            Library<span className="text-zinc-500">.</span>
          </span>
        </Link>

        {/* Desktop navigation */}
        <ul className="hidden items-center gap-1 md:flex">
          {navigation.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `rounded-lg px-4 py-2 text-[13px] font-medium transition-colors ${
                    isActive
                      ? 'bg-white/8 text-white'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Desktop actions */}
        <div className="hidden items-center gap-3 md:flex">
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-[13px] font-medium text-zinc-300 transition-colors hover:text-white"
          >
            Sign in
          </Link>

          <Link
            to="/register"
            className="rounded-lg bg-white px-4 py-2.5 text-[13px] font-semibold text-zinc-950 transition-all hover:bg-zinc-200 active:scale-[0.98]"
          >
            Get started
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          type="button"
          aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={isOpen}
          aria-controls="mobile-navigation"
          onClick={() => setIsOpen((previous) => !previous)}
          className="flex size-10 items-center justify-center rounded-lg border border-white/10 text-zinc-300 transition-colors hover:bg-white/6 hover:text-white md:hidden"
        >
          {isOpen ? (
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="size-5"
              aria-hidden="true"
            >
              <path d="m18 6-12 12M6 6l12 12" />
            </svg>
          ) : (
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="size-5"
              aria-hidden="true"
            >
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile navigation */}
      <div
        id="mobile-navigation"
        hidden={!isOpen}
        className="border-t border-white/8 bg-[#09090b] md:hidden"
      >
        <div className="mx-auto max-w-7xl space-y-2 px-5 py-5 sm:px-8">
          <ul className="space-y-1">
            {navigation.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  onClick={() => setIsOpen(false)}
                  className={({ isActive }) =>
                    `block rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-white/8 text-white'
                        : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                    }`
                  }
                >
                  {item.name}
                </NavLink>
              </li>
            ))}
          </ul>

          <div className="flex gap-3 border-t border-white/8 pt-4">
            <Link
              to="/login"
              onClick={() => setIsOpen(false)}
              className="flex-1 rounded-lg border border-white/10 py-3 text-center text-sm font-medium text-zinc-300 hover:bg-white/5"
            >
              Sign in
            </Link>

            <Link
              to="/register"
              onClick={() => setIsOpen(false)}
              className="flex-1 rounded-lg bg-white py-3 text-center text-sm font-semibold text-zinc-950 hover:bg-zinc-200"
            >
              Get started
            </Link>
          </div>
        </div>
      </div>
    </header>
  )
}
