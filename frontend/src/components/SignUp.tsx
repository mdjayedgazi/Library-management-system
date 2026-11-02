import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'

export type SignUpField = {
  name: string
  label: string
  type: 'text' | 'email' | 'password'
  placeholder: string
  autoComplete?: string
  required?: boolean
  minLength?: number
  width?: 'half' | 'full'
  includeInPayload?: boolean
  confirmFor?: string
}

export type SignUpValues = Record<string, string>

type SignUpProps = {
  title: string
  description: string
  fields: SignUpField[]
  values: SignUpValues
  onChange: (name: string, value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  loading: boolean
  error: string | null
  success: string | null
  loginPath: string
  submitLabel: string
  loadingLabel: string
  footerText: string
  loginLabel: string
}

const SignUp = ({
  title,
  description,
  fields,
  values,
  onChange,
  onSubmit,
  loading,
  error,
  success,
  loginPath,
  submitLabel,
  loadingLabel,
  footerText,
  loginLabel,
}: SignUpProps) => {
  const [visiblePasswords, setVisiblePasswords] = useState<Record<string, boolean>>({})

  const togglePassword = (name: string) => {
    setVisiblePasswords((previous) => ({
      ...previous,
      [name]: !previous[name],
    }))
  }

  return (
    <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-base-200/40 px-4 py-10">
      <section className="w-full max-w-lg rounded-2xl border border-base-300 bg-base-100 p-6 shadow-xl sm:p-9">
        {/* Heading */}
        <div className="mb-7 text-center">
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>

          <p className="mt-2 text-sm text-base-content/60">{description}</p>
        </div>

        {/* Dynamic Form */}
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {fields.map((field) => {
              const isPassword = field.type === 'password'
              const isVisible = visiblePasswords[field.name] ?? false

              return (
                <div
                  key={field.name}
                  className={field.width === 'half' ? 'space-y-2' : 'space-y-2 sm:col-span-2'}
                >
                  <label htmlFor={field.name} className="text-sm font-semibold">
                    {field.label}
                  </label>

                  <div className="relative">
                    <input
                      id={field.name}
                      name={field.name}
                      type={isPassword && isVisible ? 'text' : field.type}
                      placeholder={field.placeholder}
                      autoComplete={field.autoComplete}
                      required={field.required ?? true}
                      minLength={field.minLength}
                      value={values[field.name] ?? ''}
                      onChange={(event) => onChange(field.name, event.target.value)}
                      className={`input input-bordered w-full ${isPassword ? 'pr-16' : ''}`}
                    />

                    {isPassword && (
                      <button
                        type="button"
                        onClick={() => togglePassword(field.name)}
                        aria-label={isVisible ? 'Hide password' : 'Show password'}
                        className="absolute inset-y-0 right-3 text-xs font-medium text-base-content/60 hover:text-base-content"
                      >
                        {isVisible ? 'Hide' : 'Show'}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Feedback */}
          {error && (
            <p role="alert" className="text-sm text-error">
              {error}
            </p>
          )}

          {success && (
            <p role="status" className="text-sm text-success">
              {success}
            </p>
          )}

          {/* Submit */}
          <button type="submit" disabled={loading} className="btn btn-neutral mt-2 w-full">
            {loading ? loadingLabel : submitLabel}
          </button>
        </form>

        {/* Login Navigation */}
        <div className="mt-7 border-t border-base-300 pt-6 text-center">
          <p className="text-sm text-base-content/60">
            {footerText}{' '}
            <Link
              to={loginPath}
              className="font-semibold text-base-content underline-offset-4 hover:underline"
            >
              {loginLabel}
            </Link>
          </p>
        </div>
      </section>
    </main>
  )
}

export default SignUp
