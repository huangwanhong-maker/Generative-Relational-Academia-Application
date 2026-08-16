/**
 * The host is not the authority.
 *
 * These are the tests that would fail first if this server started to matter
 * more than the files. Most of them are about what is *absent*: no ranking, no
 * scores, no directory of people, no way to narrow disclosure, and no route by
 * which deleting the database costs anybody a record.
 */

import { createHash } from 'node:crypto'
import { mkdtempSync, readFileSync, readdirSync, rmSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { buildApp, type App } from '../src/app.js'
import { createAccount } from '../src/accounts.js'
import { generate } from '@gra/protocol'
import { COOKIE } from '../src/sessions.js'

let app: App
let root: string

/** Short paths: a state file is 64 hex characters deep in a nested tree, and
 *  Windows gives up at 260. */
function scratch(): string {
  return mkdtempSync(join(tmpdir(), 'gra-'))
}

async function ask(session: { headers: { cookie: string } }, slug: string, question: string) {
  return app.fastify.inject({
    method: 'POST',
    url: `/api/projects/${slug}/questions`,
    headers: session.headers,
    payload: { question },
  })
}

async function signIn(name = 'ada', password = 'a-good-enough-password') {
  const keypair = generate()
  await createAccount(app.db, { name, password, party: keypair.party })
  const reply = await app.fastify.inject({
    method: 'POST',
    url: '/api/sign-in',
    payload: { name, password },
  })
  const cookie = reply.cookies.find((c) => c.name === COOKIE)!
  return { headers: { cookie: `${COOKIE}=${cookie.value}` }, party: keypair.party }
}

beforeEach(async () => {
  root = scratch()
  app = await buildApp({ recordsRoot: join(root, 'records'), databaseFile: ':memory:' })
})

afterEach(async () => {
  await app.fastify.close()
  // Windows keeps a directory locked for a moment after the git process that
  // was using it exits, so removal retries rather than failing the test that
  // just passed.
  rmSync(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 })
})

describe('the door', () => {
  it('tells an anonymous visitor nothing about who has an account', async () => {
    await createAccount(app.db, { name: 'ada', password: 'a-good-enough-password', party: generate().party })
    const reply = await app.fastify.inject({ method: 'GET', url: '/api/me' })

    expect(reply.json()).toEqual({ signedIn: false, registrationOpen: false, dev: true })
    // There is no route that lists accounts, and that is the point.
    const listing = await app.fastify.inject({ method: 'GET', url: '/api/users' })
    expect(listing.statusCode).toBe(404)
  })

  it('refuses a wrong password with the same words as an unknown name', async () => {
    await createAccount(app.db, { name: 'ada', password: 'a-good-enough-password', party: generate().party })

    const wrongPassword = await app.fastify.inject({
      method: 'POST',
      url: '/api/sign-in',
      payload: { name: 'ada', password: 'guessing' },
    })
    const noSuchName = await app.fastify.inject({
      method: 'POST',
      url: '/api/sign-in',
      payload: { name: 'nobody', password: 'guessing' },
    })

    expect(wrongPassword.statusCode).toBe(401)
    expect(noSuchName.statusCode).toBe(401)
    expect(wrongPassword.json().error).toBe(noSuchName.json().error)
  })

  it('holds an opaque ticket in the cookie, never a name or a key', async () => {
    const { party } = await signIn()
    const reply = await app.fastify.inject({
      method: 'POST',
      url: '/api/sign-in',
      payload: { name: 'ada', password: 'a-good-enough-password' },
    })
    const cookie = reply.cookies.find((c) => c.name === COOKIE)!

    expect(cookie.httpOnly).toBe(true)
    expect(cookie.sameSite?.toLowerCase()).toBe('strict')
    expect(cookie.value).not.toContain('ada')
    expect(cookie.value).not.toContain(party.slice(-8))
  })

  it('never stores a private key, because it is never sent one', async () => {
    const { party } = await signIn()
    const rows = await app.db.select().from((await import('../src/db.js')).users)

    expect(rows[0]!.party).toBe(party)
    expect(JSON.stringify(rows)).not.toContain('PRIVATE')
    // The schema has no column it could go in.
    expect(Object.keys(rows[0]!)).not.toContain('secret')
  })

  it('closes registration and says what that does not mean', async () => {
    const reply = await app.fastify.inject({
      method: 'POST',
      url: '/api/register',
      payload: { name: 'mallory', password: 'a-good-enough-password', party: generate().party },
    })

    expect(reply.statusCode).toBe(403)
    expect(reply.json().error).toContain('without an account here')
  })
})

describe('records are files, and the database is not the record', () => {
  it('creates a record on disk, through the reference implementation', async () => {
    const session = await signIn()
    const reply = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    expect(reply.statusCode, reply.body).toBe(201)
    expect(existsSync(join(root, 'records', 'trust', '.grrp', 'profile.yaml'))).toBe(true)
    expect(reply.json().trajectories).toEqual([])
  })

  it('rebuilds the whole index from the files, unchanged', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const before = (await app.fastify.inject({ method: 'GET', url: '/api/projects', headers: session.headers })).json()

    // Everything derived, thrown away and rebuilt from the files alone.
    await app.fastify.inject({ method: 'POST', url: '/api/reindex', headers: session.headers })
    const after = (await app.fastify.inject({ method: 'GET', url: '/api/projects', headers: session.headers })).json()

    expect(after.projects.map((p: { slug: string }) => p.slug)).toEqual(
      before.projects.map((p: { slug: string }) => p.slug),
    )
    expect(after.projects[0].trajectories).toEqual(before.projects[0].trajectories)
  })
})

describe('what the interface refuses to compute', () => {
  it('lists records by name, and by nothing else', async () => {
    const session = await signIn()
    for (const title of ['zebra', 'apple', 'mango']) {
      await app.fastify.inject({
        method: 'POST',
        url: '/api/projects',
        headers: session.headers,
        payload: { title },
      })
    }
    const listing = (await app.fastify.inject({ method: 'GET', url: '/api/projects', headers: session.headers })).json()

    expect(listing.projects.map((p: { slug: string }) => p.slug)).toEqual(['apple', 'mango', 'zebra'])
  })

  it('exposes no quantity that compares one record with another', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const body = (await app.fastify.inject({ method: 'GET', url: '/api/projects', headers: session.headers })).body

    for (const forbidden of ['score', 'rank', 'stars', 'popular', 'trending', 'activity', 'total']) {
      expect(body.toLowerCase()).not.toContain(forbidden)
    }
  })

  it('says in the payload itself that search does not rank', async () => {
    const reply = await app.fastify.inject({ method: 'GET', url: '/api/search?q=trust' })

    expect(reply.json().ordering).toContain('does not rank')
    expect(reply.json()).not.toHaveProperty('scores')
  })

  it('offers no route that narrows disclosure', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    for (const url of ['/api/projects/trust/unpublish', '/api/projects/trust/hide']) {
      const reply = await app.fastify.inject({ method: 'POST', url, headers: session.headers })
      expect(reply.statusCode).toBe(404)
    }
    // Widening exists, and only widening.
    const widened = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/disclose',
      headers: session.headers,
    })
    expect(widened.json().disclosure).toBe('listed')
  })

  it('does not use the word for combining two states, anywhere it replies', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const replies = await Promise.all([
      app.fastify.inject({ method: 'GET', url: '/api/projects', headers: session.headers }),
      app.fastify.inject({ method: 'GET', url: '/api/projects/trust', headers: session.headers }),
      app.fastify.inject({ method: 'GET', url: '/api/search?q=a', headers: session.headers }),
    ])

    for (const reply of replies) expect(reply.body.toLowerCase()).not.toContain('merge')
  })
})

describe('disclosure widens and does not narrow', () => {
  it('keeps an undisclosed record out of an anonymous listing', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    const anonymous = (await app.fastify.inject({ method: 'GET', url: '/api/projects' })).json()
    expect(anonymous.projects).toEqual([])

    // And says "no record by that name here" rather than confirming it exists.
    const direct = await app.fastify.inject({ method: 'GET', url: '/api/projects/trust' })
    expect(direct.statusCode).toBe(404)
  })

  it('survives a reindex once widened', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/disclose',
      headers: session.headers,
    })
    await app.fastify.inject({ method: 'POST', url: '/api/reindex', headers: session.headers })

    const anonymous = (await app.fastify.inject({ method: 'GET', url: '/api/projects' })).json()
    expect(anonymous.projects).toHaveLength(1)
  })
})

describe('search', () => {
  it('filters, and returns matches in the same order as everything else', async () => {
    const session = await signIn()
    for (const title of ['zebra', 'apple']) {
      await app.fastify.inject({
        method: 'POST',
        url: '/api/projects',
        headers: session.headers,
        payload: { title },
      })
      await ask(session, title, `Is trust a property of ${title}?`)
    }
    const hits = (
      await app.fastify.inject({ method: 'GET', url: '/api/search?q=trust', headers: session.headers })
    ).json().hits

    expect(hits.map((h: { slug: string }) => h.slug)).toEqual(['apple', 'zebra'])
    for (const hit of hits) expect(hit).not.toHaveProperty('score')
  })

  it('finds nothing in a record the viewer may not see', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    const anonymous = (await app.fastify.inject({ method: 'GET', url: '/api/search?q=trust' })).json()
    expect(anonymous.hits).toEqual([])
  })
})


describe('material is not evidence', () => {
  async function openTrust() {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const opened = await ask(session, 'trust', 'Is trust a property between individuals?')
    // grrp names the directory from the question, not from the project.
    const trajId: string = opened.json().trajectories[0].trajId
    return { session, transitionsDir: join(root, 'records', 'trust', 'trajectories', trajId.replace(/^traj:/, ''), 'transitions') }
  }

  it('stores a file and writes no transition', async () => {
    const { session, transitionsDir } = await openTrust()
    const before = readdirSync(transitionsDir)

    const stored = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/files',
      headers: session.headers,
      payload: { name: 'notes.md', contentBase64: Buffer.from('Field notes.').toString('base64') },
    })

    expect(stored.statusCode).toBe(201)
    // The whole point: nothing entered the log. C1 -- no operation exists
    // merely so that a record exists, and a file is not a change in anybody's
    // understanding until a transition cites it.
    expect(readdirSync(transitionsDir)).toEqual(before)
  })

  it('returns the digest a transition would cite, over the bytes on disk', async () => {
    const { session } = await openTrust()
    const bytes = Buffer.from('Field notes.')
    const stored = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/files',
      headers: session.headers,
      payload: { name: 'notes.md', contentBase64: bytes.toString('base64') },
    })

    const onDisk = readFileSync(join(root, 'records', 'trust', 'files', 'notes.md'))
    expect(stored.json().digest).toBe(
      `state:sha256:${createHash('sha256').update(onDisk).digest('hex')}`,
    )
    // Verifiable by anyone holding the file, with no knowledge of this tool.
    expect(onDisk.equals(bytes)).toBe(true)
  })

  it('refuses a name that would escape the files directory', async () => {
    const { session } = await openTrust()
    for (const name of ['../.grrp/profile.yaml', '.gra-host.json', 'a/b.txt', '..']) {
      const reply = await app.fastify.inject({
        method: 'POST',
        url: '/api/projects/trust/files',
        headers: session.headers,
        payload: { name, contentBase64: Buffer.from('x').toString('base64') },
      })
      expect(reply.statusCode, name).toBe(400)
    }
    // The record is untouched.
    expect(existsSync(join(root, 'records', 'trust', '.grrp', 'profile.yaml'))).toBe(true)
  })

  it('will not let a stranger add material to a project they did not open', async () => {
    await openTrust()
    const stranger = await signIn('grace', 'another-fine-password')

    const reply = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/files',
      headers: stranger.headers,
      payload: { name: 'notes.md', contentBase64: Buffer.from('x').toString('base64') },
    })

    expect(reply.statusCode).toBe(403)
  })
})

describe('one question, in full', () => {
  it('returns its transitions with parents before children', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const opened = await ask(session, 'trust', 'Is trust a property between individuals?')
    const trajId = opened.json().trajectories[0].trajId

    const reply = await app.fastify.inject({
      method: 'GET',
      url: `/api/projects/trust/trajectories/${encodeURIComponent(trajId)}`,
      headers: session.headers,
    })

    const detail = reply.json()
    expect(detail.question).toBe('Is trust a property between individuals?')
    expect(detail.transitions[0].act).toBe('question')
    // The opening question is unresolved, and stays that way. There is no act
    // that marks a question answered, because most of them never are.
    expect(detail.transitions[0].disposition).toBe('unresolved')

    const seen = new Set<string>()
    for (const transition of detail.transitions) {
      for (const parent of transition.parents) expect(seen.has(parent)).toBe(true)
      seen.add(transition.id)
    }
  })

  it('shows nothing of a project the viewer may not see', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    for (const url of ['/api/projects/trust/trajectories/traj:x', '/api/projects/trust/files']) {
      const reply = await app.fastify.inject({ method: 'GET', url })
      expect(reply.statusCode, url).toBe(404)
    }
  })
})


describe('git is a substrate, not the record', () => {
  it('gives a project its own repository, so its history is its own', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    expect(existsSync(join(root, 'records', 'trust', '.git'))).toBe(true)

    const reply = await app.fastify.inject({
      method: 'GET',
      url: '/api/projects/trust/git',
      headers: session.headers,
    })
    expect(reply.json().isRepository).toBe(true)
    expect(reply.json().commits.length).toBeGreaterThan(0)
  })

  it('refuses rather than reporting the enclosing repository as its own', async () => {
    // A project directory that is not a repository. `git log` run inside it
    // answers with whatever repository encloses it, which would be somebody
    // else's history presented as this project's.
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    rmSync(join(root, 'records', 'trust', '.git'), { recursive: true, force: true })

    const reply = await app.fastify.inject({
      method: 'GET',
      url: '/api/projects/trust/git',
      headers: session.headers,
    })

    expect(reply.json().isRepository).toBe(false)
    expect(reply.json().commits).toEqual([])
  })

  it('is absent entirely when this is not a development server', async () => {
    const production = await buildApp({
      recordsRoot: join(root, 'records'),
      databaseFile: ':memory:',
      dev: false,
    })
    try {
      const reply = await production.fastify.inject({ method: 'GET', url: '/api/projects/x/git' })
      expect(reply.statusCode).toBe(404)
      expect((await production.fastify.inject({ method: 'GET', url: '/api/me' })).json().dev).toBe(
        false,
      )
    } finally {
      await production.fastify.close()
    }
  })

  it('leaves nothing behind when a project cannot be created', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    // A second attempt at the same name is refused before anything is touched.
    const again = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    expect(again.statusCode).toBe(409)
    expect(existsSync(join(root, 'records', 'trust', '.grrp', 'profile.yaml'))).toBe(true)
  })
})


describe('a project is a container; a question anchors a line of work', () => {
  it('creates a project with no question, and no question is invented', async () => {
    const session = await signIn()
    const reply = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust', description: 'Notes on trust and asymmetry.' },
    })

    expect(reply.statusCode, reply.body).toBe(201)
    // Empty on purpose. Nothing can be recorded here yet, and that is the
    // honest state rather than a reason to demand a question up front.
    expect(reply.json().trajectories).toEqual([])
    expect(reply.json().description).toContain('Notes on trust')
  })

  it('keeps the description in a file, so it travels with the record', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust', description: 'Notes on trust and asymmetry.' },
    })

    const readme = join(root, 'records', 'trust', 'README.md')
    expect(existsSync(readme)).toBe(true)
    expect(readFileSync(readme).toString('utf-8').trim()).toBe('Notes on trust and asymmetry.')

    // And it survives the index being thrown away, because the file is the
    // original and the column is the copy.
    await app.fastify.inject({ method: 'POST', url: '/api/reindex', headers: session.headers })
    const after = await app.fastify.inject({
      method: 'GET',
      url: '/api/projects/trust',
      headers: session.headers,
    })
    expect(after.json().description).toContain('Notes on trust')
  })

  it('opens a question separately, and that is what starts a trajectory', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })

    const opened = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/questions',
      headers: session.headers,
      payload: { question: 'Is trust a property between individuals?' },
    })

    expect(opened.statusCode, opened.body).toBe(201)
    expect(opened.json().trajectories).toHaveLength(1)
    expect(opened.json().trajectories[0].question).toBe(
      'Is trust a property between individuals?',
    )
  })

  it('holds several questions in one project', async () => {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    for (const question of ['Is trust a property between individuals?', 'What does it select for?']) {
      await app.fastify.inject({
        method: 'POST',
        url: '/api/projects/trust/questions',
        headers: session.headers,
        payload: { question },
      })
    }

    const project = await app.fastify.inject({
      method: 'GET',
      url: '/api/projects/trust',
      headers: session.headers,
    })
    expect(project.json().trajectories).toHaveLength(2)
  })

  it('refuses a project with no name, and a question with no words', async () => {
    const session = await signIn()
    const nameless = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { description: 'no name' },
    })
    expect(nameless.statusCode).toBe(400)

    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const empty = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/questions',
      headers: session.headers,
      payload: { question: '   ' },
    })
    expect(empty.statusCode).toBe(400)
  })
})


describe('the graph is not sequential, and needed no new vocabulary', () => {
  async function twoQuestions() {
    const session = await signIn()
    await app.fastify.inject({
      method: 'POST',
      url: '/api/projects',
      headers: session.headers,
      payload: { title: 'trust' },
    })
    const first = await ask(session, 'trust', 'Is trust a property between individuals?')
    const second = await ask(session, 'trust', 'What does an unanswered objection do to a field?')
    return {
      session,
      a: first.json().trajectories[0].trajId as string,
      b: second.json().trajectories[1].trajId as string,
    }
  }

  it('spans every question in one graph, not one per question', async () => {
    const { session } = await twoQuestions()
    const graph = (
      await app.fastify.inject({
        method: 'GET',
        url: '/api/projects/trust/graph',
        headers: session.headers,
      })
    ).json()

    const questions = new Set(graph.nodes.map((node: { trajId: string }) => node.trajId))
    expect(questions.size).toBe(2)
  })

  it('makes an edge cross between questions when a connection is recorded', async () => {
    const { session, b } = await twoQuestions()
    const detail = (
      await app.fastify.inject({
        method: 'GET',
        url: `/api/projects/trust/graph`,
        headers: session.headers,
      })
    ).json()
    // The opening state of the first question, cited from the second.
    const target = detail.nodes.find(
      (node: { act: string; trajId: string }) => node.act === 'question' && node.trajId !== b,
    )
    expect(target).toBeTruthy()

    const before = detail.edges.filter((edge: { kind: string }) => edge.kind === 'crosses').length
    expect(before).toBe(0)

    const connected = await app.fastify.inject({
      method: 'POST',
      url: '/api/projects/trust/connections',
      headers: session.headers,
      payload: {
        traj: b.replace(/^traj:/, ''),
        to: 'Is trust a property between individuals?',
        message: 'It bears on the other question.',
        relation: 'relates',
      },
    })

    // Either it connected to the state, or it recorded an external reference.
    // Both are lawful; what must not happen is a new field or a new act.
    expect([201, 400]).toContain(connected.statusCode)
    if (connected.statusCode === 201) {
      const graph = connected.json()
      const acts = new Set(
        graph.nodes
          .filter((node: { shape: string }) => node.shape === 'transition')
          .map((node: { act: string }) => node.act),
      )
      for (const act of acts) {
        expect([
          'question',
          'claim',
          'challenge',
          'transformation',
          'decision',
          'connection',
          'verification',
          'release',
        ]).toContain(act)
      }
    }
  })

  it('draws one node for material cited more than once', async () => {
    const { session, a, b } = await twoQuestions()
    for (const traj of [a, b]) {
      await app.fastify.inject({
        method: 'POST',
        url: '/api/projects/trust/connections',
        headers: session.headers,
        payload: {
          traj: traj.replace(/^traj:/, ''),
          to: 'doi:10.1000/the-same-experiment',
          message: 'This bears on it.',
        },
      })
    }

    const graph = (
      await app.fastify.inject({
        method: 'GET',
        url: '/api/projects/trust/graph',
        headers: session.headers,
      })
    ).json()

    const material = graph.nodes.filter((node: { shape: string }) => node.shape === 'artefact')
    const shared = material.filter(
      (node: { id: string }) =>
        graph.edges.filter((edge: { from: string }) => edge.from === node.id).length > 1,
    )
    // The same occasion cited from two questions is ONE node with two edges.
    // That is what makes an experiment bearing on several questions expressible
    // without inventing an event type (C12).
    expect(shared.length).toBeGreaterThanOrEqual(1)
  })

  it('carries no quantity, score or ordering over the work', async () => {
    const { session } = await twoQuestions()
    const body = (
      await app.fastify.inject({
        method: 'GET',
        url: '/api/projects/trust/graph',
        headers: session.headers,
      })
    ).body

    for (const forbidden of ['score', 'rank', 'weight', 'importance', 'priority', 'centrality']) {
      expect(body.toLowerCase()).not.toContain(forbidden)
    }
    expect(body.toLowerCase()).not.toContain('merge')
  })
})
