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
      <div className="note">
        <strong>Registration is closed at the moment.</strong> Ask whoever runs this server; they
        add accounts with <span className="id">npm run account -- add &lt;name&gt;</span>.
        <br />
        <br />
        Not a queue and not an approval. An account is access to this particular server, and
        nothing here is a precondition for taking part: the record is plain files, and anyone can
        hold a copy, continue it under any implementation, and hand it back — with no account, and
        without asking.
      </div>

      <div className="note">
        Your account reaches a keypair, and the keypair is what signs. Two people signed in here is
        the ordinary case rather than a trick: a transition becomes attested when a party other
        than the one who performed it registers it, so a second party is what gives an act any
        weight at all.
      </div>
    </>
  )
}
