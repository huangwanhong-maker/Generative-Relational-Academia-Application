/**
 * One project. Project-major, with tabs.
 *
 * The project is the thing you arrive at; its questions are one of the things
 * inside it, alongside its material. That is a presentation choice, and it is
 * available precisely because the record underneath is not organised that way:
 * a transition attaches to an identified state inside a line of work, never to
 * a project as a whole (C4), so the container is free to be whatever is
 * clearest to read.
 */

import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'

import { api, ApiError, type Me, type Project } from '../api'
import { Files } from './Files'
import { GitHistory } from './GitHistory'
import { Questions } from './Questions'

const TABS = [
  ['overview', 'Overview'],
  ['questions', 'Questions'],
  ['files', 'Files'],
] as const

type Tab = (typeof TABS)[number][0]

export function ProjectPage({ me }: { me: Me }) {
  const { slug = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const tab = (params.get('tab') as Tab) ?? 'overview'
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
  const widen = async () => setProject(await api.disclose(slug))

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

      <div className="tabs">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            className={key === tab ? 'tab on' : 'tab'}
            onClick={() => setParams(key === 'overview' ? {} : { tab: key })}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <Overview project={project} mine={mine} dev={Boolean(me.dev)} onWiden={widen} />
      )}
      {tab === 'questions' && <Questions project={project} />}
      {tab === 'files' && <Files project={project} me={me} />}
    </>
  )
}

function Overview({
  project,
  mine,
  dev,
  onWiden,
}: {
  project: Project
  mine: boolean
  dev: boolean
  onWiden: () => Promise<void>
}) {
  const standing = project.trajectories.filter((trajectory) => trajectory.openCount > 0)

  return (
    <>
      <h2>What this project is trying to find out</h2>
      {project.trajectories.length ? (
        project.trajectories.map((trajectory) => (
          <p className="framing" key={trajectory.trajId}>
            {trajectory.question}
          </p>
        ))
      ) : (
        <div className="note">No questions opened yet.</div>
      )}

      <h2>Standing unanswered</h2>
      {standing.length ? (
        standing.map((trajectory) => (
          <div className="card open" key={trajectory.trajId}>
            <div className="meta open-mark">
              {trajectory.openCount === 1
                ? 'one objection nobody has answered'
                : `${trajectory.openCount} objections nobody has answered`}
            </div>
            <div className="meta">under: {trajectory.question}</div>
          </div>
        ))
      ) : (
        <div className="note">
          Nothing objected to and unanswered. That is a statement about what has been recorded, not
          a claim that the work is sound.
        </div>
      )}

      {mine && project.disclosure !== 'listed' && (
        <>
          <h2>Share this project</h2>
          <div className="note">
            Listing it lets anyone read and search it, including people with no account here. It
            cannot be unlisted afterwards — disclosure widens and never narrows, so this is a
            decision rather than a setting.
          </div>
          <button onClick={onWiden}>share it</button>
        </>
      )}

      <h2>Working on it</h2>
      <div className="note">
        Positions, objections and checks are recorded with <span className="id">grrp</span> against
        the files themselves — <span className="id">grrp claim</span>,{' '}
        <span className="id">grrp challenge</span>, <span className="id">grrp verify</span>.
        Bringing those to this page is the next piece of work; nothing recorded at the terminal is
        invisible here, it only needs a reindex.
      </div>

      {dev && <GitHistory slug={project.slug} />}
    </>
  )
}
