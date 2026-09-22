/**
 * The subject panel: one node — or one reified edge — in full.
 *
 * Four components, per spec §5, one per storage class:
 *
 *   Record      the signed payload and the words. grrp wrote it; nothing here
 *               can. Counts appear here and only here (the C6 carve-out,
 *               scoped to the selected subject).
 *   Disclosure  what is restricted, on which ground, with what residue.
 *               Widens only; there is no unpublish.
 *   Workspace   an ordinary folder on this subject. Mutable, shared with the
 *               project, never in a bundle. Records nothing.
 *   Calendar    occasions only. Local plane: this machine, this viewer,
 *               exported to nobody. The schema has no attendee field.
 *
 * Below the head, the acts row: recording is why the page exists. Each button
 * is one grrp invocation with a form in front of it, and grrp's refusal is
 * shown verbatim.
 */

import { useEffect, useRef, useState, type FormEvent } from 'react'

import { api, ApiError, type GraphEdge, type GraphNode, type Project, type ProjectFile } from '../api'
import { Markdown } from '../Markdown'
import { Modal } from '../Modal'
import { READS_AS, occasionOf, relationReads } from './Trajectories'

type Tab = 'record' | 'disclosure' | 'workspace' | 'calendar'

const TARGETS = ['question', 'assumption', 'hypothesis', 'concept', 'theory', 'method', 'path', 'artefact']
const TRIGGERS = ['self', 'literature', 'experiment', 'simulation', 'observation', 'discussion', 'objection', 'failure']
// The last two are charter-locals: lawful, stored as local:, and never to be
// presented as CiTO-bound (C12) — so the picker says so.
const RELATIONS: [string, string][] = [
  ['modifies', 'modifies'],
  ['refines', 'refines'],
  ['replaces', 'replaces'],
  ['extends', 'extends'],
  ['generalises', 'generalises — local, defined by charter'],
  ['specialises', 'specialises — local, defined by charter'],
]

function short(key: string | null): string {
  if (!key) return '—'
  const tail = key.split(':').pop() ?? key
  return `${tail.slice(0, 10)}…`
}

function readable(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/* --------------------------------------------------------------- act dialogs */

interface ActShape {
  act: string
  title: string
  hint: string
  message?: false
  target?: boolean
  trigger?: boolean
  relation?: boolean
  failed?: boolean
  abandon?: boolean
}

const ACT_SHAPES: ActShape[] = [
  { act: 'claim', title: 'Take a position', hint: 'What you currently think, so that when it changes you can see what changed it.', target: true, trigger: true },
  { act: 'challenge', title: 'Object', hint: 'It stands until something answers it — and it may lawfully stand forever.', target: true, trigger: true },
  { act: 'transform', title: 'Change it', hint: 'What it becomes, and what moved you.', relation: true, trigger: true },
  { act: 'decide', title: 'Decide', hint: 'A decision recorded without a reason cannot be revisited by anyone, including you.', abandon: true },
  { act: 'verify', title: 'Check', hint: 'A check that did not come out joins what is unanswered.', failed: true, trigger: true },
  { act: 'release', title: 'Release', hint: 'Publishes this state, enumerating the objections standing against it. It asserts nothing about their merit.', message: false },
]

function ActDialog({
  shape,
  slug,
  node,
  onClose,
  onRecorded,
}: {
  shape: ActShape
  slug: string
  node: GraphNode
  onClose: () => void
  onRecorded: (graph: { nodes: GraphNode[]; edges: GraphEdge[] }) => void
}) {
  const [message, setMessage] = useState('')
  const [target, setTarget] = useState(shape.act === 'challenge' ? 'assumption' : 'hypothesis')
  const [trigger, setTrigger] = useState(shape.act === 'verify' ? 'experiment' : 'self')
  const [relation, setRelation] = useState('modifies')
  const [failed, setFailed] = useState(false)
  const [abandon, setAbandon] = useState(false)
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setProblem('')
    try {
      const graph = await api.act(slug, {
        act: shape.act,
        traj: node.trajId ?? '',
        state: node.posteriorState?.split(':').pop() ?? '',
        message,
        ...(shape.target ? { target } : {}),
        ...(shape.trigger ? { trigger } : {}),
        ...(shape.relation ? { relation } : {}),
        ...(shape.failed ? { failed } : {}),
        ...(shape.abandon ? { abandon } : {}),
      })
      onRecorded(graph)
      onClose()
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open title={shape.title} onClose={onClose}>
      <form onSubmit={submit}>
        <p className="meta">On: <em>{node.label || node.id}</em></p>
        {shape.message !== false && (
          <label>
            {shape.act === 'claim' ? 'The position' : shape.act === 'challenge' ? 'The objection' : shape.act === 'transform' ? 'What it becomes' : shape.act === 'decide' ? 'The reason' : 'The outcome'}
            <textarea autoFocus value={message} onChange={(e) => setMessage(e.target.value)} required />
          </label>
        )}
        <div className="row">
          {shape.target && (
            <label>
              About the
              <select value={target} onChange={(e) => setTarget(e.target.value)}>
                {TARGETS.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </label>
          )}
          {shape.relation && (
            <label>
              Relation
              <select value={relation} onChange={(e) => setRelation(e.target.value)}>
                {RELATIONS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
              </select>
            </label>
          )}
          {shape.trigger && (
            <label>
              Occasioned by
              <select value={trigger} onChange={(e) => setTrigger(e.target.value)}>
                {TRIGGERS.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </label>
          )}
        </div>
        {shape.failed && (
          <label className="row" style={{ display: 'flex' }}>
            <input type="checkbox" style={{ width: 'auto' }} checked={failed} onChange={(e) => setFailed(e.target.checked)} />
            <span>it did not come out as predicted — it will stand as unresolved</span>
          </label>
        )}
        {shape.abandon && (
          <label className="row" style={{ display: 'flex' }}>
            <input type="checkbox" style={{ width: 'auto' }} checked={abandon} onChange={(e) => setAbandon(e.target.checked)} />
            <span>retire this direction rather than continue it</span>
          </label>
        )}
        {problem && <p className="warn">{problem}</p>}
        <div className="row">
          <button type="submit" disabled={busy}>{busy ? 'recording…' : 'record it'}</button>
          <button type="button" className="quiet" onClick={onClose}>cancel</button>
        </div>
        <div className="meta">{shape.hint}</div>
      </form>
    </Modal>
  )
}

/* ---------------------------------------------------------- calendar (local) */

interface CalEntry {
  subject: string
  title: string
  when: string
  where: string
  link: string
}

function calKey(slug: string) {
  return `gra:cal:${slug}`
}

function readCal(slug: string): CalEntry[] {
  try {
    return JSON.parse(localStorage.getItem(calKey(slug)) ?? '[]')
  } catch {
    return []
  }
}

function CalendarTab({ slug, subject, suggested }: { slug: string; subject: string; suggested: string }) {
  const [entries, setEntries] = useState<CalEntry[]>(() => readCal(slug))
  const mine = entries.find((e) => e.subject === subject)
  const [title, setTitle] = useState(mine?.title ?? suggested)
  const [when, setWhen] = useState(mine?.when ?? '')
  const [where, setWhere] = useState(mine?.where ?? '')
  const [link, setLink] = useState(mine?.link ?? '')

  const save = (event: FormEvent) => {
    event.preventDefault()
    const next = [...entries.filter((e) => e.subject !== subject), { subject, title, when, where, link }]
    localStorage.setItem(calKey(slug), JSON.stringify(next))
    setEntries(next)
  }

  return (
    <>
      <form onSubmit={save}>
        <div className="row">
          <label>Title<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <label>When<input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} /></label>
        </div>
        <div className="row">
          <label>Where<input value={where} onChange={(e) => setWhere(e.target.value)} /></label>
          <label>Link<input value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://…" /></label>
        </div>
        <div className="row">
          <button type="submit" className="quiet">add to calendar</button>
          {(mine?.link || link) && (
            <button
              type="button"
              onClick={() => window.open(mine?.link || link, '_blank', 'noreferrer noopener')}
            >
              join
            </button>
          )}
        </div>
      </form>
      <p className="meta">This machine only, never exported. Joining writes nothing.</p>
    </>
  )
}

/* ---------------------------------------------------------------- the panel */

export function NodePanel({
  slug,
  node,
  project,
  mine,
  onClose,
  onRecorded,
}: {
  slug: string
  node: GraphNode
  project: Project
  mine: boolean
  onClose: () => void
  onRecorded: (graph: { nodes: GraphNode[]; edges: GraphEdge[] }) => void
}) {
  const isTransition = node.shape === 'transition'
  const occasion = occasionOf(node)
  const holdsWorkspace = isTransition || node.label.startsWith('state:')
  const [tab, setTab] = useState<Tab>('record')
  const [acting, setActing] = useState<ActShape | null>(null)

  const [files, setFiles] = useState<ProjectFile[] | null>(null)
  const [viewing, setViewing] = useState<{ name: string; text: string } | null>(null)
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)
  const picker = useRef<HTMLInputElement>(null)

  const loadFiles = () => {
    if (!holdsWorkspace) return
    void api
      .nodeFiles(slug, node.id)
      .then((reply) => setFiles(reply.files))
      .catch(() => setFiles([]))
  }

  useEffect(() => {
    setTab('record')
    setFiles(null)
    setViewing(null)
    loadFiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, node.id])

  const addFile = async (chosen: File, folder: string) => {
    setBusy(true)
    setProblem('')
    try {
      const buffer = new Uint8Array(await chosen.arrayBuffer())
      let binary = ''
      for (const byte of buffer) binary += String.fromCharCode(byte)
      const name = folder ? `${folder}/${chosen.name}` : chosen.name
      await api.uploadNodeFile(slug, node.id, name, btoa(binary))
      loadFiles()
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
      if (picker.current) picker.current.value = ''
    }
  }

  const heading = isTransition
    ? node.act === 'connection'
      ? `connection · ${relationReads(node.relation) ?? 'relates'}`
      : READS_AS[node.act ?? ''] ?? node.act
    : occasion
      ? `occasion · ${occasion}`
      : 'material — cited, not recorded'

  const line = node.trajId ? project.trajectories.find((t) => t.trajId === node.trajId) : null
  const timesDiffer =
    node.registeredAt && node.performed && node.registeredAt.slice(0, 16) !== node.performed.slice(0, 16)

  const tabs: [Tab, string][] = [
    ['record', 'Record'],
    ['disclosure', 'Disclosure'],
    ...(holdsWorkspace ? ([['workspace', 'Workspace']] as [Tab, string][]) : []),
    ...(occasion ? ([['calendar', 'Calendar']] as [Tab, string][]) : []),
  ]

  return (
    <section className="panel">
      <div className="panel-head">
        <strong>{heading}</strong>
        <div className="tabs panel-tabs">
          {tabs.map(([key, label]) => (
            <button key={key} className={key === tab ? 'tab on' : 'tab'} onClick={() => setTab(key)}>
              {label}
            </button>
          ))}
        </div>
        <button className="quiet" onClick={onClose} aria-label="close">×</button>
      </div>

      {tab === 'record' && (
        <>
          {node.body ? <Markdown source={node.body} /> : node.label && <p className="body">{node.label}</p>}

          <dl className="facts">
            {isTransition && (
              <>
                <dt>act</dt>
                <dd>{READS_AS[node.act ?? '']} <span className="id">{node.act}</span></dd>
                {node.target && (<><dt>about the</dt><dd>{node.target}</dd></>)}
                {node.relation && (
                  <><dt>relation</dt><dd>{relationReads(node.relation)} <span className="id">{node.relation}</span></dd></>
                )}
                <dt>occasioned by</dt>
                <dd>{node.trigger ?? '—'}</dd>
                <dt>disposition</dt>
                <dd>{node.disposition}</dd>
                <dt>performed</dt>
                <dd>
                  <span className="id" title={node.performer ?? ''}>{short(node.performer)}</span>{' '}
                  · {node.performed.replace('T', ' ').replace('Z', ' UTC')}
                </dd>
                <dt>registration</dt>
                <dd>
                  {node.attested
                    ? <>attested — registered by <span className="id">{short(node.registrar)}</span>, a party other than the performer. Witnessing, not approval: it says nothing about the content.</>
                    : 'unattested — registered by the party who performed it'}
                  {timesDiffer && <> · registered {node.registeredAt!.replace('T', ' ').replace('Z', ' UTC')}</>}
                </dd>
              </>
            )}
            {node.question && (<><dt>under</dt><dd>{node.question}</dd></>)}
            {node.cited.length > 0 && (
              <>
                <dt>cites</dt>
                <dd>{node.cited.map((c) => <div key={c.ref} className="id">{c.label} · {c.ref}</div>)}</dd>
              </>
            )}
            {occasion && (
              <>
                <dt>read as</dt>
                <dd>{occasion} — derived from what cites it</dd>
              </>
            )}
            {node.act === 'question' && line && (
              <>
                <dt>this line of work</dt>
                <dd>
                  {line.transitionCount} transition{line.transitionCount === 1 ? '' : 's'}
                  {line.openCount > 0 && <> · <span className="open-mark">{line.openCount} standing unanswered</span></>}
                  <div className="meta">within this line of work</div>
                </dd>
              </>
            )}
            <dt>identifier</dt>
            <dd className="id">{node.id}</dd>
          </dl>

          {mine && isTransition && (
            <div className="acts-row">
              {ACT_SHAPES.map((shape) => (
                <button key={shape.act} onClick={() => setActing(shape)}>{shape.title}</button>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'disclosure' && (
        <>
          <p className="meta">
            <strong>Not yet wired to the sidecar</strong> — this view makes no claim about
            restrictions, either way. They are recorded with{' '}
            <span className="id">grrp disclose</span> and <span className="id">grrp redact</span>.
          </p>
          <p className="meta">Disclosure widens; it never narrows.</p>
        </>
      )}

      {tab === 'workspace' && holdsWorkspace && (
        <>
          {files === null ? (
            <div className="note">reading…</div>
          ) : files.length === 0 ? (
            <div className="note">Nothing here yet.</div>
          ) : (
            files.map((file) => (
              <div className="card" key={file.name}>
                <div className="row">
                  <button
                    className="quiet link"
                    onClick={() =>
                      void fetch(api.nodeFileUrl(slug, node.id, file.name))
                        .then((r) => r.text())
                        .then((text) => setViewing({ name: file.name, text }))
                    }
                  >
                    {file.name}
                  </button>
                  <span className="meta">{readable(file.size)}</span>
                  {mine && (
                    <button
                      className="quiet"
                      onClick={() => void api.removeNodeFile(slug, node.id, file.name).catch(() => undefined).then(loadFiles)}
                    >
                      remove
                    </button>
                  )}
                </div>
                <div className="meta id" title="what a transition would cite">{file.digest}</div>
              </div>
            ))
          )}

          {viewing && (
            <div className="card">
              <div className="meta">{viewing.name}</div>
              {/\.(md|markdown)$/i.test(viewing.name) ? (
                <Markdown source={viewing.text} />
              ) : (
                <pre className="body">{viewing.text.slice(0, 20000)}</pre>
              )}
            </div>
          )}

          {mine && (
            <div className="row">
              <input
                ref={picker}
                type="file"
                disabled={busy}
                onChange={(event) => {
                  const chosen = event.target.files?.[0]
                  const folder = (document.getElementById('ws-folder') as HTMLInputElement | null)?.value?.trim()
                  if (chosen) void addFile(chosen, folder ?? '')
                }}
              />
              <input id="ws-folder" type="text" placeholder="folder — optional" style={{ maxWidth: '12rem' }} />
            </div>
          )}
          {problem && <p className="warn">{problem}</p>}

          <p className="meta">
            Shared scratch, never bundled. <strong>Adding a file records nothing</strong> — it
            joins the record when an act cites its digest.
          </p>
        </>
      )}

      {tab === 'calendar' && occasion && (
        <CalendarTab slug={slug} subject={node.id} suggested={occasion} />
      )}

      {acting && (
        <ActDialog
          shape={acting}
          slug={slug}
          node={node}
          onClose={() => setActing(null)}
          onRecorded={onRecorded}
        />
      )}
    </section>
  )
}
