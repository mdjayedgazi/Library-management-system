import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'

type LoginProps = {
  onLogin?: (credentials: { email: string; password: string }) => void | Promise<void>
}

const Login = ({ onLogin }: LoginProps) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (!onLogin) {
      setError('Login functionality has not been connected yet.')
      return
    }

    try {
      setLoading(true)
      await onLogin({ email, password })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-base-200/40 px-4 py-12">
      {/* Login Card */}
      <section className="w-full max-w-md rounded-2xl border border-base-300 bg-base-100 p-7 shadow-xl sm:p-9">
        {/* Heading */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex size-12 items-center justify-center rounded-xl bg-neutral text-neutral-content">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              className="size-6"
              aria-hidden="true"
            >
              <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
              <path d="M4 5.5v16M8 7h8M8 11h7" />
            </svg>
          </div>

          <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>

          <p className="mt-2 text-sm text-base-content/60">
            Sign in to access your library account.
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Email */}
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-semibold">
              Email address
            </label>

            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="input input-bordered w-full"
            />
          </div>

          {/* Password */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="password" className="text-sm font-semibold">
                Password
              </label>
            </div>

            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="input input-bordered w-full pr-16"
              />

              <button
                type="button"
                onClick={() => setShowPassword((previous) => !previous)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute inset-y-0 right-3 text-xs font-medium text-base-content/60 hover:text-base-content"
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <p role="alert" className="text-sm text-error">
              {error}
            </p>
          )}

          {/* Submit */}
          <button type="submit" disabled={loading} className="btn btn-neutral mt-2 w-full">
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* Registration */}
        <div className="mt-7 border-t border-base-300 pt-6 text-center">
          <p className="text-sm text-base-content/60">
            Don't have an account?{' '}
            <Link
              to="/register"
              className="font-semibold text-base-content underline-offset-4 hover:underline"
            >
              Create an account
            </Link>
          </p>
        </div>
      </section>
    </main>
  )
}

export default Login
