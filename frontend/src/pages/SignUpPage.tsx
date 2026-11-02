import { useState, type FormEvent } from 'react'
import { baseUel } from '../servies/BaseUel.tsx'

import SignUp, { type SignUpField, type SignUpValues } from '../components/SignUp.tsx'

// Registration configuration
const registerFields: SignUpField[] = [
  {
    name: 'first_name',
    label: 'First name',
    type: 'text',
    placeholder: 'First name',
    autoComplete: 'given-name',
    width: 'half',
  },
  {
    name: 'last_name',
    label: 'Last name',
    type: 'text',
    placeholder: 'Last name',
    autoComplete: 'family-name',
    width: 'half',
  },
  {
    name: 'username',
    label: 'Username',
    type: 'text',
    placeholder: 'Choose a username',
    autoComplete: 'username',
  },
  {
    name: 'email',
    label: 'Email address',
    type: 'email',
    placeholder: 'you@example.com',
    autoComplete: 'email',
  },
  {
    name: 'password',
    label: 'Password',
    type: 'password',
    placeholder: 'Create a password',
    autoComplete: 'new-password',
    minLength: 8,
  },
  {
    name: 'confirm_password',
    label: 'Confirm password',
    type: 'password',
    placeholder: 'Confirm your password',
    autoComplete: 'new-password',
    minLength: 8,
    includeInPayload: false,
    confirmFor: 'password',
  },
]

// Generate initial values from field configuration
const createInitialValues = (): SignUpValues =>
  Object.fromEntries(registerFields.map(({ name }) => [name, '']))

const SignUpPage = () => {
  const [values, setValues] = useState<SignUpValues>(createInitialValues)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Handle dynamic input changes
  const handleChange = (name: string, value: string) => {
    setValues((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  // Handle registration
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    setError(null)
    setSuccess(null)

    // Dynamic confirmation validation
    const confirmationField = registerFields.find((field) => field.confirmFor)

    if (
      confirmationField?.confirmFor &&
      values[confirmationField.name] !== values[confirmationField.confirmFor]
    ) {
      setError('Passwords do not match.')
      return
    }

    // Generate API payload from field configuration
    const payload = Object.fromEntries(
      registerFields
        .filter((field) => field.includeInPayload !== false)
        .map((field) => {
          const value = values[field.name] ?? ''

          return [field.name, field.type === 'email' ? value.trim().toLowerCase() : value]
        }),
    )

    try {
      setLoading(true)

      const response = await fetch(`${baseUel.replace(/\/+$/, '')}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data: unknown = await response.json().catch(() => null)

      if (!response.ok) {
        const detail =
          typeof data === 'object' &&
          data !== null &&
          'detail' in data &&
          typeof data.detail === 'string'
            ? data.detail
            : 'Registration failed. Please try again.'

        throw new Error(detail)
      }

      setSuccess('Account created successfully. You can now sign in.')
      setValues(createInitialValues())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SignUp
      title="Create your account"
      description="Join our library and start exploring books."
      fields={registerFields}
      values={values}
      onChange={handleChange}
      onSubmit={handleSubmit}
      loading={loading}
      error={error}
      success={success}
      loginPath="/login"
      submitLabel="Create account"
      loadingLabel="Creating account..."
      footerText="Already have an account?"
      loginLabel="Sign in"
    />
  )
}

export default SignUpPage
