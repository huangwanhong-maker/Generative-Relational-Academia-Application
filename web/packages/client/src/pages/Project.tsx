/**
 * One record: its questions, and what stands unanswered in each.
 *
 * Divergent lines are shown side by side and neither is marked principal,
 * default or current, because nothing in the record designates one. There is
 * no control here that combines two of them, and not the word for it.
 */

import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { api, ApiError, type Me, type Project } from '../api'

export function ProjectPage({ me }: { me: Me }) {
  const { slug = '' } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [problem, setProblem] = useState('')

  useEffect(() => {
    void api
      .project(slug)
      .then(setProject)
      .catch((error) => setProblem(error instanceof ApiError ? error.message : String(error)))
  }, [slug])

  if (problem) return <div className="note warn">{problem}</div>
  if (!project) return <div className="note">reading…</div>

  const mine = me.signedIn && project.openedBy === me.party

  const widen = async () => {
    setProject(await api.disclose(slug))
  }

  return (
    <>
      <header>
        <h1>{project.slug}</h1>
        <p className="lede">
          opened by {project.openedByName ?? <span className="id">{project.openedBy}</span>} ·{' '}
          {project.tier} tier ·{' '}
          {project.disclosure === 'listed' ? 'shared on this server' : 'not shared here'}
        </p>
      </header>

      <h2>Questions</h2>
      {project.trajectories.map((trajectory) => (
        <div className="card" key={trajectory.trajId}>
          <strong>{trajectory.question}</strong>
          <div className="meta id">{trajectory.trajId}</div>
          <div className="meta">
            {/* A count within one trajectory, shown beside its own question and
                never next to another's. That is the line C6 draws. */}
            {trajectory.transitionCount === 1
              ? 'one transition in this line of work'
              : `${trajectory.transitionCount} transitions in this line of work`}
          </div>
          {trajectory.openCount > 0 && (
            <div className="meta open-mark">
              {trajectory.openCount === 1
                ? 'one objection nobody has answered'
                : `${trajectory.openCount} objections nobody has answered`}
            </div>
          )}
        </div>
      ))}

      {mine && project.disclosure !== 'listed' && (
        <>
          <h2>Share this project</h2>
          <div className="note">
            Listing it lets anyone read and search it, including people with no account here. It
            cannot be unlisted afterwards — disclosure widens and never narrows, so this is a decision
            rather than a setting.
          </div>
          <button onClick={widen}>share it</button>
        </>
      )}

      <div className="note">
        Recording acts — positions, objections, checks — is done with{' '}
        <span className="id">grrp</span> against the files themselves. Bringing those to this page
        is the next thing being built; nothing recorded at the terminal is invisible here, it just
        needs a reindex.
      </div>
    </>
  )
}
