/**
 * Your projects, and the way to create one.
 *
 * Creating asks for a name and, if you want, a description. It does not ask
 * for a question: a project is a container, and a question anchors a line of
 * work *inside* it. Asking here would conflate the two, and would also imply
 * that a project is one enquiry — which is exactly the shape this is not.
 */

import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError, type Me, type Project } from '../api'
import { Modal } from '../Modal'
import { ProjectList } from './ProjectList'

export function MyProjects({ me }: { me: Me }) {
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [creating, setCreating] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    void api.projects(true).then((reply) => setProjects(reply.projects))
  }, [])

  const create = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      const project = await api.createProject(title, description)
      navigate(`/p/${project.slug}`)
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <header>
        <h1>Your projects</h1>
        <p className="lede">
          A project holds the questions you are working on and the material they draw on.
          Underneath it is a directory of plain files — readable without this page, and yours to
          take anywhere without asking anyone.
        </p>
      </header>

      <div className="row">
        <button onClick={() => setCreating(true)}>create a project</button>
      </div>

      <ProjectList
        projects={projects ?? []}
        empty={projects === null ? 'reading…' : 'Nothing yet.'}
      />

      <Modal open={creating} title="Create a project" onClose={() => setCreating(false)}>
        <form onSubmit={create}>
          <label>
            Name
            <input
              autoFocus
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
            />
          </label>
          <label>
            Description <span className="meta">— optional</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          {problem && <p className="warn">{problem}</p>}
          <div className="row">
            <button type="submit" disabled={busy}>
              {busy ? 'creating…' : 'create it'}
            </button>
            <button type="button" className="quiet" onClick={() => setCreating(false)}>
              cancel
            </button>
          </div>
          <div className="meta">
            A project starts empty. You open questions inside it, and each one stays open until
            something answers it — there is no way to mark a question done, because most of them
            never are.
          </div>
        </form>
      </Modal>

      <div className="note">
        A project you create is not shared on this server until you say so, and sharing only ever
        widens: there is no unshare, here or anywhere in the design. You sign as{' '}
        <span className="id">{me.party}</span>.
      </div>
    </>
  )
}
