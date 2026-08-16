/**
 * The Trajectories tab: the whole project as one living graph.
 *
 * Spec: plans/spec-graph-model.md. Three node families (transition, material,
 * occasion — occasions derived, never creatable), two edge families
 * (structural facts; reified connections). A connection with two or more
 * parents is drawn as an EDGE — a labelled chip at its midpoint, joined by
 * curves to what it connects — and opened as a node, because it is one.
 *
 * The canvas is direct: nodes drag, the view pans and zooms, selection lights
 * what is connected and lets the rest recede. Dragged positions are layout,
 * not record — they persist in localStorage (the local plane: this machine,
 * this viewer, exported to nobody).
 *
 * What the drawing still refuses: nothing is sized, coloured or placed by
 * importance; no line is marked principal; emphasis marks attention, never
 * worth.
 */

import { useEffect, useMemo, useRef, useState, type FormEvent, type PointerEvent as ReactPointerEvent, type WheelEvent as ReactWheelEvent } from 'react'

import { api, ApiError, type GraphEdge, type GraphNode, type Project } from '../api'
import { Modal } from '../Modal'
import { NodePanel } from './NodePanel'

/* ---------------------------------------------------------------- vocabulary */

export const READS_AS: Record<string, string> = {
  question: 'question',
  claim: 'position',
  transformation: 'position, changed',
  challenge: 'objection',
  decision: 'decision',
  verification: 'check',
  connection: 'connection',
  release: 'release',
}

/** Occasion labels derive from the trigger — the citation is the membership. */
const OCCASIONS: [string, string][] = [
  ['discussion', 'meeting'],
  ['experiment', 'experiment'],
  ['observation', 'observation'],
  ['simulation', 'simulation'],
  ['literature', 'reading'],
  ['failure', 'failure'],
]

export function occasionOf(node: GraphNode): string | null {
  if (node.shape !== 'artefact') return null
  for (const [trigger, label] of OCCASIONS) {
    if ((node.triggers ?? []).includes(trigger)) return label
  }
  const local = (node.triggers ?? []).find((t) => t.startsWith('local:'))
  return local ? local.slice(6) : null
}

export function relationReads(relation: string | null): string | null {
  if (!relation) return null
  return relation.startsWith('cito:') ? relation.slice(5) : relation
}

/* ------------------------------------------------------------- presentation */

type PKind = 'transition' | 'chip' | 'material' | 'occasion'

interface PNode {
  id: string
  kind: PKind
  node: GraphNode
  w: number
  h: number
}

const SIZES: Record<PKind, { w: number; h: number }> = {
  transition: { w: 200, h: 68 },
  chip: { w: 128, h: 28 },
  material: { w: 184, h: 56 },
  occasion: { w: 184, h: 56 },
}

/** A connection with two or more parents reads as an edge; give it a chip. */
function present(nodes: GraphNode[]): PNode[] {
  return nodes.map((node) => {
    let kind: PKind
    if (node.shape === 'artefact') kind = occasionOf(node) ? 'occasion' : 'material'
    else if (node.act === 'connection' && node.parents.length >= 2) kind = 'chip'
    else kind = 'transition'
    return { id: node.id, kind, node, ...SIZES[kind] }
  })
}

/* --------------------------------------------------------------------- layout */

interface Point { x: number; y: number }

function autoLayout(pnodes: PNode[], edges: GraphEdge[]): Map<string, Point> {
  const incoming = new Map<string, string[]>()
  for (const p of pnodes) incoming.set(p.id, [])
  for (const e of edges) incoming.get(e.to)?.push(e.from)

  const depth = new Map<string, number>()
  const settle = (id: string, guard: Set<string>): number => {
    if (depth.has(id)) return depth.get(id)!
    if (guard.has(id)) return 0
    guard.add(id)
    const parents = incoming.get(id) ?? []
    const value = parents.length ? Math.max(...parents.map((p) => settle(p, guard) + 1)) : 0
    depth.set(id, value)
    return value
  }
  for (const p of pnodes) settle(p.id, new Set())

  const columns = new Map<number, PNode[]>()
  for (const p of pnodes) {
    const c = depth.get(p.id) ?? 0
    columns.set(c, [...(columns.get(c) ?? []), p])
  }

  const out = new Map<string, Point>()
  for (const [c, members] of [...columns.entries()].sort((a, b) => a[0] - b[0])) {
    members.sort(
      (a, b) => a.node.performed.localeCompare(b.node.performed) || a.id.localeCompare(b.id),
    )
    let y = 28
    for (const p of members) {
      out.set(p.id, { x: 28 + c * 252, y })
      y += p.h + 26
    }
  }
  return out
}

function layoutKey(slug: string) {
  return `gra:layout:${slug}`
}

function savedLayout(slug: string): Record<string, Point> {
  try {
    return JSON.parse(localStorage.getItem(layoutKey(slug)) ?? '{}')
  } catch {
    return {}
  }
}

/* --------------------------------------------------------------------- canvas */

function wrap(text: string, width: number, lines: number): string[] {
  const words = text
    .split(/\s+/)
    .filter(Boolean)
    .flatMap((w) => (w.length <= width ? [w] : (w.match(new RegExp(`.{1,${width}}`, 'g')) ?? [w])))
  const out: string[] = []
  let current = ''
  for (const word of words) {
    if ((current + ' ' + word).trim().length > width) {
      if (current) out.push(current)
      current = word
      if (out.length === lines) break
    } else current = (current + ' ' + word).trim()
  }
  if (out.length < lines && current) out.push(current)
  if (out.join(' ').replace(/\s+/g, '').length < text.replace(/\s+/g, '').length && out.length) {
    out[out.length - 1] = out[out.length - 1]!.slice(0, width - 1) + '…'
  }
  return out
}

function curve(x1: number, y1: number, x2: number, y2: number): string {
  const reach = Math.max(36, Math.abs(x2 - x1) / 2)
  return `M ${x1} ${y1} C ${x1 + reach} ${y1}, ${x2 - reach} ${y2}, ${x2} ${y2}`
}

export function GraphCanvas({
  slug,
  nodes,
  edges,
  selected,
  onSelect,
}: {
  slug: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  selected: string | null
  onSelect: (id: string | null) => void
}) {
  const pnodes = useMemo(() => present(nodes), [nodes])
  const byId = useMemo(() => new Map(pnodes.map((p) => [p.id, p])), [pnodes])

  const [pos, setPos] = useState<Map<string, Point>>(() => new Map())
  const [view, setView] = useState({ tx: 0, ty: 0, s: 1 })
  const [panning, setPanning] = useState(false)
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const gesture = useRef<{
    mode: 'pan' | 'node'
    id?: string
    startX: number
    startY: number
    origin: { x: number; y: number }
    moved: boolean
  } | null>(null)
  const frame = useRef<HTMLDivElement>(null)

  const fit = (positions: Map<string, Point>) => {
    if (!frame.current || positions.size === 0) return
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    for (const p of pnodes) {
      const at = positions.get(p.id)
      if (!at) continue
      minX = Math.min(minX, at.x); minY = Math.min(minY, at.y)
      maxX = Math.max(maxX, at.x + p.w); maxY = Math.max(maxY, at.y + p.h)
    }
    const width = frame.current.clientWidth
    const s = Math.min(1, (width - 48) / Math.max(1, maxX - minX), (560 - 40) / Math.max(1, maxY - minY))
    setView({ s, tx: 24 - minX * s, ty: 20 - minY * s })
  }

  // Auto-layout for whatever has no remembered place; remembered places win.
  // The first sight of the graph fits it whole: nothing off-stage, nothing cut.
  useEffect(() => {
    const auto = autoLayout(pnodes, edges)
    const saved = savedLayout(slug)
    const merged = new Map<string, Point>()
    for (const p of pnodes) merged.set(p.id, saved[p.id] ?? auto.get(p.id) ?? { x: 28, y: 28 })
    setPos(merged)
    fit(merged)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, pnodes, edges])

  const persist = (next: Map<string, Point>) => {
    const record: Record<string, Point> = {}
    for (const [id, point] of next) record[id] = point
    localStorage.setItem(layoutKey(slug), JSON.stringify(record))
  }

  const toWorld = (clientX: number, clientY: number) => {
    const rect = frame.current!.getBoundingClientRect()
    return {
      x: (clientX - rect.left - view.tx) / view.s,
      y: (clientY - rect.top - view.ty) / view.s,
    }
  }

  const onPointerDown = (event: ReactPointerEvent<SVGSVGElement>) => {
    const target = (event.target as Element).closest('[data-node]')
    const world = toWorld(event.clientX, event.clientY)
    if (target) {
      const id = target.getAttribute('data-node')!
      const at = pos.get(id) ?? { x: 0, y: 0 }
      gesture.current = {
        mode: 'node',
        id,
        startX: world.x - at.x,
        startY: world.y - at.y,
        origin: { x: event.clientX, y: event.clientY },
        moved: false,
      }
      setDraggingId(id)
    } else {
      gesture.current = {
        mode: 'pan',
        startX: event.clientX - view.tx,
        startY: event.clientY - view.ty,
        origin: { x: event.clientX, y: event.clientY },
        moved: false,
      }
      setPanning(true)
    }
    try {
      event.currentTarget.setPointerCapture(event.pointerId)
    } catch {
      // synthetic events carry pointer ids the platform does not know; the
      // gesture works without capture, capture just makes it smoother
    }
  }

  const onPointerMove = (event: ReactPointerEvent<SVGSVGElement>) => {
    const g = gesture.current
    if (!g) return
    if (Math.abs(event.clientX - g.origin.x) + Math.abs(event.clientY - g.origin.y) > 3) {
      g.moved = true
    }
    if (g.mode === 'pan') {
      setView((v) => ({ ...v, tx: event.clientX - g.startX, ty: event.clientY - g.startY }))
    } else if (g.id) {
      const world = toWorld(event.clientX, event.clientY)
      setPos((prev) => {
        const next = new Map(prev)
        next.set(g.id!, { x: world.x - g.startX, y: world.y - g.startY })
        return next
      })
    }
  }

  const onPointerUp = () => {
    const g = gesture.current
    gesture.current = null
    setPanning(false)
    setDraggingId(null)
    if (!g) return
    if (!g.moved) {
      onSelect(g.mode === 'node' ? (selected === g.id ? null : g.id!) : null)
    } else if (g.mode === 'node') {
      setPos((prev) => {
        persist(prev)
        return prev
      })
    }
  }

  const onWheel = (event: ReactWheelEvent<SVGSVGElement>) => {
    event.preventDefault()
    const factor = Math.exp(-event.deltaY * 0.0015)
    setView((v) => {
      const s = Math.min(2.5, Math.max(0.4, v.s * factor))
      const rect = frame.current!.getBoundingClientRect()
      const cx = event.clientX - rect.left
      const cy = event.clientY - rect.top
      // keep the point under the cursor under the cursor
      return { s, tx: cx - ((cx - v.tx) / v.s) * s, ty: cy - ((cy - v.ty) / v.s) * s }
    })
  }

  // What lights up: the selection and everything one edge away.
  const lit = useMemo(() => {
    if (!selected) return null
    const litEdges = new Set<number>()
    const litNodes = new Set<string>([selected])
    edges.forEach((e, i) => {
      if (e.from === selected || e.to === selected) {
        litEdges.add(i)
        litNodes.add(e.from)
        litNodes.add(e.to)
      }
    })
    return { litEdges, litNodes }
  }, [selected, edges])

  const anchor = (p: PNode, side: 'out' | 'in', otherX: number): Point => {
    const at = pos.get(p.id) ?? { x: 0, y: 0 }
    const cy = at.y + p.h / 2
    if (p.kind === 'chip') return { x: at.x + p.w / 2, y: cy } // chips join centre-on
    const rightward = side === 'out' ? otherX >= at.x + p.w / 2 : otherX > at.x + p.w / 2
    return { x: rightward ? at.x + p.w : at.x, y: cy }
  }

  return (
    <div className="canvas-frame" ref={frame}>
      <svg
        height={560}
        className={panning ? 'panning' : ''}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onWheel={onWheel}
        role="application"
        aria-label="The project as one graph. Drag to arrange; this arranges your view only."
      >
        <g transform={`translate(${view.tx} ${view.ty}) scale(${view.s})`}>
          {edges.map((edge, index) => {
            const from = byId.get(edge.from)
            const to = byId.get(edge.to)
            if (!from || !to || !pos.has(from.id) || !pos.has(to.id)) return null
            const a = anchor(from, 'out', (pos.get(to.id) ?? { x: 0 }).x)
            const b = anchor(to, 'in', (pos.get(from.id) ?? { x: 0 }).x)
            const via = from.kind === 'chip' || to.kind === 'chip'
            const classes = [
              'e',
              via ? 'e-via' : `e-${edge.kind}`,
              lit ? (lit.litEdges.has(index) ? 'lit' : 'faded') : '',
            ]
              .filter(Boolean)
              .join(' ')
            return <path key={index} className={classes} d={curve(a.x, a.y, b.x, b.y)} />
          })}

          {pnodes.map((p) => {
            const at = pos.get(p.id)
            if (!at) return null
            const { node } = p
            const standing =
              node.act !== 'question' &&
              (node.disposition === 'unresolved' || node.disposition === 'contested')
            const groupClass = [
              'n',
              selected === p.id ? 'active' : '',
              lit && !lit.litNodes.has(p.id) ? 'faded' : '',
              draggingId === p.id ? 'dragging' : '',
            ]
              .filter(Boolean)
              .join(' ')

            if (p.kind === 'chip') {
              const reads = relationReads(node.relation) ?? 'relates'
              return (
                <g key={p.id} className={groupClass} data-node={p.id} transform={`translate(${at.x} ${at.y})`}>
                  <rect className="e-chip" width={p.w} height={p.h} rx={p.h / 2} />
                  <text className="e-chip-text" x={p.w / 2} y={p.h / 2 + 3} textAnchor="middle">
                    {reads.length > 16 ? reads.slice(0, 15) + '…' : reads}
                  </text>
                </g>
              )
            }

            const isMaterial = p.kind === 'material' || p.kind === 'occasion'
            const overline =
              p.kind === 'occasion'
                ? occasionOf(node)!
                : p.kind === 'material'
                  ? node.label.startsWith('state:')
                    ? 'material'
                    : node.label.split(':')[0]
                  : READS_AS[node.act ?? ''] ?? node.act ?? ''
            const text =
              isMaterial && node.label.startsWith('state:')
                ? `held · ${node.label.split(':').pop()!.slice(0, 12)}`
                : node.label
            const boxClass = [
              'n-box',
              p.kind === 'occasion' ? 'occasion' : isMaterial ? 'artefact' : '',
              standing ? 'open' : '',
              node.act === 'question' ? 'question' : '',
            ]
              .filter(Boolean)
              .join(' ')

            return (
              <g key={p.id} className={groupClass} data-node={p.id} transform={`translate(${at.x} ${at.y})`}>
                <rect className={boxClass} width={p.w} height={p.h} rx="7" />
                <text className="n-kind" x={11} y={16}>
                  {overline}
                </text>
                {!isMaterial && node.disposition && (
                  <circle
                    className={`n-dot ${node.disposition === 'accepted' ? 'accepted' : ''}`}
                    cx={p.w - 13}
                    cy={12}
                    r={3}
                  />
                )}
                {node.attested && (
                  <text className="n-badge" x={p.w - 24} y={p.h - 8} textAnchor="end">
                    attested
                  </text>
                )}
                {wrap(text, 27, isMaterial ? 1 : 2).map((line, i) => (
                  <text className="n-text" key={i} x={11} y={34 + i * 16}>
                    {line}
                  </text>
                ))}
              </g>
            )
          })}
        </g>
      </svg>

      <div className="canvas-tools">
        <button onClick={() => fit(pos)}>fit</button>
        <button
          onClick={() => {
            localStorage.removeItem(layoutKey(slug))
            const auto = autoLayout(pnodes, edges)
            setPos(new Map(auto))
            fit(auto)
          }}
        >
          tidy
        </button>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------- the tab */

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
  const [selected, setSelected] = useState<string | null>(null)
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

  const selectedNode = selected ? (graph.nodes.find((n) => n.id === selected) ?? null) : null

  return (
    <>
      {mine && (
        <div className="row">
          <button className="quiet" onClick={() => setLinking(true)}>
            record a connection
          </button>
        </div>
      )}

      {graph.nodes.length === 0 ? (
        <div className="note">
          Nothing recorded yet. Open a question, and what follows from it appears here.
        </div>
      ) : (
        <>
          <GraphCanvas
            slug={project.slug}
            nodes={graph.nodes}
            edges={graph.edges}
            selected={selected}
            onSelect={setSelected}
          />
          <div className="legend">
            <span><span className="swatch" /> follows</span>
            <span><span className="swatch crosses" /> crosses between questions</span>
            <span><span className="swatch cites" /> cites material</span>
            <span>drag to arrange — your view only, recorded nowhere</span>
          </div>

          {selectedNode && (
            <NodePanel
              slug={project.slug}
              node={selectedNode}
              project={project}
              mine={mine}
              onClose={() => setSelected(null)}
              onRecorded={(next) => {
                setGraph(next)
                onChanged()
              }}
            />
          )}

          {!selectedNode && (
            <div className="note">
              Select anything — a card, or the small labelled capsule on a line, which is a
              connection: an edge that is itself a recorded act, with its own content and its own
              workspace. Deeper-toned edges cross between questions; material cited from more than
              one line of work appears once, with an edge to each.
            </div>
          )}
        </>
      )}

      <Modal open={linking} title="Record a connection" onClose={() => setLinking(false)}>
        <form onSubmit={connect}>
          <label>
            Made from which question
            <select value={from} onChange={(e) => setFrom(e.target.value)}>
              {project.trajectories.map((t) => (
                <option key={t.trajId} value={t.trajId}>
                  {t.question}
                </option>
              ))}
            </select>
          </label>
          <label>
            What it points at
            <input
              autoFocus
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="a state here, or doi: arxiv: https:…"
              required
            />
          </label>
          <label>
            Why it matters
            <textarea value={why} onChange={(e) => setWhy(e.target.value)} required />
          </label>
          <div className="row">
            <label>
              Relation
              <select value={relation} onChange={(e) => setRelation(e.target.value)}>
                {['relates', 'supports', 'refutes', 'confirms', 'disputes', 'extends', 'repliesTo', 'usesMethodIn', 'usesDataFrom'].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </label>
            <label>
              Occasioned by
              <select value={trigger} onChange={(e) => setTrigger(e.target.value)}>
                {['literature', 'experiment', 'simulation', 'observation', 'discussion', 'objection', 'failure'].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
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
            A connection is an act: recorded, attributed, and it says why the connection matters.
            Relations bind to CiTO rather than to words invented here.
          </div>
        </form>
      </Modal>
    </>
  )
}
