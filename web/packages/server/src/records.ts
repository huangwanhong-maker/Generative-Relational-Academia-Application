/**
 * The files, and the index derived from them.
 *
 * Two rules govern this module and nothing here may quietly break them.
 *
 * **Writes go through `grrp`.** Creating a record, opening a trajectory and
 * recording an act are done by invoking the reference implementation as a
 * subprocess. This server does not construct a transition skeleton, does not
 * compute an identifier and does not decide what is lawful. One implementation
 * owns those decisions -- the one with the conformance suite -- for the same
 * reason a git forge shells out to git instead of reimplementing it.
 *
 * **Reads may parse the files directly.** Reading YAML to build an index is
 * not reimplementing the protocol; it is looking at what the protocol wrote.
 * Nothing derived here is authoritative, and `reindex` rebuilds all of it.
 */

import { spawn } from 'node:child_process'
import { readFileSync, readdirSync, existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

import { parse as parseYaml } from 'yaml'

export interface GrrpResult {
  ok: boolean
  code: number
  stdout: string
  stderr: string
}

/**
 * How to invoke the reference implementation.
 *
 * Configurable because the two are deliberately separate programs: this server
 * is Level 3 and disposable, `grrp` is the implementation the protocol is
 * defined against, and coupling them by import would make that untrue.
 */
export const GRRP_COMMAND = (process.env['GRA_GRRP'] ?? 'python -m grrp.cli').split(' ')

export function runGrrp(args: string[], cwd: string): Promise<GrrpResult> {
  const [command, ...prefix] = GRRP_COMMAND
  return new Promise((resolve) => {
    const child = spawn(command!, [...prefix, ...args], {
      cwd,
      env: process.env,
      shell: false,
    })
    let stdout = ''
    let stderr = ''
    child.stdout.on('data', (chunk) => (stdout += chunk))
    child.stderr.on('data', (chunk) => (stderr += chunk))
    child.on('error', (error) =>
      resolve({ ok: false, code: -1, stdout, stderr: `${error.message}. Is grrp installed?` }),
    )
    child.on('close', (code) => resolve({ ok: code === 0, code: code ?? -1, stdout, stderr }))
  })
}

/**
 * Open a record, and the first trajectory in it.
 *
 * Two invocations of `grrp`, not one call into a library: `init` makes the
 * directory a record and generates nothing this server keeps, and `new` opens
 * the question. Both are the reference implementation's decisions to make.
 */
export async function createRecord(
  root: string,
  slug: string,
  question: string,
  openedBy: string,
): Promise<GrrpResult> {
  const dir = join(root, slug)
  mkdirSync(dir, { recursive: true })
  const started = await runGrrp(['init'], dir)
  if (!started.ok) return started
  const opened = await runGrrp(['new', question, '--title', slug], dir)
  if (opened.ok) writeHostFacts(root, slug, { openedBy, disclosure: 'private' })
  return opened
}

/**
 * Facts this host holds about a record, which are not part of the record.
 *
 * Who opened it *here* and whether it is listed *here* are properties of this
 * server, not of the protocol: the same record hosted elsewhere would have
 * different answers, and a copy taken away has none. They live in a file
 * beside the record rather than only in the database, so that the database
 * stays a pure cache -- deleteable at any moment, rebuildable from the files,
 * and therefore never the system of record (C11).
 *
 * Deliberately outside `.grrp/`, because it is not part of what a bundle
 * carries and must not travel with the record as though it were.
 */
export interface HostFacts {
  /** The party who opened it here. Not an owner: nothing here confers control. */
  openedBy: string
  /** Widens only, never narrows (C7). */
  disclosure: 'private' | 'listed'
}

const HOST_FILE = '.gra-host.json'

export function readHostFacts(root: string, slug: string): HostFacts | null {
  const path = join(root, slug, HOST_FILE)
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path).toString('utf-8')) as HostFacts
  } catch {
    return null
  }
}

export function writeHostFacts(root: string, slug: string, facts: HostFacts): void {
  const path = join(root, slug, HOST_FILE)
  const held = readHostFacts(root, slug)
  // Disclosure widens and never narrows, including through this function.
  // There is no argument that makes it go back.
  const disclosure = held?.disclosure === 'listed' ? 'listed' : facts.disclosure
  writeFileSync(path, `${JSON.stringify({ ...facts, disclosure }, null, 2)}
`, 'utf-8')
}

export function slugify(text: string, limit = 48): string {
  const slug = text
    .normalize('NFKD')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, limit)
    .replace(/-+$/, '')
  return slug || 'record'
}

// --- reading the files -------------------------------------------------------

export interface TrajectoryOnDisk {
  trajId: string
  title: string | null
  question: string
  openedAt: string
  transitionCount: number
  openCount: number
  states: { stateId: string; kind: string; body: string }[]
}

export interface ProjectOnDisk {
  slug: string
  title: string
  openedBy: string
  tier: 'personal' | 'group' | 'open'
  openedAt: string
  trajectories: TrajectoryOnDisk[]
}

function readYaml(path: string): Record<string, unknown> {
  // Bytes, then decoded as UTF-8: never a text-mode read. A state identifier
  // is the hash of the bytes of its file, and a runtime that translated line
  // endings on the way in would silently repair a corrupted record rather
  // than reveal it.
  return (parseYaml(readFileSync(path).toString('utf-8')) ?? {}) as Record<string, unknown>
}

/** Acts that leave a live position behind. A question is not one of them. */
const POSITION_ACTS = new Set(['claim', 'transformation'])

export function readProject(root: string, slug: string): ProjectOnDisk | null {
  const dir = join(root, slug)
  const profilePath = join(dir, '.grrp', 'profile.yaml')
  if (!existsSync(profilePath)) return null
  const profile = readYaml(profilePath)

  const trajectoriesDir = join(dir, 'trajectories')
  const trajectories: TrajectoryOnDisk[] = []
  if (existsSync(trajectoriesDir)) {
    for (const entry of readdirSync(trajectoriesDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue
      const trajectory = readTrajectory(join(trajectoriesDir, entry.name))
      if (trajectory) trajectories.push(trajectory)
    }
  }
  trajectories.sort((a, b) => a.trajId.localeCompare(b.trajId))

  return {
    slug,
    title: (trajectories[0]?.title || slug) as string,
    openedBy: String(profile['party'] ?? ''),
    tier: (profile['tier'] as ProjectOnDisk['tier']) ?? 'personal',
    openedAt: String(profile['created'] ?? ''),
    trajectories,
  }
}

function readTrajectory(dir: string): TrajectoryOnDisk | null {
  const metaPath = join(dir, 'trajectory.yaml')
  if (!existsSync(metaPath)) return null
  const meta = readYaml(metaPath)

  const transitionsDir = join(dir, 'transitions')
  const records: Record<string, unknown>[] = existsSync(transitionsDir)
    ? readdirSync(transitionsDir)
        .filter((name) => name.endsWith('.yaml'))
        .map((name) => readYaml(join(transitionsDir, name)))
    : []

  // An objection or a failed check that no later transition has answered.
  // Counted within this trajectory and shown only beside its own question --
  // never compared with another's, which is what would make it a measure.
  const answered = new Set<string>()
  for (const record of records) {
    for (const parent of (record['parents'] as string[]) ?? []) answered.add(parent)
  }
  const openCount = records.filter((record) => {
    const disposition = record['disposition']
    return (
      (disposition === 'unresolved' || disposition === 'contested') &&
      record['act'] !== 'question' &&
      !answered.has(String(record['id']))
    )
  }).length

  const statesDir = join(dir, 'states')
  const byState = new Map<string, string>()
  for (const record of records) {
    const posterior = record['posterior_state']
    if (typeof posterior === 'string') {
      byState.set(posterior, POSITION_ACTS.has(String(record['act'])) ? 'position' : String(record['act'] ?? 'state'))
    }
  }
  const states: TrajectoryOnDisk['states'] = []
  if (existsSync(statesDir)) {
    for (const name of readdirSync(statesDir)) {
      if (!name.endsWith('.md')) continue
      const stateId = `state:sha256:${name.replace(/\.md$/, '')}`
      states.push({
        stateId,
        kind: byState.get(stateId) ?? 'state',
        body: readFileSync(join(statesDir, name)).toString('utf-8'),
      })
    }
  }

  return {
    trajId: String(meta['id'] ?? ''),
    title: (meta['title'] as string) ?? null,
    question: String(meta['question'] ?? ''),
    openedAt: String(meta['created'] ?? ''),
    transitionCount: records.length,
    openCount,
    states,
  }
}

export function listRecordSlugs(root: string): string[] {
  if (!existsSync(root)) return []
  return readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(root, entry.name, '.grrp')))
    .map((entry) => entry.name)
    .sort()
}
