/**
 * The questions in a project, and what happened to each.
 *
 * A question is not a category the project belongs to — it is where a line of
 * work started, and everything below it is what the work did. Divergent lines
 * are shown side by side and none is marked principal, default or current,
 * because nothing in the record designates one.
 */

import { useEffect, useState, type FormEvent } from 'react'

import { ApiError, api, type Project, type TrajectoryDetail, type TransitionView } from '../api'
import { Markdown } from '../Markdown'
import { Modal } from '../Modal'

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
        <Markdown source={transition.body} />
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

export function Questions({
  project,
  mine,
  onOpened,
}: {
  project: Project
  mine: boolean
  onOpened: (project: Project) => void
}) {
  const [asking, setAsking] = useState(false)
  const [question, setQuestion] = useState('')
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)
  const [openId, setOpenId] = useState(project.trajectories[0]?.trajId ?? '')
  const [detail, setDetail] = useState<TrajectoryDetail | null>(null)

  useEffect(() => {
    setDetail(null)
    if (openId) void api.trajectory(project.slug, openId).then(setDetail).catch(() => setDetail(null))
  }, [project.slug, openId])

  const ask = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      const updated = await api.openQuestion(project.slug, question)
      setQuestion('')
      setAsking(false)
      onOpened(updated)
      setOpenId(updated.trajectories[updated.trajectories.length - 1]?.trajId ?? '')
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  const opener = mine && (
    <>
      <div className="row">
        <button onClick={() => setAsking(true)}>open a question</button>
      </div>
      <Modal open={asking} title="Open a question" onClose={() => setAsking(false)}>
        <form onSubmit={ask}>
          <label>
            The question you are actually trying to answer
            <textarea
              autoFocus
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              required
            />
          </label>
          {problem && <p className="warn">{problem}</p>}
          <div className="row">
            <button type="submit" disabled={busy}>
              {busy ? 'opening…' : 'open it'}
            </button>
            <button type="button" className="quiet" onClick={() => setAsking(false)}>
              cancel
            </button>
          </div>
          <div className="meta">It stays open until something answers it.</div>
        </form>
      </Modal>
    </>
  )

  if (!project.trajectories.length) {
    return (
      <>
        <p className="meta">No questions open yet.</p>
        {opener}
      </>
    )
  }

  return (
    <>
      {opener}
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


        </>
      )}
    </>
  )
}
