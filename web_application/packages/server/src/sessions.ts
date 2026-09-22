/**
 * Who is signed in, in memory, for as long as the process runs.
 *
 * In memory and not in the database, deliberately. A session table is a log of
 * who was here and when, which is precisely the monitoring by-product this
 * design goes out of its way not to accumulate -- the same reason the event
 * plane is never exported. Restarting the server signs everybody out. That is
 * the correct trade, and it is cheap to pay.
 *
 * The cookie holds an opaque ticket and nothing else: never the name, never
 * the key, never anything derived from either.
 */

import { randomBytes } from 'node:crypto'

export const COOKIE = 'gra_session'

export interface Session {
  userId: number
  name: string
  party: string
  since: number
}

export class Sessions {
  private readonly open = new Map<string, Session>()

  /** How long a ticket survives without being used. */
  constructor(private readonly idleMs = 1000 * 60 * 60 * 12) {}

  begin(session: Omit<Session, 'since'>): string {
    const ticket = randomBytes(24).toString('base64url')
    this.open.set(ticket, { ...session, since: Date.now() })
    return ticket
  }

  get(ticket: string | undefined): Session | null {
    if (!ticket) return null
    const session = this.open.get(ticket)
    if (!session) return null
    if (Date.now() - session.since > this.idleMs) {
      this.open.delete(ticket)
      return null
    }
    session.since = Date.now()
    return session
  }

  end(ticket: string | undefined): void {
    if (ticket) this.open.delete(ticket)
  }

  /** Sign out every session of one account, on a password change. */
  endAllFor(userId: number): void {
    for (const [ticket, session] of this.open) {
      if (session.userId === userId) this.open.delete(ticket)
    }
  }

  get size(): number {
    return this.open.size
  }
}
