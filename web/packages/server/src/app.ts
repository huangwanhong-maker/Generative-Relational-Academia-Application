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
import {
  createRecord,
  gitHistory,
  openQuestion,
  listFiles,
  readProjectFile,
  readTrajectoryDetail,
  slugify,
  trajectoryGraph,
  writeProjectFile,
} from './records.js'
import { COOKIE, Sessions, type Session } from './sessions.js'

export interface Options {
  /** Where records live. Files, and they are the record. */
  recordsRoot: string
  /**
   * Development aids: views of the substrate rather than of the record.
   *
   * Off in production on purpose. A commit is not a transition, and an
   * interface that showed them side by side would teach that git is where the
   * meaning lives. These exist to debug the thing, not to use it.
   */
  dev?: boolean
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

  // Room for a figure or a dataset. Not room for an archive: material this
  // server will not look inside belongs beside the record, not inside it.
  const fastify = Fastify({ logger: false, bodyLimit: 25 * 1024 * 1024 })
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

  const dev = options.dev ?? process.env['NODE_ENV'] !== 'production'

  fastify.get('/api/me', async (request) => {
    if (!request.session) return { signedIn: false, registrationOpen: REGISTRATION_OPEN, dev }
    return {
      signedIn: true,
      registrationOpen: REGISTRATION_OPEN,
      dev,
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
    if (!project) return reply.code(404).send({ error: 'no project by that name here' })
    if (project.disclosure !== 'listed' && project.openedBy !== request.session?.party) {
      // Not "forbidden": the honest statement is that this viewer cannot see
      // it, not that it exists and is being withheld from them.
      return reply.code(404).send({ error: 'no project by that name here' })
    }
    return project
  })

  fastify.post('/api/projects', { onRequest: requireSession }, async (request, reply) => {
    const body = request.body as { title?: string; description?: string }
    const title = (body.title ?? '').trim()
    if (!title) return reply.code(400).send({ error: 'a project needs a name' })

    const slug = slugify(title)
    const existing = await getProject(db, slug)
    if (existing) return reply.code(409).send({ error: `${slug} already exists here` })

    // A project is a container and starts empty. The question belongs a level
    // down, where a transition can attach to it (C4).
    const created = await createRecord(
      options.recordsRoot,
      slug,
      request.session!.party,
      body.description ?? '',
    )
    if (!created.ok) {
      return reply.code(500).send({ error: created.stderr.trim() || created.stdout.trim() })
    }
    await reindex(db, options.recordsRoot)
    return reply.code(201).send(await getProject(db, slug))
  })

  /**
   * Open a question, which is what starts a line of work.
   *
   * Separate from creating the project on purpose. A question anchors a
   * trajectory; a project holds trajectories. Nothing can be recorded in a
   * project with no question open, because a transition must reference an
   * identified prior state and there is not one yet.
   */
  fastify.post('/api/projects/:slug/questions', { onRequest: requireSession }, async (request, reply) => {
    const { slug } = request.params as { slug: string }
    const project = await getProject(db, slug)
    if (!project) return reply.code(404).send({ error: 'no project by that name here' })
    if (project.openedBy !== request.session!.party) {
      return reply.code(403).send({ error: 'only the party who created a project may open a question in it' })
    }
    const question = ((request.body as { question?: string }).question ?? '').trim()
    if (!question) return reply.code(400).send({ error: 'a question is the one thing needed' })

    const opened = await openQuestion(options.recordsRoot, slug, question)
    if (!opened.ok) {
      return reply.code(500).send({ error: opened.stderr.trim() || opened.stdout.trim() })
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
    if (!project) return reply.code(404).send({ error: 'no project by that name here' })
    if (project.openedBy !== request.session!.party) {
      return reply.code(403).send({ error: 'only the party who opened a project may widen it' })
    }
    await widenDisclosure(db, options.recordsRoot, slug)
    return getProject(db, slug)
  })

  /**
   * May this viewer see this project? Returns it, or null.
   *
   * Null means "no project by that name here", and the reply says exactly
   * that rather than "forbidden" -- confirming that something exists and is
   * being withheld is itself a disclosure.
   */
  const visible = async (slug: string, request: FastifyRequest) => {
    const project = await getProject(db, slug)
    if (!project) return null
    if (project.disclosure === 'listed' || project.openedBy === request.session?.party) {
      return project
    }
    return null
  }

  // --- one question, in full -----------------------------------------------

  fastify.get('/api/projects/:slug/trajectories/:trajId', async (request, reply) => {
    const { slug, trajId } = request.params as { slug: string; trajId: string }
    if (!(await visible(slug, request))) {
      return reply.code(404).send({ error: 'no project by that name here' })
    }
    const detail = readTrajectoryDetail(options.recordsRoot, slug, trajId)
    if (!detail) return reply.code(404).send({ error: 'no question by that name in this project' })
    return {
      ...detail,
      trajId,
      // Drawn by the reference implementation, so the picture and the record
      // cannot drift apart. Divergent branches are drawn identically and none
      // is marked principal, because nothing in the record designates one.
      graph: await trajectoryGraph(options.recordsRoot, slug, trajId),
    }
  })

  // --- the artefact plane ---------------------------------------------------

  fastify.get('/api/projects/:slug/files', async (request, reply) => {
    const { slug } = request.params as { slug: string }
    if (!(await visible(slug, request))) {
      return reply.code(404).send({ error: 'no project by that name here' })
    }
    return { files: listFiles(options.recordsRoot, slug) }
  })

  fastify.get('/api/projects/:slug/files/:name', async (request, reply) => {
    const { slug, name } = request.params as { slug: string; name: string }
    if (!(await visible(slug, request))) {
      return reply.code(404).send({ error: 'no project by that name here' })
    }
    try {
      const bytes = readProjectFile(options.recordsRoot, slug, name)
      if (!bytes) return reply.code(404).send({ error: 'no such file in this project' })
      return reply.type('application/octet-stream').send(bytes)
    } catch (error) {
      return reply.code(400).send({ error: String((error as Error).message) })
    }
  })

  /**
   * Store a file. **This records nothing.**
   *
   * No transition is written and no identifier is minted: C1 says no operation
   * exists merely so that a record exists, and a file arriving in a directory
   * is not a change in anyone's understanding. The digest comes back because
   * it is what a transition would cite to make this material part of the
   * record -- an act somebody has to perform deliberately, elsewhere.
   */
  fastify.post('/api/projects/:slug/files', { onRequest: requireSession }, async (request, reply) => {
    const { slug } = request.params as { slug: string }
    const project = await getProject(db, slug)
    if (!project) return reply.code(404).send({ error: 'no project by that name here' })
    if (project.openedBy !== request.session!.party) {
      return reply.code(403).send({ error: 'only the party who opened a project may add to it' })
    }
    const body = request.body as { name?: string; contentBase64?: string }
    if (!body.name || typeof body.contentBase64 !== 'string') {
      return reply.code(400).send({ error: 'a file needs a name and its bytes' })
    }
    try {
      const file = writeProjectFile(
        options.recordsRoot,
        slug,
        body.name,
        Buffer.from(body.contentBase64, 'base64'),
      )
      return reply.code(201).send({
        ...file,
        note:
          'Stored, and nothing was recorded. Cite this digest from a transition to make it ' +
          'part of the record.',
      })
    } catch (error) {
      return reply.code(400).send({ error: String((error as Error).message) })
    }
  })

  /**
   * The project's git history. Development only.
   *
   * A commit is not a transition. git supplies append-only history and the
   * transport by which a record is copied elsewhere; it supplies none of the
   * meaning, and a record in a directory that was never a repository is
   * exactly as valid. This is here to see what the substrate did, and it is
   * off in production so that nobody comes to read it as the record.
   */
  fastify.get('/api/projects/:slug/git', async (request, reply) => {
    if (!dev) return reply.code(404).send({ error: 'no such route' })
    const { slug } = request.params as { slug: string }
    if (!(await visible(slug, request))) {
      return reply.code(404).send({ error: 'no project by that name here' })
    }
    return gitHistory(options.recordsRoot, slug)
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
