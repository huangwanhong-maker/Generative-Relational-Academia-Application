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
import { Markdown } from '../Markdown'
import { Files } from './Files'
import { GitHistory } from './GitHistory'
import { Questions } from './Questions'
import { Trajectories } from './Trajectories'

const TABS = [
  ['overview', 'Overview'],
  ['trajectories', 'Trajectories'],
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
      {tab === 'trajectories' && (
        <Trajectories
          project={project}
          mine={mine}
          onChanged={() => void api.project(slug).then(setProject)}
        />
      )}
      {tab === 'questions' && (
        <Questions project={project} mine={mine} onOpened={setProject} />
      )}
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
  return (
    <>
      {project.description && <Markdown source={project.description} />}

      <h2>Questions</h2>
      {project.trajectories.length ? (
        <ul className="questions">
          {project.trajectories.map((trajectory) => (
            <li key={trajectory.trajId}>
              <span>{trajectory.question}</span>
              {trajectory.openCount > 0 && (
                <span className="open-mark">
                  {trajectory.openCount} unanswered
                </span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="meta">None yet — open one from the Questions tab.</p>
      )}

      {mine && project.disclosure !== 'listed' && (
        <div className="row" style={{ marginTop: '1.6rem' }}>
          <button onClick={onWiden}>share this project</button>
          <span className="meta">Sharing cannot be undone.</span>
        </div>
      )}

      {dev && <GitHistory slug={project.slug} />}
    </>
  )
}
