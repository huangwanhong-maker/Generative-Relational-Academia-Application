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
import { createHash } from 'node:crypto'
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { join, resolve } from 'node:path'

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
  // Its own repository, before grrp touches it. Version control is a
  // substrate here and not a requirement -- everything works in a directory
  // that is not one -- but a project nested inside another repository would
  // have its transitions committed into somebody else's history, and `git log`
  // run inside it would answer with that history instead of its own.
  await runGit(['init', '-q'], dir)
  const started = await runGrrp(['init'], dir)
  if (!started.ok) {
    rmSync(dir, { recursive: true, force: true })
    return started
  }
  const opened = await runGrrp(['new', question, '--title', slug], dir)
  if (!opened.ok) {
    // A half-built project is worse than none: it holds the name, it is not a
    // valid record, and the person who tried to create it has no way to say
    // so. Nothing was disclosed and nothing was recorded, so removing it takes
    // nothing from anybody -- which is the only reason it is safe to do.
    rmSync(dir, { recursive: true, force: true })
    return opened
  }
  writeHostFacts(root, slug, { openedBy, disclosure: 'private' })
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


// --- the artefact plane ------------------------------------------------------

/**
 * Working files belonging to a project: data, drafts, figures, notes.
 *
 * **Storing a file records nothing.** No transition is written, no identifier
 * is minted, nothing enters the log. C1 is explicit that no operation exists
 * merely so that a record exists, and a file appearing in a directory is not a
 * change in anybody's understanding.
 *
 * What makes a file part of the record is a transition referencing it, by the
 * hash of its bytes, through the `artefacts` field the skeleton already
 * carries. Until then it is material, and material is not evidence.
 *
 * The hash is computed and shown for exactly that reason: it is what a
 * transition would cite, and what a reader elsewhere would check.
 */
export interface ProjectFile {
  name: string
  size: number
  /** state:sha256:… over the bytes as they sit on disk. Citable as an artefact. */
  digest: string
  modified: string
}

const FILES_DIR = 'files'

/**
 * Names that are a single path segment, and nothing clever.
 *
 * Rejecting traversal is the obvious half. The less obvious half is rejecting
 * leading dots, so that no upload can land on `.grrp/`, `.git/` or the host
 * sidecar and rewrite the record through the file tab.
 *
 * This **refuses** a name with a directory in it rather than quietly reducing
 * it to its last segment. Stripping would be equally safe and would silently
 * store something other than what was asked for, which is the habit that makes
 * a tool untrustworthy in the places where being wrong is not merely untidy.
 */
export function safeFileName(name: string): string {
  const trimmed = name.trim()
  const wrong =
    !trimmed ||
    /[\/]/.test(trimmed) ||
    trimmed.startsWith('.') ||
    trimmed.includes('..') ||
    // eslint-disable-next-line no-control-regex
    /[ -]/.test(trimmed) ||
    trimmed.length > 128
  if (wrong) {
    throw new Error(
      `${JSON.stringify(name)} will not do as a file name: one plain name, no directories, ` +
        'not starting with a dot, up to 128 characters.',
    )
  }
  return trimmed
}

export function listFiles(root: string, slug: string): ProjectFile[] {
  const dir = join(root, slug, FILES_DIR)
  if (!existsSync(dir)) return []
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => {
      const path = join(dir, entry.name)
      const bytes = readFileSync(path)
      return {
        name: entry.name,
        size: bytes.length,
        digest: `state:sha256:${createHash('sha256').update(bytes).digest('hex')}`,
        modified: statSync(path).mtime.toISOString(),
      }
    })
    // By name. Not by size, not by recency: an ordering here would be a
    // measure over the project's material, and would say which mattered.
    .sort((a, b) => a.name.localeCompare(b.name))
}

export function writeProjectFile(
  root: string,
  slug: string,
  name: string,
  bytes: Buffer,
): ProjectFile {
  const safe = safeFileName(name)
  const dir = join(root, slug, FILES_DIR)
  mkdirSync(dir, { recursive: true })
  // Bytes, always. A file cited by a transition is cited by the hash of what
  // is on disk, so nothing may rewrite it on the way in.
  writeFileSync(join(dir, safe), bytes)
  return listFiles(root, slug).find((file) => file.name === safe)!
}

export function readProjectFile(root: string, slug: string, name: string): Buffer | null {
  const path = join(root, slug, FILES_DIR, safeFileName(name))
  return existsSync(path) ? readFileSync(path) : null
}

// --- one trajectory, in full -------------------------------------------------

export interface TransitionView {
  id: string
  act: string | null
  target: string | null
  relation: string | null
  trigger: string | null
  disposition: string | null
  parents: string[]
  priorState: string | null
  posteriorState: string | null
  performer: string
  performed: string
  attested: boolean
  /** The content of the state this act produced, when it is held here. */
  body: string | null
  artefacts: unknown[]
}

export function readTrajectoryDetail(
  root: string,
  slug: string,
  trajId: string,
): { question: string; title: string | null; transitions: TransitionView[] } | null {
  const dir = join(root, slug, 'trajectories', trajId.replace(/^traj:/, ''))
  const metaPath = join(dir, 'trajectory.yaml')
  if (!existsSync(metaPath)) return null
  const meta = readYaml(metaPath)

  const transitionsDir = join(dir, 'transitions')
  const records = existsSync(transitionsDir)
    ? readdirSync(transitionsDir)
        .filter((name) => name.endsWith('.yaml'))
        .map((name) => readYaml(join(transitionsDir, name)))
    : []

  const body = (stateId: unknown): string | null => {
    if (typeof stateId !== 'string') return null
    const path = join(dir, 'states', `${stateId.split(':').pop()}.md`)
    return existsSync(path) ? readFileSync(path).toString('utf-8') : null
  }

  const views: TransitionView[] = records.map((record) => ({
    id: String(record['id']),
    act: (record['act'] as string) ?? null,
    target: (record['target'] as string) ?? null,
    relation: (record['relation'] as string) ?? null,
    trigger: (record['trigger'] as string) ?? null,
    disposition: (record['disposition'] as string) ?? null,
    parents: ((record['parents'] as string[]) ?? []).map(String),
    priorState: (record['prior_state'] as string) ?? null,
    posteriorState: (record['posterior_state'] as string) ?? null,
    performer: String(record['performer'] ?? ''),
    performed: String(record['performed'] ?? ''),
    attested: Boolean((record['registration'] as Record<string, unknown>)?.['attested']),
    body: body(record['posterior_state']),
    artefacts: (record['artefacts'] as unknown[]) ?? [],
  }))

  // Parents before children, then by time. The log order, which is a
  // chronology of one line of work and not a ranking of anything.
  const byId = new Map(views.map((view) => [view.id, view]))
  const ordered: TransitionView[] = []
  const placed = new Set<string>()
  const place = (view: TransitionView) => {
    if (placed.has(view.id)) return
    placed.add(view.id)
    for (const parent of view.parents) {
      const ancestor = byId.get(parent)
      if (ancestor) place(ancestor)
    }
    ordered.push(view)
  }
  for (const view of [...views].sort((a, b) => a.performed.localeCompare(b.performed))) place(view)

  return {
    question: String(meta['question'] ?? ''),
    title: (meta['title'] as string) ?? null,
    transitions: ordered,
  }
}

/** The trajectory drawn, as the reference implementation draws it. */
export async function trajectoryGraph(
  root: string,
  slug: string,
  trajId: string,
): Promise<string | null> {
  const drawn = await runGrrp(['graph', trajId], join(root, slug))
  return drawn.ok && drawn.stdout.includes('<svg') ? drawn.stdout : null
}


// --- git, which is a substrate and not the record ----------------------------

/**
 * A commit is **not** a transition, and this is why the view of them is a
 * development tool rather than a feature.
 *
 * git supplies append-only history and the transport by which a complete
 * record is copied elsewhere. It supplies none of the meaning: the record is
 * the YAML and the state files, the identifiers are hashes of their bytes, and
 * a record in a directory that was never a repository is exactly as valid.
 * Showing commits beside transitions would teach the opposite, which is why
 * this is behind a flag and labelled.
 */
export interface Commit {
  hash: string
  when: string
  subject: string
}

function runGit(args: string[], cwd: string): Promise<GrrpResult> {
  return new Promise((resolve) => {
    const child = spawn('git', args, { cwd, env: process.env, shell: false })
    let stdout = ''
    let stderr = ''
    child.stdout.on('data', (chunk) => (stdout += chunk))
    child.stderr.on('data', (chunk) => (stderr += chunk))
    child.on('error', (error) => resolve({ ok: false, code: -1, stdout, stderr: error.message }))
    child.on('close', (code) => resolve({ ok: code === 0, code: code ?? -1, stdout, stderr }))
  })
}

/**
 * The project's own commits, or nothing.
 *
 * The guard is the whole of the difficulty. `git log` inside a directory that
 * is not a repository answers with the history of whichever repository
 * encloses it, so a project sitting inside another checkout would report that
 * one's commits as its own. This asks git where the repository root actually
 * is and refuses unless it is this project.
 */
export async function gitHistory(
  root: string,
  slug: string,
  limit = 50,
): Promise<{ isRepository: boolean; commits: Commit[]; note?: string }> {
  const dir = resolve(join(root, slug))
  const top = await runGit(['rev-parse', '--show-toplevel'], dir)
  if (!top.ok) {
    return { isRepository: false, commits: [], note: 'This project is not a git repository.' }
  }
  if (resolve(top.stdout.trim()) !== dir) {
    return {
      isRepository: false,
      commits: [],
      note:
        'This project is not a git repository of its own. It sits inside one, whose history ' +
        'is not shown here because it is not this project.',
    }
  }

  const log = await runGit(
    ['log', `--max-count=${limit}`, '--date=iso-strict', '--format=%H%x1f%ad%x1f%s'],
    dir,
  )
  if (!log.ok) return { isRepository: true, commits: [], note: 'No commits yet.' }

  return {
    isRepository: true,
    commits: log.stdout
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        const [hash = '', when = '', subject = ''] = line.split('\u001f')
        return { hash, when, subject }
      }),
  }
}
