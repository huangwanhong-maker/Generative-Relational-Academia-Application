/**
 * Build the demonstration project: every node kind and every edge kind the
 * specification names, in one record that reads like real work.
 *
 *   npx tsx tools/demo.ts          # server must be running (npm run dev)
 *
 * What it exercises, deliberately:
 *   transitions   question · claim · challenge (unresolved AND contested) ·
 *                 transformation · decision (incl. an abandoned path) ·
 *                 verification (passed AND failed) · release · connection
 *   edges         follows · crosses (between questions) · cites ·
 *                 reified connections incl. a multi-parent one (the lawful
 *                 neighbour of combining, which is refused)
 *   materials     held artefacts by hash · external works (doi, arxiv, url)
 *   occasions     a meeting (minutes cited from two questions, trigger
 *                 discussion) · an experiment (run log, trigger experiment)
 *   registration  one attested transition — performed by one key, registered
 *                 by another (C2), via the group-tier proposal flow
 *   workspaces    seeded on a transition and on the meeting artefact
 *
 * Every transition goes through grrp; this script never writes one itself.
 * Two things do NOT go through grrp, because grrp has no command for them
 * yet, and saying so beats pretending: the tier switch hand-edits
 * profile.yaml (no `grrp tier` exists — an M3 gap), and the second keypair is
 * minted with grrp's own keys module (no second-party keygen command exists;
 * the tests do the same). Both are flagged where they happen.
 */

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

const BASE = process.env.GRA_BASE ?? 'http://127.0.0.1:5173'
const ROOT = resolve(import.meta.dirname, '../packages/server/data')
const SLUG = 'field-memory'
const DIR = join(ROOT, 'records', SLUG)

/* ------------------------------------------------------------------ helpers */

function grrp(args: string[], env: Record<string, string> = {}): string {
  return execFileSync('grrp', args, {
    cwd: DIR,
    env: { ...process.env, ...env },
    encoding: 'utf-8',
  })
}

/** The digest grrp will give simple one-paragraph content (its normalisation
 *  reduces to trim + newline for plain ASCII), so connections can name their
 *  target without parsing log output. */
function digestOf(text: string): string {
  return createHash('sha256').update(`${text.trim()}\n`, 'utf-8').digest('hex')
}

let cookie = ''
async function call(method: string, path: string, body?: unknown) {
  const reply = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', cookie },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const setCookie = reply.headers.get('set-cookie')
  if (setCookie) cookie = setCookie.split(';')[0]!
  const text = await reply.text()
  if (!reply.ok) throw new Error(`${method} ${path} → ${reply.status}: ${text.slice(0, 200)}`)
  return text ? JSON.parse(text) : {}
}

async function ensureAccount(name: string, password: string) {
  try {
    await call('POST', '/api/sign-in', { name, password })
    console.log(`  ${name}: signed in`)
  } catch {
    const { openDatabase } = await import('../packages/server/src/database.js')
    const { createAccount } = await import('../packages/server/src/accounts.js')
    const { generate } = await import('@gra/protocol')
    const db = openDatabase(join(ROOT, 'index.sqlite'))
    await createAccount(db, { name, password, party: generate().party })
    await call('POST', '/api/sign-in', { name, password })
    console.log(`  ${name}: account made, signed in`)
  }
}

/* --------------------------------------------------------------------- build */

const Q1 = 'How does a research field forget its own negative results?'
const Q2 = 'What makes a replication attempt credible to outsiders?'
const Q3 = 'Do citation practices preserve or erase dissent?'

// content, named once so digests can be computed for connections
const A1 = 'Negative results are not lost; they are never indexed in the first place.'
const C1 = 'Archives do index some of them. What is missing is any reason to read them: nobody is credited for engaging with a negative result.'
const T1 = 'Negative results vanish because no venue makes reading them creditable. Indexing is necessary but nowhere near sufficient.'
const DIV = 'Forgetting is an artefact of citation half-life, not of indexing at all.'
const B1 = 'A replication is credible to outsiders when its protocol was fixed before its outcome was known.'
const D1 = 'Do citation practices reward agreement chains at the expense of recorded dissent?'

const MINUTES = `# Lab meeting — 12 August 2026

Standing question: indexing versus credit as the mechanism of forgetting.

Agreed to refine rather than abandon the indexing claim; the credit half is
now the live end. Replication-credibility criteria set for the audit sample.
`
const RUNLOG = `finding_id,indexed_anywhere,venue_count
f-001,yes,2
f-002,no,0
f-003,no,0
f-004,yes,1
# … 40 rows in the sampled audit; 12 of 40 indexed.
`

async function main() {
  console.log('accounts:')
  await ensureAccount('noor', 'a-quiet-reviewer')
  await ensureAccount('ada', 'a-good-enough-password')

  if (existsSync(DIR)) {
    console.log(`\n${SLUG} already exists — reindexing only. Delete the folder to rebuild.`)
    await call('POST', '/api/reindex', {})
    return
  }

  console.log('\nproject:')
  await call('POST', '/api/projects', {
    title: 'field memory',
    description:
      '## Field memory\n\nHow a research field forgets — negative results, dissent, and the ' +
      'credit structures that decide what stays readable.\n\n*A demonstration record: every ' +
      'kind of node and edge the graph model names, built through `grrp` alone.*',
  })
  console.log(`  ${SLUG}: created`)

  console.log('\nquestions:')
  for (const q of [Q1, Q2, Q3]) {
    grrp(['new', q])
    console.log(`  ${q.slice(0, 56)}…`)
  }
  const trajDirs = readdirSync(join(DIR, 'trajectories'))
  const t1 = trajDirs.find((d) => d.startsWith('how-does'))!
  const t2 = trajDirs.find((d) => d.startsWith('what-makes'))!
  const t3 = trajDirs.find((d) => d.startsWith('do-citation'))!

  console.log('\nacts:')
  // Q1 — a position, an objection that stands, a refinement, a divergence, an
  // abandonment, a failed check.
  grrp(['claim', t1, '-m', A1, '--target', 'hypothesis', '--trigger', 'literature'])
  grrp(['challenge', '-t', t1, '-m', C1, '--target', 'assumption', '--trigger', 'discussion'])
  grrp(['transform', digestOf(A1).slice(0, 12), '-m', T1, '-t', t1, '--relation', 'refines', '--trigger', 'discussion'])
  grrp(['claim', digestOf(A1).slice(0, 12), '-m', DIV, '--trigger', 'self'])   // divergent sibling
  grrp(['decide', digestOf(DIV).slice(0, 12), '-t', t1, '--abandon', '-m',
    'Citation half-life alone cannot explain field-specific forgetting rates. Retiring this line; the divergence stays visible.'])
  grrp(['verify', digestOf(T1).slice(0, 12), '-t', t1, '--failed', '--trigger', 'experiment', '-m',
    'Sampled 40 abandoned findings: only 12 were indexed anywhere. The necessary condition fails more often than the refined claim assumed.'])
  console.log('  Q1: claim · challenge (standing) · transformation · divergence · abandonment · failed check')

  // Q2 — a position, a passed check, a release.
  grrp(['claim', t2, '-m', B1, '--target', 'method', '--trigger', 'literature'])
  grrp(['verify', '-t', t2, '--trigger', 'literature', '-m',
    'Across the audit sample, pre-registered protocols were treated as credible by outside groups roughly three times as often as post-hoc ones.'])
  grrp(['release', '-t', t2])
  console.log('  Q2: claim · passed check · release')

  // Q3 — a position and a contested objection.
  grrp(['claim', t3, '-m', 'Citation practices erase dissent by rewarding agreement chains.', '--trigger', 'literature'])
  grrp(['challenge', '-t', t3, '-m',
    'Dissenting citations exist; they are simply rarer. Erasure overstates what is better described as attenuation.',
    '--disposition', 'contested', '--trigger', 'objection'])
  console.log('  Q3: claim · contested objection')

  console.log('\nmaterial and occasions:')
  mkdirSync(join(DIR, 'files'), { recursive: true })
  writeFileSync(join(DIR, 'files', 'minutes-2026-08-12.md'), MINUTES, 'utf-8')
  writeFileSync(join(DIR, 'files', 'runlog-indexing-audit.csv'), RUNLOG, 'utf-8')
  const minutesHash = createHash('sha256').update(readFileSync(join(DIR, 'files', 'minutes-2026-08-12.md'))).digest('hex')
  const runlogHash = createHash('sha256').update(readFileSync(join(DIR, 'files', 'runlog-indexing-audit.csv'))).digest('hex')

  // The meeting: one minutes file, cited from two questions with trigger
  // discussion — one shared node, two lines of work, no roster anywhere.
  grrp(['connect', '-t', t1, '--to', `state:sha256:${minutesHash}`, '--relation', 'relates', '--trigger', 'discussion', '-m',
    'Lab meeting outcome: refine the indexing claim rather than abandon it — the credit half is the live end.'])
  grrp(['connect', '-t', t2, '--to', `state:sha256:${minutesHash}`, '--relation', 'relates', '--trigger', 'discussion', '-m',
    'The same meeting fixed the credibility criteria for the replication audit.'])
  // The experiment: the run log behind the failed check.
  grrp(['connect', '-t', t1, '--to', `state:sha256:${runlogHash}`, '--relation', 'usesDataFrom', '--trigger', 'experiment', '-m',
    'The 40-finding indexing sample behind the failed check.'])
  console.log('  meeting minutes (cited from two questions) · experiment run log')

  console.log('\nconnections across and outward:')
  // Crosses between questions: Q2's line supports Q1's refined claim.
  grrp(['connect', '-t', t2, '--to', digestOf(T1).slice(0, 12), '--relation', 'supports', '--trigger', 'discussion', '-m',
    'Credibility criteria decide who bothers to read negative results at all — the two questions share a mechanism.'])
  // A reply to the standing objection: concession in part. Multi-parent.
  grrp(['connect', '-t', t1, '--to', digestOf(C1).slice(0, 12), '--relation', 'repliesTo', '--trigger', 'self', '-m',
    'Conceded in part: indexing exists. The credit half of the objection is the part still standing.'])
  // External works: doi, arxiv, url.
  grrp(['connect', '-t', t1, '--to', 'doi:10.1126/science.aac4716', '--relation', 'disputes', '--trigger', 'literature', '-m',
    'The reproducibility project reads as though indexing suffices; the audit sample disagrees.'])
  grrp(['connect', '-t', t2, '--to', 'arxiv:1602.05593', '--relation', 'usesMethodIn', '--trigger', 'literature', '-m',
    'Pre-registration audit method adapted from this survey design.'])
  grrp(['connect', '-t', t3, '--to', 'https://retractionwatch.com', '--relation', 'usesDataFrom', '--trigger', 'observation', '-m',
    'Retraction notices as a proxy corpus for dissent that left the record.'])
  console.log('  crosses · repliesTo (multi-parent) · doi · arxiv · url')

  console.log('\nattestation (C2 — a second key registers):')
  const profilePath = join(DIR, '.grrp', 'profile.yaml')
  writeFileSync(profilePath, readFileSync(profilePath, 'utf-8').replace('tier: personal', 'tier: group'), 'utf-8')
  execFileSync('python', ['-c',
    "from pathlib import Path; from grrp import keys; keys.generate(Path('.grrp/keys'), 'noor')"],
    { cwd: DIR, encoding: 'utf-8' })
  grrp(['decide', digestOf(B1).slice(0, 12), '-t', t2, '-m',
    'Adopt pre-registration as the standing criterion for replications this project runs itself.'])
  const pending = grrp(['pending'])
  const proposal = pending.match(/[0-9a-f]{12}/)?.[0]
  if (proposal) {
    grrp(['register', proposal], { GRRP_KEY: 'noor' })
    console.log('  one decision performed by self, registered by noor — attested')
  } else {
    console.log('  (no proposal surfaced — skipped)')
  }
  writeFileSync(profilePath, readFileSync(profilePath, 'utf-8').replace('tier: group', 'tier: personal'), 'utf-8')

  console.log('\nworkspaces (applicative — recorded nowhere):')
  const transitions = readdirSync(join(DIR, 'trajectories', t1, 'transitions'))
  for (const name of transitions) {
    const yaml = readFileSync(join(DIR, 'trajectories', t1, 'transitions', name), 'utf-8')
    if (yaml.includes(digestOf(T1))) {
      const area = join(DIR, 'nodes', 't', name.replace(/\.yaml$/, ''))
      mkdirSync(area, { recursive: true })
      writeFileSync(join(area, 'dossier.md'),
        '# Working dossier\n\nDraft framings for the credit-side mechanism; nothing here is recorded.\n', 'utf-8')
    }
  }
  const meetingArea = join(DIR, 'nodes', 'a', minutesHash)
  mkdirSync(meetingArea, { recursive: true })
  writeFileSync(join(meetingArea, 'agenda.md'), '# Agenda\n\n1. indexing vs credit\n2. replication criteria\n', 'utf-8')
  console.log('  dossier on the refined claim · agenda beside the minutes')

  await call('POST', '/api/projects/field-memory/disclose', {})
  await call('POST', '/api/reindex', {})
  const checked = grrp(['check'])
  console.log('
grrp check:', checked.trim().split('
').pop())
  const graph = await call('GET', '/api/projects/field-memory/graph')
  const kinds = { follows: 0, crosses: 0, cites: 0 } as Record<string, number>
  for (const e of graph.edges) kinds[e.kind] = (kinds[e.kind] ?? 0) + 1
  console.log(`\ndone: ${graph.nodes.length} nodes · edges ${JSON.stringify(kinds)} · shared on this server`)
  console.log(`sign in as ada / a-good-enough-password → ${BASE}/p/field-memory?tab=trajectories`)
}

main().catch((error) => {
  console.error(String(error))
  process.exit(1)
})
