import { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router'
import type { NavbarProps } from '../type.ts'

export default function Navbar({ isAuthenticated, user, onLogout }: NavbarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { pathname } = useLocation()

  const isAuthPage = pathname === '/login' || pathname === '/register'

  const avatarLetter =
    user?.name?.trim().charAt(0).toUpperCase() || user?.email?.trim().charAt(0).toUpperCase() || 'U'

  const handleLogout = () => {
    setIsOpen(false)
    void onLogout()
  }

  const activeLink = ({ isActive }: { isActive: boolean }) =>
    `rounded-lg px-4 py-2 text-[13px] font-medium transition-colors ${
      isActive ? 'bg-white/8 text-white' : 'text-zinc-400 hover:bg-white/5 hover:text-white'
    }`

  const UserProfile = () => (
    <div className="flex items-center gap-2.5">
      <div className="flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-full border border-white/15 bg-white/10 text-sm font-semibold text-white">
        {user?.image ? (
          <img src={user.image} alt="User profile" className="size-full object-cover" />
        ) : (
          avatarLetter
        )}
      </div>

      <span className="max-w-32 truncate text-sm font-medium text-white">
        {user?.name || user?.email || 'My Account'}
      </span>
    </div>
  )

  return (
    <header className="sticky top-0 z-50 border-b border-white/8 bg-[#09090b]/90 backdrop-blur-xl">
      <nav
        aria-label="Main navigation"
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8 lg:h-19 lg:px-10"
      >
        {/* Brand */}
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl border border-white/10 bg-white/6 text-white">
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
        </div>

        {/* Desktop Navigation */}
        <ul className="hidden items-center gap-1 md:flex">
          <li>
            <NavLink to="/" end className={activeLink}>
              Home
            </NavLink>
          </li>

          <li>
            <NavLink to="/books" className={activeLink}>
              Books
            </NavLink>
          </li>

          <li>
            <NavLink to="/categories" className={activeLink}>
              Categories
            </NavLink>
          </li>

          <li>
            <NavLink to="/about" className={activeLink}>
              About
            </NavLink>
          </li>
        </ul>

        {/* Desktop Actions */}
        <div className="hidden items-center gap-3 md:flex">
          {!isAuthPage &&
            (isAuthenticated ? (
              <>
                <UserProfile />

                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-lg border border-white/10 px-4 py-2.5 text-[13px] font-medium text-zinc-300 transition-colors hover:bg-white/5 hover:text-white"
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded-lg px-4 py-2 text-[13px] font-medium text-zinc-300 transition-colors hover:text-white"
                >
                  Sign in
                </Link>

                <Link
                  to="/register"
                  className="rounded-lg bg-white px-4 py-2.5 text-[13px] font-semibold text-zinc-950 transition-colors hover:bg-zinc-200"
                >
                  Get started
                </Link>
              </>
            ))}
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          aria-label={isOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isOpen}
          aria-controls="mobile-navigation"
          onClick={() => setIsOpen((previous) => !previous)}
          className="flex size-10 items-center justify-center rounded-lg border border-white/10 text-zinc-300 hover:bg-white/6 hover:text-white md:hidden"
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

      {/* Mobile Navigation */}
      <div
        id="mobile-navigation"
        hidden={!isOpen}
        className="border-t border-white/8 bg-[#09090b] md:hidden"
      >
        <div className="mx-auto max-w-7xl space-y-2 px-5 py-5 sm:px-8">
          <ul className="space-y-1">
            <li>
              <NavLink
                to="/"
                end
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `block rounded-lg px-4 py-3 text-sm font-medium ${
                    isActive
                      ? 'bg-white/8 text-white'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                Home
              </NavLink>
            </li>

            <li>
              <NavLink
                to="/books"
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `block rounded-lg px-4 py-3 text-sm font-medium ${
                    isActive
                      ? 'bg-white/8 text-white'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                Books
              </NavLink>
            </li>

            <li>
              <NavLink
                to="/categories"
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `block rounded-lg px-4 py-3 text-sm font-medium ${
                    isActive
                      ? 'bg-white/8 text-white'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                Categories
              </NavLink>
            </li>

            <li>
              <NavLink
                to="/about"
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `block rounded-lg px-4 py-3 text-sm font-medium ${
                    isActive
                      ? 'bg-white/8 text-white'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                About
              </NavLink>
            </li>
          </ul>

          {/* Mobile Actions */}
          {!isAuthPage && (
            <div className="space-y-4 border-t border-white/8 pt-4">
              {isAuthenticated ? (
                <>
                  <UserProfile />

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full rounded-lg border border-white/10 py-3 text-sm font-medium text-zinc-300 hover:bg-white/5"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <div className="flex gap-3">
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
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
