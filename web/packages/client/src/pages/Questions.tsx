/**
 * The questions in a project, and what happened to each.
 *
 * A question is not a category the project belongs to — it is where a line of
 * work started, and everything below it is what the work did. Divergent lines
 * are shown side by side and none is marked principal, default or current,
 * because nothing in the record designates one.
 */

import { useEffect, useState } from 'react'

import { api, type Project, type TrajectoryDetail, type TransitionView } from '../api'

/** What each act leaves behind, in the words a person would use for it. */
const READS_AS: Record<string, string> = {
  question: 'the question',
  claim: 'a position',
  transformation: 'a position, changed',
  challenge: 'an objection',
  decision: 'a decision',
  verification: 'a check',
  connection: 'a connection',
  release: 'a release',
}

function Transition({ transition }: { transition: TransitionView }) {
  const standing =
    transition.act !== 'question' &&
    (transition.disposition === 'unresolved' || transition.disposition === 'contested')

  return (
    <div className={`card${standing ? ' open' : ''}`}>
      <div className="meta">
        {READS_AS[transition.act ?? ''] ?? transition.act}
        {transition.target ? ` · on the ${transition.target}` : ''}
        {transition.trigger && transition.trigger !== 'self' ? ` · from ${transition.trigger}` : ''}
        {' · '}
        {transition.disposition}
        {transition.attested ? ' · attested' : ' · unattested'}
      </div>
      {transition.body ? (
        <p className="body">{transition.body.trim()}</p>
      ) : (
        <p className="meta">(content not held here)</p>
      )}
      <div className="meta id">{transition.id.split(':').pop()?.slice(0, 12)}</div>
    </div>
  )
}

/**
 * The drawing, in an `<img>` rather than inlined.
 *
 * An SVG inlined into the page can carry script; the same SVG loaded as an
 * image cannot. The picture comes from the reference implementation and is
 * escaped there, but a rendering path that is safe only while an escaping
 * function stays correct is not safe.
 */
function Graph({ svg }: { svg: string }) {
  return (
    <div className="scroll">
      <img
        alt="The trajectory: one column per step away from the question."
        src={`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`}
      />
    </div>
  )
}

export function Questions({ project }: { project: Project }) {
  const [openId, setOpenId] = useState(project.trajectories[0]?.trajId ?? '')
  const [detail, setDetail] = useState<TrajectoryDetail | null>(null)

  useEffect(() => {
    setDetail(null)
    if (openId) void api.trajectory(project.slug, openId).then(setDetail).catch(() => setDetail(null))
  }, [project.slug, openId])

  if (!project.trajectories.length) {
    return (
      <div className="note">
        No questions opened yet. A project without one has nothing for a transition to attach to —
        every act changes an identified state, and the question is the first state there is.
      </div>
    )
  }

  return (
    <>
      {project.trajectories.length > 1 && (
        <div className="chips">
          {project.trajectories.map((trajectory) => (
            <button
              key={trajectory.trajId}
              className={trajectory.trajId === openId ? 'chip on' : 'chip'}
              onClick={() => setOpenId(trajectory.trajId)}
            >
              {trajectory.title ?? trajectory.trajId}
            </button>
          ))}
        </div>
      )}

      {detail === null ? (
        <div className="note">reading…</div>
      ) : (
        <>
          <h2>The question</h2>
          <p className="framing">{detail.question}</p>

          {detail.graph && (
            <>
              <h2>How it moved</h2>
              <Graph svg={detail.graph} />
            </>
          )}

          <h2>What happened</h2>
          {detail.transitions.map((transition) => (
            <Transition key={transition.id} transition={transition} />
          ))}

          <div className="note">
            Parents before children, then in the order they were performed. Not ordered by
            importance, because nothing here computes importance.
          </div>
        </>
      )}
    </>
  )
}
