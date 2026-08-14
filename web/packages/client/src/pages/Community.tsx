/**
 * What people on this server have shared.
 *
 * Not "the community" in the sense of a directory of everyone doing this kind
 * of work — no such directory exists, and building one is what the design
 * refuses. This is the records on *this* host whose holders chose to list
 * them, which is a much smaller and much more honest claim.
 */

import { useEffect, useState } from 'react'

import { api, type Me, type Project } from '../api'
import { RecordList } from './RecordList'

export function Community({ me }: { me: Me }) {
  const [projects, setProjects] = useState<Project[] | null>(null)

  useEffect(() => {
    void api.projects().then((reply) => setProjects(reply.projects))
  }, [])

  const shared = (projects ?? []).filter((project) => project.disclosure === 'listed')

  return (
    <>
      <header>
        <h1>Shared here</h1>
        <p className="lede">
          Records on this server that their holders have chosen to list. Listed by name, and by
          nothing else: no ordering by activity, size or recency, because an ordering would tell
          you which of these matters before you had read any of them.
        </p>
      </header>

      <h2>Records</h2>
      <RecordList
        projects={shared}
        empty={
          projects === null
            ? 'reading…'
            : 'Nobody has shared a record on this server yet. Yours are on “Your records”, and stay unlisted until you widen them.'
        }
      />

      <div className="note">
        There is no directory of other people's work here, and there is not going to be one. A
        service that knew where everyone's records were would be party to every entry, and what
        makes a record credible is registration by parties who did not coordinate. Work reaches you
        because somebody chose to hand it to you.
      </div>

      <div className="note">
        You are one of the parties here, as <span className="id">{me.party}</span>. Nothing on this
        page counts what you have done, and nothing compares it with anyone else.
      </div>
    </>
  )
}
