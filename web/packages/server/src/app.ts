/**
 * The HTTP surface.
 *
 * This is the contract another implementation would speak, so it is written as
 * the durable thing here and the browser client is written against it -- not
 * the other way round. Anything this server can do, a script can do, which is
 * what makes hosting somewhere else a real option rather than a promise (C10).
 *
 * What this API deliberately does not offer, because a screen is where the
 * temptation is strongest:
 *
 *   no quantity over participants or trajectories, no ordering by relevance,
 *   activity or size, and nothing marked principal, default or current;
 *   no operation that narrows disclosure and none that combines two states;
 *   no listing of who has an account here.
 */

import { readFileSync } from 'node:fs'
import { mkdir } from 'node:fs/promises'
import { join } from 'node:path'

import cookie from '@fastify/cookie'
import Fastify, { type FastifyInstance, type FastifyReply, type FastifyRequest } from 'fastify'

import { REGISTRATION_OPEN, Refused, authenticate, createAccount } from './accounts.js'
import { openDatabase, type Db } from './database.js'
import { getProject, listProjects, reindex, search, widenDisclosure } from './projects.js'
import { createRecord, slugify } from './records.js'
import { COOKIE, Sessions, type Session } from './sessions.js'

export interface Options {
  /** Where records live. Files, and they are the record. */
  recordsRoot: string
  /** Where the rebuildable index lives. `:memory:` for tests. */
  databaseFile: string
  sessions?: Sessions
  /** Serve the built browser client from here, when there is one. */
  clientRoot?: string
}

export interface App {
  fastify: FastifyInstance
  db: Db
  sessions: Sessions
}

declare module 'fastify' {
  interface FastifyRequest {
    session: Session | null
  }
}

export async function buildApp(options: Options): Promise<App> {
  const db = openDatabase(options.databaseFile)
  const sessions = options.sessions ?? new Sessions()
  await mkdir(options.recordsRoot, { recursive: true })
  await reindex(db, options.recordsRoot)

  const fastify = Fastify({ logger: false })
  await fastify.register(cookie)

  fastify.decorateRequest('session', null)
  fastify.addHook('onRequest', async (request) => {
    request.session = sessions.get(request.cookies[COOKIE])
  })

  const requireSession = async (request: FastifyRequest, reply: FastifyReply) => {
    if (!request.session) {
      await reply.code(401).send({ error: 'sign in first' })
    }
  }

  // --- who am I ------------------------------------------------------------

  fastify.get('/api/me', async (request) => {
    if (!request.session) return { signedIn: false, registrationOpen: REGISTRATION_OPEN }
    return {
      signedIn: true,
      registrationOpen: REGISTRATION_OPEN,
      name: request.session.name,
      party: request.session.party,
    }
  })

  fastify.post('/api/sign-in', async (request, reply) => {
    const body = request.body as { name?: string; password?: string }
    try {
      const account = await authenticate(db, body.name ?? '', body.password ?? '')
      const ticket = sessions.begin({
        userId: account.id,
        name: account.name,
        party: account.party,
      })
      // The cookie is an opaque ticket. Never the name, never the key.
      void reply.setCookie(COOKIE, ticket, {
        path: '/',
        httpOnly: true,
        sameSite: 'strict',
        secure: process.env['NODE_ENV'] === 'production',
      })
      return { name: account.name, party: account.party }
    } catch (error) {
      if (error instanceof Refused) return reply.code(401).send({ error: error.message })
      throw error
    }
  })

  fastify.post('/api/sign-out', async (request, reply) => {
    sessions.end(request.cookies[COOKIE])
    void reply.clearCookie(COOKIE, { path: '/' })
    return { signedIn: false }
  })

  fastify.post('/api/register', async (request, reply) => {
    if (!REGISTRATION_OPEN) {
      return reply.code(403).send({
        error:
          'Registration is closed on this server. An account is access to this host, not ' +
          'permission to take part: the record is plain files, and anyone can hold a copy, ' +
          'continue it under any implementation and verify it without an account here.',
      })
    }
    const body = request.body as { name?: string; password?: string; party?: string }
    try {
      const account = await createAccount(db, {
        name: body.name ?? '',
        password: body.password ?? '',
        party: body.party ?? '',
      })
      return { name: account.name, party: account.party }
    } catch (error) {
      if (error instanceof Refused) return reply.code(400).send({ error: error.message })
      throw error
    }
  })

  // --- records -------------------------------------------------------------

  /** Everything this viewer may see. By name. */
  fastify.get('/api/projects', async (request) => {
    const query = request.query as { mine?: string }
    const party = request.session?.party
    const all = await listProjects(db, party ? { viewerParty: party } : {})
    const listed = query.mine === '1' && party ? all.filter((p) => p.openedBy === party) : all
    return { projects: listed }
  })

  fastify.get('/api/projects/:slug', async (request, reply) => {
    const { slug } = request.params as { slug: string }
    const project = await getProject(db, slug)
    if (!project) return reply.code(404).send({ error: 'no record by that name here' })
    if (project.disclosure !== 'listed' && project.openedBy !== request.session?.party) {
      // Not "forbidden": the honest statement is that this viewer cannot see
      // it, not that it exists and is being withheld from them.
      return reply.code(404).send({ error: 'no record by that name here' })
    }
    return project
  })

  fastify.post('/api/projects', { onRequest: requireSession }, async (request, reply) => {
    const body = request.body as { title?: string; question?: string }
    const title = (body.title ?? '').trim()
    const question = (body.question ?? '').trim()
    if (!title || !question) {
      return reply.code(400).send({ error: 'a record needs a name and a question' })
    }
    const slug = slugify(title)
    const existing = await getProject(db, slug)
    if (existing) return reply.code(409).send({ error: `${slug} already exists here` })

    // The reference implementation decides what a record is. This server does
    // not construct a transition or compute an identifier.
    const created = await createRecord(
      options.recordsRoot,
      slug,
      question,
      request.session!.party,
    )
    if (!created.ok) {
      return reply.code(500).send({ error: created.stderr.trim() || created.stdout.trim() })
    }
    await reindex(db, options.recordsRoot)
    return reply.code(201).send(await getProject(db, slug))
  })

  /**
   * Widen what a record discloses. There is no route that narrows it, and
   * adding one would be adding an "unpublish" (C7).
   */
  fastify.post('/api/projects/:slug/disclose', { onRequest: requireSession }, async (request, reply) => {
    const { slug } = request.params as { slug: string }
    const project = await getProject(db, slug)
    if (!project) return reply.code(404).send({ error: 'no record by that name here' })
    if (project.openedBy !== request.session!.party) {
      return reply.code(403).send({ error: 'only the party who opened a record may widen it' })
    }
    await widenDisclosure(db, options.recordsRoot, slug)
    return getProject(db, slug)
  })

  // --- search --------------------------------------------------------------

  fastify.get('/api/search', async (request) => {
    const { q } = request.query as { q?: string }
    const party = request.session?.party
    const hits = await search(db, q ?? '', party ? { viewerParty: party } : {})
    return {
      query: q ?? '',
      hits,
      // Stated in the payload, not only in the interface, so that a second
      // client cannot present these as ranked without contradicting the API.
      ordering: 'by record, then by trajectory — search filters, it does not rank',
    }
  })

  fastify.post('/api/reindex', { onRequest: requireSession }, async () => {
    const counted = await reindex(db, options.recordsRoot)
    return { indexed: counted }
  })

  // --- the browser client --------------------------------------------------

  if (options.clientRoot) {
    const { default: fastifyStatic } = await import('@fastify/static')
    await fastify.register(fastifyStatic, { root: options.clientRoot, wildcard: false })
    const shell = readFileSync(join(options.clientRoot, 'index.html'), 'utf-8')
    fastify.setNotFoundHandler(async (request, reply) => {
      if (request.url.startsWith('/api/')) {
        return reply.code(404).send({ error: 'no such route' })
      }
      return reply.type('text/html').send(shell)
    })
  }

  return { fastify, db, sessions }
}
