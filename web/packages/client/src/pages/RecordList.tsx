/**
 * How a record is shown in a list, wherever a list appears.
 *
 * One component so that "your records" and "shared here" cannot drift apart
 * and start presenting the same thing two different ways — which is how a
 * count on one page becomes a comparison across pages.
 */

import { Link } from 'react-router-dom'

import type { Project } from '../api'

export function RecordCard({ project }: { project: Project }) {
  return (
    <div className="card">
      <Link to={`/r/${project.slug}`}>
        <strong>{project.slug}</strong>
      </Link>
      <div className="meta">
        {project.tier} tier
        {project.disclosure === 'listed' ? ' · shared on this server' : ' · not yet shared here'}
      </div>

      {project.trajectories.map((trajectory) => (
        <div className="traj" key={trajectory.trajId}>
          <Link to={`/r/${project.slug}`}>{trajectory.question}</Link>
          {trajectory.openCount > 0 && (
            <div className="meta open-mark">
              {trajectory.openCount === 1
                ? 'one objection nobody has answered'
                : `${trajectory.openCount} objections nobody has answered`}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

/**
 * Records, by name.
 *
 * Never by recency, size or anything derived from the work: an ordering over
 * trajectories tells you which of them matters before you have read any, and a
 * measure adopted to direct attention becomes the thing people work towards.
 * The server returns them in this order; this only preserves it.
 */
export function RecordList({ projects, empty }: { projects: Project[]; empty: string }) {
  if (!projects.length) return <div className="note">{empty}</div>
  return (
    <>
      {projects.map((project) => (
        <RecordCard key={project.slug} project={project} />
      ))}
    </>
  )
}
