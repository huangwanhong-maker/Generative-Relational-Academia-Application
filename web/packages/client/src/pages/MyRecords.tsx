/**
 * Your records, and the way to start one.
 */

import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError, type Me, type Project } from '../api'
import { RecordList } from './RecordList'

export function MyRecords({ me }: { me: Me }) {
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [title, setTitle] = useState('')
  const [question, setQuestion] = useState('')
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    void api.projects(true).then((reply) => setProjects(reply.projects))
  }, [])

  const open = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      const project = await api.openProject(title, question)
      navigate(`/r/${project.slug}`)
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <header>
        <h1>Your records</h1>
        <p className="lede">
          Each record is a directory of work with one or more questions in it. It is plain files in
          a filesystem — readable without this page, and yours to take anywhere without asking
          anyone.
        </p>
      </header>

      <h2>Here</h2>
      <RecordList
        projects={projects ?? []}
        empty={
          projects === null
            ? 'reading…'
            : 'Nothing yet. A record starts with a question you are actually trying to answer.'
        }
      />

      <h2>Start a record</h2>
      <form onSubmit={open}>
        <label>
          The question you are actually trying to answer
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            required
          />
        </label>
        <label>
          A short name
          <input value={title} onChange={(event) => setTitle(event.target.value)} required />
        </label>
        {problem && <p className="warn">{problem}</p>}
        <div className="row">
          <button type="submit" disabled={busy}>
            {busy ? 'opening…' : 'open it'}
          </button>
        </div>
        <div className="meta">
          Write down what you are trying to find out, once, before the framing hardens and you
          forget you chose it. It stays open until something answers it — there is no way to mark a
          question done, because most of them never are.
        </div>
      </form>

      <div className="note">
        A record you open is not shared on this server until you say so, and sharing only ever
        widens: there is no unshare, here or anywhere in the design. Signed in as{' '}
        <span className="id">{me.party}</span>.
      </div>
    </>
  )
}
