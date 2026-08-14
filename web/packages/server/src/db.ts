/**
 * The database, and what it is emphatically not.
 *
 * **No database is the system of record** (C11). The record is plain files on
 * disk: transitions in YAML, state content in its own files named by the hash
 * of its bytes. Everything in this schema is one of two things:
 *
 *   *accounts* -- who may reach this server through a browser. Local to this
 *   host, meaningful nowhere else, and not part of any record. Deleting the
 *   whole table leaves every transition and every signature intact.
 *
 *   *an index* -- a cache of what is in the files, so that a page can list and
 *   search without walking the filesystem. Every row is derived, and
 *   `reindex()` rebuilds all of it from the files. If this file is deleted the
 *   only cost is the time to rebuild.
 *
 * The test that keeps this honest is in `test/authority.test.ts`: delete the
 * database, rebuild, and every identifier must be unchanged. The day that test
 * cannot be written is the day the host has become the authority.
 */

import { sql } from 'drizzle-orm'
import { index, integer, sqliteTable, text, uniqueIndex } from 'drizzle-orm/sqlite-core'

/**
 * A person who can sign in here.
 *
 * `party` is the public half of their keypair. The private half is **not
 * here**, is not anywhere on this server, and never arrives: it is generated
 * in the browser and stays there. A server that could sign as its users could
 * forge attestations, and C2 would mean nothing.
 */
export const users = sqliteTable(
  'users',
  {
    id: integer('id').primaryKey({ autoIncrement: true }),
    name: text('name').notNull(),
    /** key:ed25519:… — public, quotable, safe to print. */
    party: text('party').notNull(),
    /** scrypt. Guards browser access to this host, and nothing else. */
    passwordHash: text('password_hash').notNull(),
    displayName: text('display_name'),
    createdAt: text('created_at').notNull(),
  },
  (table) => [
    uniqueIndex('users_name').on(table.name),
    uniqueIndex('users_party').on(table.party),
  ],
)

/**
 * A record hosted here. Derived from the files under `data/records/<slug>`.
 *
 * There is no `stars`, no `views`, no `activity` and no `rank` column, and
 * there will not be one. A measure adopted to direct attention becomes the
 * thing people work towards, and the first place that happens in a system like
 * this is the project list (C6).
 */
export const projects = sqliteTable(
  'projects',
  {
    id: integer('id').primaryKey({ autoIncrement: true }),
    slug: text('slug').notNull(),
    title: text('title').notNull(),
    /** Derived from the project's README. The file is the original. */
    description: text('description').notNull().default(''),
    /** The party who opened it. Not an owner: nothing here confers control. */
    openedBy: text('opened_by').notNull(),
    tier: text('tier', { enum: ['personal', 'group', 'open'] }).notNull(),
    /** Widens only, never narrows (C7). Enforced in `projects.ts`. */
    disclosure: text('disclosure', { enum: ['private', 'listed'] }).notNull(),
    openedAt: text('opened_at').notNull(),
    indexedAt: text('indexed_at').notNull(),
  },
  (table) => [uniqueIndex('projects_slug').on(table.slug)],
)

/** A line of work inside a record. One record may hold several. */
export const trajectories = sqliteTable(
  'trajectories',
  {
    id: integer('id').primaryKey({ autoIncrement: true }),
    projectId: integer('project_id')
      .notNull()
      .references(() => projects.id, { onDelete: 'cascade' }),
    trajId: text('traj_id').notNull(),
    title: text('title'),
    question: text('question').notNull(),
    /**
     * How many transitions are in *this* trajectory. Permitted: a count
     * within one trajectory, shown without comparison to any other, is
     * information about your own work. It is never sorted on, never compared
     * across projects, and never shown beside another trajectory's (C6).
     */
    transitionCount: integer('transition_count').notNull(),
    /** Objections and failed checks nobody has answered. */
    openCount: integer('open_count').notNull(),
    openedAt: text('opened_at').notNull(),
  },
  (table) => [
    index('trajectories_project').on(table.projectId),
    uniqueIndex('trajectories_traj').on(table.projectId, table.trajId),
  ],
)

/**
 * Searchable text, derived from state content.
 *
 * Search **filters; it does not rank** — so there is no relevance score column
 * and no BM25 table. Results come back in the same order everything else is
 * listed in, because an ordering by relevance is a measure over trajectories.
 */
export const searchText = sqliteTable(
  'search_text',
  {
    id: integer('id').primaryKey({ autoIncrement: true }),
    projectId: integer('project_id')
      .notNull()
      .references(() => projects.id, { onDelete: 'cascade' }),
    trajId: text('traj_id').notNull(),
    stateId: text('state_id').notNull(),
    kind: text('kind').notNull(),
    body: text('body').notNull(),
  },
  (table) => [index('search_project').on(table.projectId)],
)

export const SCHEMA = sql`
  PRAGMA journal_mode = WAL;
  PRAGMA foreign_keys = ON;
`
