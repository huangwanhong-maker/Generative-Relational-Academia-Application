/**
 * The way in.
 *
 * What the password does, and does not do, is stated on the page rather than
 * implied by the shape of it. It controls who reaches this server through a
 * browser. It does not make anything true, and it is not what a reader
 * elsewhere checks — they check signatures, over keys this server never sees.
 */

import { useState, type FormEvent } from 'react'

import { api, ApiError } from '../api'

export function SignIn({ onSignedIn }: { onSignedIn: () => Promise<void> }) {
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
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <header>
        <h1>Generative Relational Academia</h1>
        <p className="lede">
          A place to record how an understanding changed — the question, the position, the
          objection nobody has answered — and to hand that record to someone else intact.
        </p>
      </header>

      <h2>Sign in</h2>
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
