/**
 * The panel under the graph: one node, in full.
 *
 * A panel rather than a modal, because you want it open while you read the
 * graph, and because the space under the drawing was doing nothing.
 *
 * The distinction this panel exists to make legible is the one between the two
 * layers:
 *
 *   **Cited** — artefacts this transition committed to, by the hash of their
 *   bytes, at the moment it was performed. Part of the record. Immutable,
 *   because the transition is (C3).
 *
 *   **Workspace** — an ordinary folder for this node. Applicative. Nothing
 *   signed refers to it, it may be changed at any time, and putting a file
 *   there records nothing.
 *
 * Showing them in one list would be the whole confusion in one screen.
 */

import { useEffect, useRef, useState } from 'react'

import { api, ApiError, type GraphNode, type ProjectFile } from '../api'
import { Markdown } from '../Markdown'

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

const TABS = [
  ['details', 'Details'],
  ['cited', 'Cited'],
  ['workspace', 'Workspace'],
] as const

type Tab = (typeof TABS)[number][0]

function readable(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function NodePanel({
  slug,
  node,
  cited,
  mine,
  onClose,
}: {
  slug: string
  node: GraphNode
  cited: { ref: string; label: string }[]
  mine: boolean
  onClose: () => void
}) {
  const [tab, setTab] = useState<Tab>('details')
  const [files, setFiles] = useState<ProjectFile[] | null>(null)
  const [viewing, setViewing] = useState<{ name: string; text: string } | null>(null)
  const [problem, setProblem] = useState('')
  const [busy, setBusy] = useState(false)
  const picker = useRef<HTMLInputElement>(null)

  const isTransition = node.shape === 'transition'

  const load = () => {
    if (!isTransition) return
    void api
      .nodeFiles(slug, node.id)
      .then((reply) => setFiles(reply.files))
      .catch(() => setFiles([]))
  }

  useEffect(() => {
    setFiles(null)
    setViewing(null)
    load()
  }, [slug, node.id])

  const add = async (chosen: File, folder: string) => {
    setBusy(true)
    setProblem('')
    try {
      const buffer = new Uint8Array(await chosen.arrayBuffer())
      let binary = ''
      for (const byte of buffer) binary += String.fromCharCode(byte)
      const name = folder ? `${folder}/${chosen.name}` : chosen.name
      await api.uploadNodeFile(slug, node.id, name, btoa(binary))
      load()
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
      if (picker.current) picker.current.value = ''
    }
  }

  const remove = async (name: string) => {
    await api.removeNodeFile(slug, node.id, name).catch(() => undefined)
    load()
  }

  const view = async (file: ProjectFile) => {
    const reply = await fetch(api.nodeFileUrl(slug, node.id, file.name))
    setViewing({ name: file.name, text: await reply.text() })
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <strong>
          {isTransition ? READS_AS[node.act ?? ''] ?? node.act : 'material — cited, not recorded'}
        </strong>
        <div className="tabs panel-tabs">
          {isTransition &&
            TABS.map(([key, label]) => (
              <button
                key={key}
                className={key === tab ? 'tab on' : 'tab'}
                onClick={() => setTab(key)}
              >
                {label}
              </button>
            ))}
        </div>
        <button className="quiet" onClick={onClose} aria-label="close">
          ×
        </button>
      </div>

      {(!isTransition || tab === 'details') && (
        <>
          {node.label && <Markdown source={node.label} />}
          <dl className="facts">
            {isTransition && (
              <>
                <dt>act</dt>
                <dd>{node.act}</dd>
                <dt>disposition</dt>
                <dd>{node.disposition}</dd>
                <dt>occasioned by</dt>
                <dd>{node.trigger ?? '—'}</dd>
                <dt>registration</dt>
                <dd>
                  {node.attested
                    ? 'attested — registered by a party other than the performer'
                    : 'unattested — registered by the party who performed it'}
                </dd>
                <dt>performed</dt>
                <dd>{node.performed.replace('T', ' ').replace('Z', ' UTC')}</dd>
              </>
            )}
            {node.question && (
              <>
                <dt>under</dt>
                <dd>{node.question}</dd>
              </>
            )}
            <dt>identifier</dt>
            <dd className="id">{node.id}</dd>
          </dl>
        </>
      )}

      {isTransition && tab === 'cited' && (
        <>
          {cited.length === 0 ? (
            <div className="note">
              This transition cites nothing. Material becomes part of the record when a transition
              commits to it by hash — which is an act, performed deliberately.
            </div>
          ) : (
            cited.map((artefact) => (
              <div className="card" key={artefact.ref}>
                <div className="meta">{artefact.label}</div>
                <div className="meta id">{artefact.ref}</div>
              </div>
            ))
          )}
          <div className="note">
            Cited material is committed to by the hash of its bytes, at the moment this transition
            was performed. It cannot change afterwards: the transition is never edited (C3), and a
            hash that no longer matches is how you find out.
          </div>
        </>
      )}

      {isTransition && tab === 'workspace' && (
        <>
          {files === null ? (
            <div className="note">reading…</div>
          ) : files.length === 0 ? (
            <div className="note">Nothing here yet.</div>
          ) : (
            files.map((file) => (
              <div className="card" key={file.name}>
                <div className="row">
                  <button className="quiet link" onClick={() => void view(file)}>
                    {file.name}
                  </button>
                  <span className="meta">{readable(file.size)}</span>
                  {mine && (
                    <button className="quiet" onClick={() => void remove(file.name)}>
                      remove
                    </button>
                  )}
                </div>
                <div className="meta id" title="what a transition would cite">
                  {file.digest}
                </div>
              </div>
            ))
          )}

          {viewing && (
            <div className="card">
              <div className="meta">{viewing.name}</div>
              {/^.+\.(md|markdown)$/i.test(viewing.name) ? (
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
                  const folder = (
                    document.getElementById('workspace-folder') as HTMLInputElement | null
                  )?.value?.trim()
                  if (chosen) void add(chosen, folder ?? '')
                }}
              />
              <input id="workspace-folder" type="text" placeholder="folder — optional" />
            </div>
          )}
          {problem && <p className="warn">{problem}</p>}

          <div className="note">
            This workspace is <strong>yours and is not the record</strong>. Nothing signed refers to
            it, you may change or remove anything in it, and putting a file here records nothing.
            <br />
            <br />
            It travels when the project directory is copied, and <em>not</em> in a bundle — a bundle
            carries transitions, states and questions. What travels of a cited artefact is its hash.
          </div>
        </>
      )}
    </section>
  )
}
