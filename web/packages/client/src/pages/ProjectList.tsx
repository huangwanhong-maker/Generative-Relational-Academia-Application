/**
 * How a project appears in a list, wherever a list appears.
 *
 * One component, so the front page and your own panel cannot drift apart and
 * start presenting the same thing two different ways — which is how a count
 * shown on one page quietly becomes a comparison across pages.
 */

import { Link } from 'react-router-dom'

import type { Project } from '../api'

export function ProjectCard({ project }: { project: Project }) {
  return (
    <div className="card">
      <Link to={`/p/${project.slug}`}>
        <strong>{project.slug}</strong>
      </Link>
      <div className="meta">
        opened by {project.openedByName ?? <span className="id">{project.openedBy}</span>} ·{' '}
        {project.tier} tier
        {project.disclosure === 'listed' ? '' : ' · not shared here'}
      </div>

      {project.trajectories.map((trajectory) => (
        <div className="traj" key={trajectory.trajId}>
          <Link to={`/p/${project.slug}`}>{trajectory.question}</Link>
          {trajectory.openCount > 0 && (
            <div className="meta open-mark">
              {trajectory.openCount === 1
                ? 'one objection nobody has answered'
                : `${trajectory.openCount} objections nobody has answered`}
            </div>
          )}
        </div>
      ))}

      {!project.trajectories.length && <div className="meta">no questions opened yet</div>}
    </div>
  )
}

/**
 * Projects, by name.
 *
 * Never by recency, size or anything derived from the work. The server returns
 * them in this order; this only preserves it.
 */
export function ProjectList({ projects, empty }: { projects: Project[]; empty: string }) {
  if (!projects.length) return <div className="note">{empty}</div>
  return (
    <>
      {projects.map((project) => (
        <ProjectCard key={project.slug} project={project} />
      ))}
    </>
  )
}
