/**
 * The way in.
 *
 * What the password does, and does not do, is stated on the page rather than
 * implied by the shape of it. It controls who reaches this server through a
 * browser. It does not make anything true, and it is not what a reader
 * elsewhere checks — they check signatures, over keys this server never sees.
 */

import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { api, ApiError, type Me } from '../api'

export function SignIn({ me, onSignedIn }: { me: Me; onSignedIn: () => Promise<void> }) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      await api.signIn(name, password)
      await onSignedIn()
      navigate('/projects')
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  if (me.signedIn) return <Navigate to="/projects" replace />

  return (
    <>
      <header>
        <h1>Sign in</h1>
        <p className="lede">
          An account is needed only to open a project of your own. Reading and searching what
          people have shared here needs nothing.
        </p>
      </header>

      <form className="signin" onSubmit={submit}>
        <label>
          Name
          <input
            autoFocus
            autoComplete="username"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {problem && <p className="warn">{problem}</p>}
        <div className="row">
          <button type="submit" disabled={busy}>
            {busy ? 'checking…' : 'sign in'}
          </button>
        </div>
      </form>

      <h2>New here</h2>
      <p className="meta">
        <strong>Registration is closed.</strong> Ask whoever runs this server —{' '}
        <span className="id">npm run account -- add &lt;name&gt;</span>. Reading and searching
        need no account.
      </p>
    </>
  )
}
