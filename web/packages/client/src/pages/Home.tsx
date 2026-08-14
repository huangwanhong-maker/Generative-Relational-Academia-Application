/**
 * The front page, and it is public.
 *
 * What GRA is, a search box that works signed out, and the projects people
 * here have shared. No account required to read any of it.
 *
 * What is deliberately absent: any ordering of the projects by activity,
 * size, recency or interest. They are listed by name. A front page that
 * ordered them would be telling you which mattered before you had read one,
 * and a measure adopted to direct attention becomes the thing people work
 * towards (C6).
 */

import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, type Me, type Project } from '../api'
import { ProjectList } from './ProjectList'

export function Home({ me }: { me: Me }) {
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [draft, setDraft] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    void api
      .projects()
      .then((reply) => setProjects(reply.projects.filter((p) => p.disclosure === 'listed')))
      .catch(() => setProjects([]))
  }, [])

  const search = (event: FormEvent) => {
    event.preventDefault()
    if (draft.trim()) navigate(`/search?q=${encodeURIComponent(draft)}`)
  }

  return (
    <>
      <header>
        <h1>Generative Relational Academia</h1>
        <p className="lede">
          A place to record how an understanding changed — the question somebody was actually
          trying to answer, the position they took, the objection nobody has answered yet — and to
          hand that record to someone else intact.
        </p>
        <p className="lede">
          Not a publication venue and not a metrics dashboard. What is recorded here is the
          movement of an argument, including the parts that did not resolve.
        </p>
      </header>

      <form className="searchbar" onSubmit={search}>
        <input
          value={draft}
          placeholder="Search shared projects — questions, positions, objections…"
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit">search</button>
      </form>

      <h2>Projects shared on this server</h2>
      <ProjectList
        projects={projects ?? []}
        empty={
          projects === null
            ? 'reading…'
            : 'Nobody has shared a project on this server yet. Projects stay unlisted until their holder widens them.'
        }
      />

      {me.signedIn ? (
        <div className="note">
          Your own projects — shared or not — are on{' '}
          <Link to="/projects">
            <strong>Your projects</strong>
          </Link>
          .
        </div>
      ) : (
        <div className="note">
          You are reading this signed out, which is the intended way to read it. An account is
          needed only to open a project of your own. Registration is closed on this server; that is
          a property of this host and not a gate on taking part, because the record is plain files
          that anyone may hold, continue and verify without asking.
        </div>
      )}

      <div className="note">
        This lists projects on <em>this</em> server. There is no directory of other people's work
        anywhere here, and there is not going to be one: a service that knew where everyone's
        records were would be party to every entry, and what makes a record credible is
        registration by parties who did not coordinate.
      </div>
    </>
  )
}
