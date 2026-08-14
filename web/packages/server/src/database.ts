/**
 * Opening the index, and creating it when it is not there.
 *
 * Migrations are plain `CREATE TABLE IF NOT EXISTS`, deliberately. Everything
 * except `users` is derived from the files and can be dropped and rebuilt, so
 * the usual reason for a migration framework -- data you cannot regenerate --
 * applies to exactly one table here.
 */

import { mkdirSync } from 'node:fs'
import { dirname } from 'node:path'

import Database from 'better-sqlite3'
import { drizzle, type BetterSQLite3Database } from 'drizzle-orm/better-sqlite3'

import * as schema from './db.js'

export type Db = BetterSQLite3Database<typeof schema>

const TABLES = [
  `CREATE TABLE IF NOT EXISTS users (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     name TEXT NOT NULL,
     party TEXT NOT NULL,
     password_hash TEXT NOT NULL,
     display_name TEXT,
     created_at TEXT NOT NULL
   )`,
  `CREATE UNIQUE INDEX IF NOT EXISTS users_name ON users (name)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS users_party ON users (party)`,
  `CREATE TABLE IF NOT EXISTS projects (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     slug TEXT NOT NULL,
     title TEXT NOT NULL,
     opened_by TEXT NOT NULL,
     tier TEXT NOT NULL,
     disclosure TEXT NOT NULL,
     opened_at TEXT NOT NULL,
     indexed_at TEXT NOT NULL
   )`,
  `CREATE UNIQUE INDEX IF NOT EXISTS projects_slug ON projects (slug)`,
  `CREATE TABLE IF NOT EXISTS trajectories (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
     traj_id TEXT NOT NULL,
     title TEXT,
     question TEXT NOT NULL,
     transition_count INTEGER NOT NULL,
     open_count INTEGER NOT NULL,
     opened_at TEXT NOT NULL
   )`,
  `CREATE INDEX IF NOT EXISTS trajectories_project ON trajectories (project_id)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS trajectories_traj ON trajectories (project_id, traj_id)`,
  `CREATE TABLE IF NOT EXISTS search_text (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
     traj_id TEXT NOT NULL,
     state_id TEXT NOT NULL,
     kind TEXT NOT NULL,
     body TEXT NOT NULL
   )`,
  `CREATE INDEX IF NOT EXISTS search_project ON search_text (project_id)`,
]

export function openDatabase(file: string): Db {
  if (file !== ':memory:') mkdirSync(dirname(file), { recursive: true })
  const connection = new Database(file)
  connection.pragma('journal_mode = WAL')
  connection.pragma('foreign_keys = ON')
  for (const statement of TABLES) connection.exec(statement)
  return drizzle(connection, { schema })
}
