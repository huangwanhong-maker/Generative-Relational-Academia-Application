/**
 * The substrate's history. **Development only.**
 *
 * A commit is not a transition, and this component exists to debug the thing
 * rather than to use it. git supplies append-only history and the transport by
 * which a complete record is copied elsewhere; it supplies none of the
 * meaning. The record is the YAML and the state files, the identifiers are
 * hashes of their bytes, and a record in a directory that was never a
 * repository is exactly as valid as one in a repository.
 *
 * Shown behind a button, labelled, and absent in production — because an
 * interface that put commits beside transitions would teach that git is where
 * the meaning lives, and then somebody would start reading the commit log to
 * find out what happened.
 */

import { useState } from 'react'

import { api, ApiError, type Commit } from '../api'

export function GitHistory({ slug }: { slug: string }) {
  const [shown, setShown] = useState(false)
  const [commits, setCommits] = useState<Commit[] | null>(null)
  const [note, setNote] = useState('')

  const reveal = async () => {
    setShown(true)
    try {
      const reply = await api.gitHistory(slug)
      setCommits(reply.commits)
      setNote(reply.note ?? '')
    } catch (error) {
      setCommits([])
      setNote(error instanceof ApiError ? error.message : String(error))
    }
  }

  if (!shown) {
    return (
      <>
        <h2>Underneath — development only</h2>
        <button className="quiet" onClick={reveal}>
          show the git history
        </button>
        <div className="meta">
          The substrate, not the record. Absent in production.
        </div>
      </>
    )
  }

  return (
    <>
      <h2>Underneath — development only</h2>
      <div className="note">
        <strong>A commit is not a transition.</strong> git gives this project append-only history
        and a way to be copied elsewhere. It gives it no meaning: the record is the YAML and the
        state files, every identifier is the hash of some bytes, and a record in a directory that
        was never a repository is exactly as valid. Nothing here is part of what anybody recorded.
      </div>

      {note && <div className="note warn">{note}</div>}

      {commits === null && <div className="note">reading…</div>}

      {commits?.map((commit) => (
        <div className="card" key={commit.hash}>
          <div className="meta">{commit.subject}</div>
          <div className="meta id">
            {commit.hash.slice(0, 12)} · {commit.when.slice(0, 19).replace('T', ' ')}
          </div>
        </div>
      ))}

      <button className="quiet" onClick={() => setShown(false)}>
        hide
      </button>
    </>
  )
}
