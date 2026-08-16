/**
 * Search, which filters and does not rank.
 *
 * No relevance ordering, no "best match", no score, and no highlighting of one
 * result over another. Matches appear in the same order everything else does,
 * because an ordering by relevance is a measure over trajectories — and this
 * is the single place a reader would most readily believe a number.
 */

import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { api, type Hit, type Me } from '../api'

/** Show where the word occurs. Marking a match is not scoring it. */
function highlight(text: string, needle: string): ReactNode {
  if (!needle) return text
  const parts = text.split(new RegExp(`(${needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'ig'))
  return parts.map((part, index) =>
    part.toLowerCase() === needle.toLowerCase() ? <mark key={index}>{part}</mark> : part,
  )
}

export function SearchPage({ me }: { me: Me }) {
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const [draft, setDraft] = useState(query)
  const [hits, setHits] = useState<Hit[] | null>(null)
  const [ordering, setOrdering] = useState('')

  const run = async (text: string) => {
    if (!text.trim()) {
      setHits(null)
      return
    }
    const reply = await api.search(text)
    setHits(reply.hits)
    setOrdering(reply.ordering)
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    setParams(draft ? { q: draft } : {})
    void run(draft)
  }

  return (
    <>
      <header>
        <h1>Search</h1>
        <p className="lede">
          {me.signedIn
            ? 'Across the projects you can see: your own, and the ones shared on this server.'
            : 'Across the projects shared on this server. No account needed to read them.'}
        </p>
      </header>

      <form className="searchbar" onSubmit={submit}>
        <input
          autoFocus
          value={draft}
          placeholder="questions, positions, objections…"
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit">search</button>
      </form>

      {hits !== null && (
        <>
          <h2>{hits.length ? `Matches for “${query}”` : `Nothing mentions “${query}”`}</h2>
          {hits.map((hit) => (
            <div className="card" key={`${hit.slug}:${hit.trajId}`}>
              <Link to={`/r/${hit.slug}`}>
                <strong>{highlight(hit.question, query)}</strong>
              </Link>
              <div className="meta">
                {hit.slug} · matched in {hit.where}
              </div>
              <div className="meta">{highlight(hit.snippet, query)}</div>
            </div>
          ))}
          {ordering && <p className="meta">Ordered {ordering}.</p>}
        </>
      )}

      {hits === null && (
        <p className="meta hint">Search filters; it does not rank.</p>
      )}
    </>
  )
}
