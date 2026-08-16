/**
 * The whole project as one graph, across every question.
 *
 * Per-question views hide the structure that matters most: an experiment that
 * bears on three questions, a position that answers an objection raised under
 * another. Those are ordinary edges in the record and always have been —
 * `parents` is a list, and `grrp connect` to a state elsewhere makes that
 * state's transition a parent.
 *
 * Three things this drawing refuses to do:
 *
 *   No node is marked principal, default or current. Divergent lines are drawn
 *   identically, because nothing in the record designates one (C5).
 *
 *   Nothing is sized, coloured or placed by importance. Depth is distance from
 *   a question and nothing else — a layout that ranked nodes would be a
 *   measure over the work wearing a picture (C6).
 *
 *   Nothing offers to combine two lines. There is no such operation and not
 *   the word for it.
 */

import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { api, ApiError, type GraphEdge, type GraphNode, type Project } from '../api'
import { Modal } from '../Modal'

const COLUMN = 230
const ROW = 96
const BOX_W = 190
const BOX_H = 62

/** What each act leaves behind, in the words a person would use for it. */
const READS_AS: Record<string, string> = {
  question: 'question',
  claim: 'position',
  transformation: 'position, changed',
  challenge: 'objection',
  decision: 'decision',
  verification: 'check',
  connection: 'connection',
  release: 'release',
}

interface Placed extends GraphNode {
  x: number
  y: number
}

/**
 * Depth is the longest path from a node with no parents.
 *
 * Longest rather than shortest so that a node always sits to the right of
 * everything it depends on, including through a cross-trajectory link. That is
 * a statement about dependency, not about importance.
 */
function layout(nodes: GraphNode[], edges: GraphEdge[]): { placed: Placed[]; width: number; height: number } {
  const incoming = new Map<string, string[]>()
  for (const node of nodes) incoming.set(node.id, [])
  for (const edge of edges) incoming.get(edge.to)?.push(edge.from)

  const depth = new Map<string, number>()
  const settle = (id: string, guard: Set<string>): number => {
    if (depth.has(id)) return depth.get(id)!
    if (guard.has(id)) return 0
    guard.add(id)
    const parents = incoming.get(id) ?? []
    const value = parents.length
      ? Math.max(...parents.map((parent) => settle(parent, guard) + 1))
      : 0
    depth.set(id, value)
    return value
  }
  for (const node of nodes) settle(node.id, new Set())

  const columns = new Map<number, GraphNode[]>()
  for (const node of nodes) {
    const column = depth.get(node.id) ?? 0
    columns.set(column, [...(columns.get(column) ?? []), node])
  }

  const placed: Placed[] = []
  let tallest = 0
  for (const [column, members] of [...columns.entries()].sort((a, b) => a[0] - b[0])) {
    // Within a column, by time then identifier: repeatable, and not a ranking.
    members.sort((a, b) => a.performed.localeCompare(b.performed) || a.id.localeCompare(b.id))
    members.forEach((node, row) => {
      placed.push({ ...node, x: 20 + column * COLUMN, y: 20 + row * ROW })
    })
    tallest = Math.max(tallest, members.length)
  }

  return {
    placed,
    width: 40 + columns.size * COLUMN,
    height: 40 + tallest * ROW,
  }
}

function wrap(text: string, width = 26, lines = 2): string[] {
  const words = text.split(/\s+/).filter(Boolean)
  const out: string[] = []
  let current = ''
  for (const word of words) {
    if ((current + ' ' + word).trim().length > width) {
      out.push(current)
      current = word
      if (out.length === lines) break
    } else {
      current = (current + ' ' + word).trim()
    }
  }
  if (out.length < lines && current) out.push(current)
  if (out.length === lines && out.join(' ').length < text.length) {
    out[lines - 1] = out[lines - 1]!.slice(0, width - 1) + '…'
  }
  return out
}

function Drawing({
  nodes,
  edges,
  onPick,
}: {
  nodes: GraphNode[]
  edges: GraphEdge[]
  onPick: (node: GraphNode) => void
}) {
  const { placed, width, height } = useMemo(() => layout(nodes, edges), [nodes, edges])
  const at = new Map(placed.map((node) => [node.id, node]))

  return (
    <div className="scroll">
      <svg width={width} height={height} role="img" aria-label="The project, as one graph.">
        {edges.map((edge, index) => {
          const from = at.get(edge.from)
          const to = at.get(edge.to)
          if (!from || !to) return null
          const x1 = from.x + BOX_W
          const y1 = from.y + BOX_H / 2
          const x2 = to.x
          const y2 = to.y + BOX_H / 2
          const mid = (x1 + x2) / 2
          return (
            <path
              key={`${edge.from}-${edge.to}-${index}`}
              className={`e-${edge.kind}`}
              d={`M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`}
            />
          )
        })}

        {placed.map((node) => {
          const standing =
            node.act !== 'question' &&
            (node.disposition === 'unresolved' || node.disposition === 'contested')
          const classes = [
            'n-box',
            node.shape === 'artefact' ? 'artefact' : '',
            standing ? 'open' : '',
          ]
            .filter(Boolean)
            .join(' ')
          return (
            <g key={node.id} className="n" onClick={() => onPick(node)}>
              <rect className={classes} x={node.x} y={node.y} width={BOX_W} height={BOX_H} rx="5" />
              <text className="n-kind" x={node.x + 10} y={node.y + 17}>
                {node.shape === 'artefact'
                  ? node.trigger && node.trigger !== 'self'
                    ? node.trigger
                    : 'material'
                  : READS_AS[node.act ?? ''] ?? node.act}
              </text>
              {wrap(node.label).map((line, index) => (
                <text className="n-text" key={index} x={node.x + 10} y={node.y + 34 + index * 15}>
                  {line}
                </text>
              ))}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export function Trajectories({
  project,
  mine,
  onChanged,
}: {
  project: Project
  mine: boolean
  onChanged: () => void
}) {
  const [graph, setGraph] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null)
  const [picked, setPicked] = useState<GraphNode | null>(null)
  const [linking, setLinking] = useState(false)
  const [to, setTo] = useState('')
  const [why, setWhy] = useState('')
  const [from, setFrom] = useState(project.trajectories[0]?.trajId ?? '')
  const [relation, setRelation] = useState('relates')
  const [trigger, setTrigger] = useState('literature')
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => {
    void api
      .graph(project.slug)
      .then(setGraph)
      .catch(() => setGraph({ nodes: [], edges: [] }))
  }

  useEffect(load, [project.slug])

  const connect = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      setGraph(await api.connect(project.slug, { to, message: why, traj: from, relation, trigger }))
      setTo('')
      setWhy('')
      setLinking(false)
      onChanged()
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  if (!graph) return <div className="note">reading…</div>

  const crossings = graph.edges.filter((edge) => edge.kind === 'crosses').length
  const shared = graph.nodes.filter(
    (node) =>
      node.shape === 'artefact' &&
      graph.edges.filter((edge) => edge.from === node.id).length > 1,
  )

  return (
    <>
      {mine && (
        <div className="row">
          <button onClick={() => setLinking(true)}>record a connection</button>
        </div>
      )}

      {graph.nodes.length === 0 ? (
        <div className="note">
          Nothing recorded yet. Open a question, and what follows from it appears here.
        </div>
      ) : (
        <>
          <Drawing nodes={graph.nodes} edges={graph.edges} onPick={setPicked} />

          <div className="note">
            Every question in this project, in one graph. Left to right is distance from a
            question, not importance — nothing here is ranked, sized or coloured by how much it
            matters, and no line is marked the principal one.
            <br />
            <br />
            {crossings > 0 ? (
              <>
                <strong>{crossings}</strong> edge{crossings === 1 ? '' : 's'} cross between
                questions.{' '}
              </>
            ) : (
              <>
                Nothing crosses between questions yet. A connection to a state under another
                question makes that state's transition a parent, and the graph stops being a line.{' '}
              </>
            )}
            {shared.length > 0 && (
              <>
                <strong>{shared.length}</strong> piece
                {shared.length === 1 ? '' : 's'} of material {shared.length === 1 ? 'is' : 'are'}{' '}
                cited by more than one transition — the same occasion bearing on more than one
                line of work.
              </>
            )}
          </div>
        </>
      )}

      <Modal open={Boolean(picked)} title="This node" onClose={() => setPicked(null)}>
        {picked && (
          <>
            <div className="meta">
              {picked.shape === 'artefact'
                ? 'material — cited, not recorded'
                : READS_AS[picked.act ?? ''] ?? picked.act}
              {picked.trigger && picked.trigger !== 'self' ? ` · occasioned by ${picked.trigger}` : ''}
              {picked.disposition ? ` · ${picked.disposition}` : ''}
              {picked.shape === 'transition' && (picked.attested ? ' · attested' : ' · unattested')}
            </div>
            <p className="body">{picked.label}</p>
            {picked.question && <div className="meta">under: {picked.question}</div>}
            <div className="meta id">{picked.id}</div>
          </>
        )}
      </Modal>

      <Modal open={linking} title="Record a connection" onClose={() => setLinking(false)}>
        <form onSubmit={connect}>
          <label>
            Made from which question
            <select value={from} onChange={(event) => setFrom(event.target.value)}>
              {project.trajectories.map((trajectory) => (
                <option key={trajectory.trajId} value={trajectory.trajId}>
                  {trajectory.question}
                </option>
              ))}
            </select>
          </label>
          <label>
            What it points at
            <input
              autoFocus
              value={to}
              onChange={(event) => setTo(event.target.value)}
              placeholder="a state here, or doi: arxiv: https:…"
              required
            />
          </label>
          <label>
            Why it matters
            <textarea value={why} onChange={(event) => setWhy(event.target.value)} required />
          </label>
          <div className="row">
            <label>
              Relation
              <select value={relation} onChange={(event) => setRelation(event.target.value)}>
                {['relates', 'supports', 'refutes', 'confirms', 'disputes', 'extends', 'usesMethodIn', 'usesDataFrom'].map(
                  (value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ),
                )}
              </select>
            </label>
            <label>
              Occasioned by
              <select value={trigger} onChange={(event) => setTrigger(event.target.value)}>
                {['literature', 'experiment', 'simulation', 'observation', 'discussion', 'objection', 'failure'].map(
                  (value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ),
                )}
              </select>
            </label>
          </div>
          {problem && <p className="warn">{problem}</p>}
          <div className="row">
            <button type="submit" disabled={busy}>
              {busy ? 'recording…' : 'record it'}
            </button>
            <button type="button" className="quiet" onClick={() => setLinking(false)}>
              cancel
            </button>
          </div>
          <div className="meta">
            A connection is an act: it is recorded, attributed and says why the connection matters.
            That is what separates it from adding a file — a claim about how two things bear on
            each other has an author. Relations bind to CiTO rather than to words invented here.
          </div>
        </form>
      </Modal>
    </>
  )
}
