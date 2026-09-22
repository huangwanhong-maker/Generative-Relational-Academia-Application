/**
 * The index over the records, and the search across it.
 *
 * `reindex` is the load-bearing function: it drops everything derived and
 * rebuilds it from the files. If it cannot, something has become
 * authoritative that should not be.
 */

import { and, eq, like, or } from 'drizzle-orm'

import type { Db } from './database.js'
import { projects, searchText, trajectories, users } from './db.js'
import { listRecordSlugs, readHostFacts, readProject, writeHostFacts } from './records.js'

export interface Listed {
  slug: string
  title: string
  /** What the project says about itself. A README, not a database column. */
  description: string
  openedBy: string
  /**
   * The account name behind that key, when this host knows one.
   *
   * A convenience for reading, never an identifier: the party is the key. A
   * project opened by someone with no account here still shows its key, which
   * is the honest answer rather than "unknown".
   */
  openedByName: string | null
  tier: string
  disclosure: string
  openedAt: string
  trajectories: {
    trajId: string
    title: string | null
    question: string
    transitionCount: number
    openCount: number
  }[]
}

/**
 * Rebuild the whole index from the files.
 *
 * Cheap enough to run at boot. The point is not performance, it is that the
 * database can be deleted at any moment without losing anything, which is what
 * keeps it from being the system of record (C11).
 */
export async function reindex(db: Db, root: string): Promise<number> {
  const now = new Date().toISOString()
  const seen: string[] = []

  for (const slug of listRecordSlugs(root)) {
    const onDisk = readProject(root, slug)
    if (!onDisk) continue
    seen.push(slug)

    const [existing] = await db.select().from(projects).where(eq(projects.slug, slug)).limit(1)
    // Host facts come from the sidecar, not from the database, so that
    // deleting the database costs a rebuild and nothing else. A record with no
    // sidecar -- one dropped into the directory by hand -- is private and
    // attributed to the party in its own profile, which is the cautious
    // reading and the only one available.
    const host = readHostFacts(root, slug)

    const row = {
      slug,
      title: onDisk.title,
      description: onDisk.description,
      openedBy: host?.openedBy ?? onDisk.openedBy,
      tier: onDisk.tier,
      disclosure: host?.disclosure ?? existing?.disclosure ?? 'private',
      openedAt: onDisk.openedAt,
      indexedAt: now,
    }
    const projectId = existing
      ? (await db.update(projects).set(row).where(eq(projects.id, existing.id)).returning())[0]!.id
      : (await db.insert(projects).values(row).returning())[0]!.id

    await db.delete(trajectories).where(eq(trajectories.projectId, projectId))
    await db.delete(searchText).where(eq(searchText.projectId, projectId))

    for (const trajectory of onDisk.trajectories) {
      await db.insert(trajectories).values({
        projectId,
        trajId: trajectory.trajId,
        title: trajectory.title,
        question: trajectory.question,
        transitionCount: trajectory.transitionCount,
        openCount: trajectory.openCount,
        openedAt: trajectory.openedAt,
      })
      if (trajectory.states.length) {
        await db.insert(searchText).values(
          trajectory.states.map((state) => ({
            projectId,
            trajId: trajectory.trajId,
            stateId: state.stateId,
            kind: state.kind,
            body: state.body,
          })),
        )
      }
    }
  }

  // Records removed from disk leave the index. Nothing is deleted from any
  // record here -- this only forgets what is no longer there to be seen.
  for (const row of await db.select().from(projects)) {
    if (!seen.includes(row.slug)) await db.delete(projects).where(eq(projects.id, row.id))
  }
  return seen.length
}

/**
 * Records this viewer may see, by name.
 *
 * **By name, always.** Not by recency, not by size, not by anything derived
 * from the work. An ordering over trajectories tells you which of them matters
 * before you have read any of them, and a measure adopted to direct attention
 * becomes the thing people work towards (C6).
 */
export async function listProjects(db: Db, options: { viewerParty?: string } = {}) {
  const visible = options.viewerParty
    ? or(eq(projects.disclosure, 'listed'), eq(projects.openedBy, options.viewerParty))
    : eq(projects.disclosure, 'listed')

  const rows = await db.select().from(projects).where(visible)
  rows.sort((a, b) => a.slug.localeCompare(b.slug))
  return Promise.all(rows.map((row) => withTrajectories(db, row)))
}

export async function getProject(db: Db, slug: string): Promise<Listed | null> {
  const [row] = await db.select().from(projects).where(eq(projects.slug, slug)).limit(1)
  return row ? withTrajectories(db, row) : null
}

async function withTrajectories(db: Db, row: typeof projects.$inferSelect): Promise<Listed> {
  const lines = await db.select().from(trajectories).where(eq(trajectories.projectId, row.id))
  lines.sort((a, b) => a.trajId.localeCompare(b.trajId))
  const [opener] = await db.select().from(users).where(eq(users.party, row.openedBy)).limit(1)
  return {
    slug: row.slug,
    title: row.title,
    description: row.description,
    openedBy: row.openedBy,
    openedByName: opener?.name ?? null,
    tier: row.tier,
    disclosure: row.disclosure,
    openedAt: row.openedAt,
    trajectories: lines.map((line) => ({
      trajId: line.trajId,
      title: line.title,
      question: line.question,
      transitionCount: line.transitionCount,
      openCount: line.openCount,
    })),
  }
}

export interface Hit {
  slug: string
  trajId: string
  question: string
  snippet: string
  where: string
}

/**
 * Search **filters; it does not rank.**
 *
 * There is no relevance score, no ordering by match quality and no "best
 * result". Matches come back in the same order everything else is listed in,
 * because an ordering by relevance is a measure over trajectories, and a
 * measure adopted to direct attention becomes the object of effort. This is
 * the single place a reader would most readily believe a number, which is why
 * there is not one.
 */
export async function search(
  db: Db,
  query: string,
  options: { viewerParty?: string } = {},
): Promise<Hit[]> {
  const needle = query.trim().toLowerCase()
  if (!needle) return []
  const pattern = `%${needle.replace(/[%_]/g, (c) => `\\${c}`)}%`

  const visible = options.viewerParty
    ? or(eq(projects.disclosure, 'listed'), eq(projects.openedBy, options.viewerParty))
    : eq(projects.disclosure, 'listed')
  const allowed = await db.select().from(projects).where(visible)
  const bySlug = new Map(allowed.map((row) => [row.id, row]))

  const hits: Hit[] = []

  const questions = await db
    .select()
    .from(trajectories)
    .where(or(like(trajectories.question, pattern), like(trajectories.title, pattern)))
  for (const line of questions) {
    const project = bySlug.get(line.projectId)
    if (!project) continue
    hits.push({
      slug: project.slug,
      trajId: line.trajId,
      question: line.question,
      snippet: line.question,
      where: 'the question',
    })
  }

  const bodies = await db.select().from(searchText).where(like(searchText.body, pattern))
  for (const row of bodies) {
    const project = bySlug.get(row.projectId)
    if (!project) continue
    if (hits.some((hit) => hit.slug === project.slug && hit.trajId === row.trajId)) continue
    const line =
      row.body
        .split('\n')
        .find((candidate) => candidate.toLowerCase().includes(needle))
        ?.trim() ?? row.body.split('\n')[0]!
    const [trajectory] = await db
      .select()
      .from(trajectories)
      .where(and(eq(trajectories.projectId, row.projectId), eq(trajectories.trajId, row.trajId)))
      .limit(1)
    hits.push({
      slug: project.slug,
      trajId: row.trajId,
      question: trajectory?.question ?? '',
      snippet: line.slice(0, 240),
      where: row.kind === 'position' ? 'a position' : `a ${row.kind}`,
    })
  }

  // Same order as everything else: by record, then by trajectory.
  hits.sort((a, b) => a.slug.localeCompare(b.slug) || a.trajId.localeCompare(b.trajId))
  return hits
}

/**
 * Widen what a record discloses. There is no operation that narrows it (C7).
 */
export async function widenDisclosure(db: Db, root: string, slug: string): Promise<void> {
  const [row] = await db.select().from(projects).where(eq(projects.slug, slug)).limit(1)
  if (!row) return
  writeHostFacts(root, slug, { openedBy: row.openedBy, disclosure: 'listed' })
  await db.update(projects).set({ disclosure: 'listed' }).where(eq(projects.slug, slug))
}
