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
import { dirname, join, resolve } from 'node:path'

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
 * Create a project. An empty one, on purpose.
 *
 * A project is a container -- a directory that is a record -- and creating one
 * asks for nothing but a name. The question belongs a level down: it anchors a
 * *trajectory*, which is the thing transitions attach to (C4), and demanding
 * one up front conflates the container with the line of work inside it.
 *
 * An empty project can hold material and can record nothing, which is the
 * honest state and worth showing rather than preventing: until a question is
 * open there is no identified prior state for a transition to reference.
 */
export async function createRecord(
  root: string,
  slug: string,
  openedBy: string,
  description = '',
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
  if (description.trim()) writeDescription(root, slug, description)
  writeHostFacts(root, slug, { openedBy, disclosure: 'private' })
  return started
}

/**
 * Open a question, which is what actually starts a line of work.
 *
 * The reference implementation decides what that means and what identifier it
 * gets. This only passes the words along.
 */
export async function openQuestion(
  root: string,
  slug: string,
  question: string,
): Promise<GrrpResult> {
  return runGrrp(['new', question], join(root, slug))
}

/**
 * What a project says about itself, in a file anybody can read.
 *
 * A plain `README.md` at the top of the project rather than a column in a
 * database: it travels with the record when somebody takes a copy, it survives
 * this server being replaced, and it is legible without any of this (C11).
 *
 * Like anything under `files/`, writing it records nothing. A description is
 * material, not a transition.
 */
const DESCRIPTION_FILE = 'README.md'

export function readDescription(root: string, slug: string): string {
  const path = join(root, slug, DESCRIPTION_FILE)
  return existsSync(path) ? readFileSync(path).toString('utf-8') : ''
}

export function writeDescription(root: string, slug: string, text: string): void {
  writeFileSync(join(root, slug, DESCRIPTION_FILE), text.trim() + '\n', 'utf-8')
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
  description: string
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
    title: slug,
    description: readDescription(root, slug),
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
const NODES_DIR = 'nodes'

/**
 * Where a node's workspace lives.
 *
 * `nodes/<transition>/` is **applicative**, not protocol. It is an ordinary
 * folder, it may be changed at any time, and nothing signed refers to it.
 *
 * That separation is what makes a mutable per-node folder safe at all. A
 * transition is never edited (C3); if a signature covered a folder whose
 * contents could change, the node would mean something different tomorrow than
 * when it was signed and the signature would still verify -- which is worse
 * than it failing, because nothing would tell you. Nothing here is covered, so
 * nothing can move underneath.
 *
 * Material becomes part of the record when a transition **cites** it by hash,
 * through the `artefacts` field the skeleton already carries. That is an act,
 * and it is performed deliberately.
 */
export function nodeArea(nodeId: string): string {
  return `${NODES_DIR}/${safeSegment(nodeId.split(':').pop() ?? nodeId)}`
}

/**
 * One path segment, and nothing clever.
 *
 * Rejecting traversal is the obvious half. The less obvious half is rejecting
 * leading dots, so no upload can land on `.grrp/`, `.git/` or the host sidecar
 * and rewrite the record through a file tab.
 *
 * This **refuses** rather than quietly reducing a name to its last segment.
 * Stripping would be equally safe and would silently store something other
 * than what was asked for, which is the habit that makes a tool untrustworthy
 * in the places where being wrong is not merely untidy.
 */
function safeSegment(segment: string): string {
  const trimmed = segment.trim()
  const wrong =
    !trimmed ||
    trimmed.startsWith('.') ||
    trimmed.includes('..') ||
    // eslint-disable-next-line no-control-regex
    /[ -<>:"|?*\/]/.test(trimmed) ||
    trimmed.length > 128
  if (wrong) {
    throw new Error(
      `${JSON.stringify(segment)} will not do as a name: letters, digits and ordinary ` +
        'punctuation, not starting with a dot, up to 128 characters per segment.',
    )
  }
  return trimmed
}

/** A relative path of safe segments. Folders are allowed; escaping is not. */
export function safeFilePath(name: string): string {
  const segments = name.trim().split(String.fromCharCode(92)).join("/").split('/').filter(Boolean)
  if (!segments.length || segments.length > 8) {
    throw new Error(`${JSON.stringify(name)} will not do as a path`)
  }
  return segments.map(safeSegment).join('/')
}

/** Kept for the project-wide store, which is one flat area. */
export function safeFileName(name: string): string {
  return safeFilePath(name)
}

export interface ProjectFile {
  /** Relative to the area. May contain folders. */
  name: string
  size: number
  /** state:sha256:… over the bytes as they sit on disk. Citable as an artefact. */
  digest: string
  modified: string
}

function walk(base: string, prefix = ''): ProjectFile[] {
  const dir = prefix ? join(base, prefix) : base
  if (!existsSync(dir)) return []
  const out: ProjectFile[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const relative = prefix ? `${prefix}/${entry.name}` : entry.name
    if (entry.isDirectory()) {
      out.push(...walk(base, relative))
    } else if (entry.isFile()) {
      const bytes = readFileSync(join(base, relative))
      out.push({
        name: relative,
        size: bytes.length,
        digest: `state:sha256:${createHash('sha256').update(bytes).digest('hex')}`,
        modified: statSync(join(base, relative)).mtime.toISOString(),
      })
    }
  }
  // By path. Not by size, not by recency: an ordering here would be a measure
  // over the project's material, and would say which of it mattered.
  return out.sort((a, b) => a.name.localeCompare(b.name))
}

export function listFiles(root: string, slug: string, area = FILES_DIR): ProjectFile[] {
  return walk(join(root, slug, area))
}

export function writeProjectFile(
  root: string,
  slug: string,
  name: string,
  bytes: Buffer,
  area = FILES_DIR,
): ProjectFile {
  const safe = safeFilePath(name)
  const path = join(root, slug, area, safe)
  mkdirSync(dirname(path), { recursive: true })
  // Bytes, always. A file cited by a transition is cited by the hash of what
  // is on disk, so nothing may rewrite it on the way in.
  writeFileSync(path, bytes)
  return listFiles(root, slug, area).find((file) => file.name === safe)!
}

export function readProjectFile(
  root: string,
  slug: string,
  name: string,
  area = FILES_DIR,
): Buffer | null {
  const path = join(root, slug, area, safeFilePath(name))
  return existsSync(path) ? readFileSync(path) : null
}

export function removeProjectFile(
  root: string,
  slug: string,
  name: string,
  area = FILES_DIR,
): boolean {
  // Only in a workspace, and only because nothing in the record refers to it.
  // A cited artefact is referenced by hash from a signed transition; removing
  // the bytes is a redaction, which is `grrp redact` and leaves a mark.
  const path = join(root, slug, area, safeFilePath(name))
  if (!existsSync(path)) return false
  rmSync(path, { force: true })
  return true
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


// --- the whole project as one graph ------------------------------------------

/**
 * Every transition in a project, across every question, in one graph.
 *
 * Three things make this graph **not sequential**, and none of them is new:
 *
 *   `parents` is a list, so a transition may follow several.
 *
 *   `grrp connect` to a state in another trajectory adds *that* trajectory's
 *   transition as a parent. The link is an ordinary edge and travels with the
 *   record; no field was invented for it.
 *
 *   Artefacts are cited by the hash of their bytes, so an experiment bearing
 *   on three questions is cited by three transitions and appears here as one
 *   node with three edges. That is the occasion, shared -- and it needed no
 *   parallel vocabulary of event types, which acts being closed would have
 *   forbidden anyway (C12).
 *
 * What kind of occasion it was is already named by `trigger`: experiment,
 * discussion, observation, simulation, literature, failure.
 */
export interface GraphNode {
  id: string
  /** 'transition' or 'artefact'. Not a type vocabulary -- a drawing distinction. */
  shape: 'transition' | 'artefact'
  act: string | null
  trigger: string | null
  disposition: string | null
  trajId: string | null
  question: string | null
  label: string
  attested: boolean
  performed: string
  /** What this transition committed to, by hash. Part of the record. */
  cited: { ref: string; label: string }[]
}

export interface GraphEdge {
  from: string
  to: string
  /** 'follows' | 'cites'. 'crosses' when the parent is in another trajectory. */
  kind: 'follows' | 'crosses' | 'cites'
}

export function projectGraph(
  root: string,
  slug: string,
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const project = readProject(root, slug)
  if (!project) return { nodes: [], edges: [] }

  const nodes = new Map<string, GraphNode>()
  const edges: GraphEdge[] = []
  const trajectoryOf = new Map<string, string>()

  for (const trajectory of project.trajectories) {
    const detail = readTrajectoryDetail(root, slug, trajectory.trajId)
    if (!detail) continue

    for (const transition of detail.transitions) {
      trajectoryOf.set(transition.id, trajectory.trajId)
      nodes.set(transition.id, {
        id: transition.id,
        shape: 'transition',
        act: transition.act,
        trigger: transition.trigger,
        disposition: transition.disposition,
        trajId: trajectory.trajId,
        question: trajectory.question,
        label: (transition.body ?? '').trim().split('\n')[0] ?? '',
        attested: transition.attested,
        performed: transition.performed,
        cited: (transition.artefacts as { ref?: string; scheme?: string }[])
          .filter((artefact) => artefact?.ref)
          .map((artefact) => ({
            ref: String(artefact.ref),
            label: String(artefact.scheme ?? 'reference'),
          })),
      })

      // An artefact is the occasion, and the same occasion cited twice is one
      // node. The key is the reference itself, which for held material is the
      // hash of its bytes.
      for (const artefact of transition.artefacts as { ref?: string; scheme?: string }[]) {
        if (!artefact?.ref) continue
        const key = `artefact:${artefact.ref}`
        if (!nodes.has(key)) {
          nodes.set(key, {
            id: key,
            shape: 'artefact',
            act: null,
            trigger: transition.trigger,
            disposition: null,
            trajId: null,
            question: null,
            label: artefact.ref,
            attested: false,
            performed: transition.performed,
            cited: [],
          })
        }
        edges.push({ from: key, to: transition.id, kind: 'cites' })
      }
    }
  }

  for (const node of nodes.values()) {
    if (node.shape !== 'transition') continue
    const detail = node.trajId ? readTrajectoryDetail(root, slug, node.trajId) : null
    const transition = detail?.transitions.find((candidate) => candidate.id === node.id)
    for (const parent of transition?.parents ?? []) {
      if (!nodes.has(parent)) continue
      edges.push({
        from: parent,
        to: node.id,
        // A parent in another trajectory is the cross-link. Drawn differently
        // because it is the thing this view exists to show.
        kind: trajectoryOf.get(parent) === node.trajId ? 'follows' : 'crosses',
      })
    }
  }

  return { nodes: [...nodes.values()], edges }
}
