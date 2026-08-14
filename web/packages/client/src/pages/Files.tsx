/**
 * A project's working material: data, drafts, figures, notes.
 *
 * **Putting a file here records nothing.** No transition is written and no
 * identifier is minted — C1 is explicit that no operation exists merely so
 * that a record exists, and a file arriving in a directory is not a change in
 * anybody's understanding.
 *
 * What makes a file part of the record is a transition citing it, by the hash
 * of its bytes. The hash is shown for that reason and no other: it is what a
 * transition would reference, and what a reader elsewhere would check. The
 * page says so plainly rather than letting an upload feel like an act.
 */

import { useEffect, useRef, useState } from 'react'

import { api, ApiError, type Me, type Project, type ProjectFile } from '../api'

function readable(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function Files({ project, me }: { project: Project; me: Me }) {
  const [files, setFiles] = useState<ProjectFile[] | null>(null)
  const [problem, setProblem] = useState('')
  const [said, setSaid] = useState('')
  const [busy, setBusy] = useState(false)
  const picker = useRef<HTMLInputElement>(null)

  const mine = me.signedIn && project.openedBy === me.party

  const load = () => {
    void api
      .files(project.slug)
      .then((reply) => setFiles(reply.files))
      .catch(() => setFiles([]))
  }

  useEffect(load, [project.slug])

  const add = async (chosen: File) => {
    setBusy(true)
    setProblem('')
    setSaid('')
    try {
      const buffer = new Uint8Array(await chosen.arrayBuffer())
      let binary = ''
      for (const byte of buffer) binary += String.fromCharCode(byte)
      const stored = await api.upload(project.slug, chosen.name, btoa(binary))
      setSaid(stored.note)
      load()
    } catch (error) {
      setProblem(error instanceof ApiError ? error.message : String(error))
    } finally {
      setBusy(false)
      if (picker.current) picker.current.value = ''
    }
  }

  return (
    <>
      <h2>Material</h2>
      {files === null ? (
        <div className="note">reading…</div>
      ) : files.length === 0 ? (
        <div className="note">Nothing here yet.</div>
      ) : (
        files.map((file) => (
          <div className="card" key={file.name}>
            <a href={api.fileUrl(project.slug, file.name)} target="_blank" rel="noreferrer">
              <strong>{file.name}</strong>
            </a>
            <div className="meta">{readable(file.size)}</div>
            <div className="meta id" title="what a transition would cite">
              {file.digest}
            </div>
          </div>
        ))
      )}

      {mine && (
        <>
          <h2>Add material</h2>
          <input
            ref={picker}
            type="file"
            disabled={busy}
            onChange={(event) => {
              const chosen = event.target.files?.[0]
              if (chosen) void add(chosen)
            }}
          />
          {problem && <p className="warn">{problem}</p>}
          {said && <p className="meta">{said}</p>}
        </>
      )}

      <div className="note">
        Adding a file here <strong>records nothing</strong>. Nothing enters the log, no identifier
        is minted, and nobody is credited. This is material, and material is not evidence.
        <br />
        <br />
        A file becomes part of the record when a transition cites it — by the hash shown above,
        through the artefact field the transition skeleton already carries. That is an act somebody
        performs deliberately, and it is done with <span className="id">grrp connect</span> against
        the files. Bringing it to this page is on the list.
      </div>
    </>
  )
}
