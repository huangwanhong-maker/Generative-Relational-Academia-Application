/**
 * Start the server.
 *
 * Binds to loopback unless told otherwise, because the default for something
 * holding other people's work should be the cautious one.
 */

import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

import { buildApp } from './app.js'

const recordsRoot = resolve(process.env['GRA_RECORDS'] ?? 'data/records')
const databaseFile = resolve(process.env['GRA_DB'] ?? 'data/index.sqlite')
const clientRoot = resolve(process.env['GRA_CLIENT'] ?? '../client/dist')
const host = process.env['GRA_HOST'] ?? '127.0.0.1'
const port = Number(process.env['GRA_PORT'] ?? 5173)

const { fastify } = await buildApp({
  recordsRoot,
  databaseFile,
  ...(existsSync(clientRoot) ? { clientRoot } : {}),
})

await fastify.listen({ host, port })

console.log(`GRA on http://${host}:${port}/`)
console.log(`  records   ${recordsRoot}   <- these are the record. The rest is derived.`)
console.log(`  index     ${databaseFile}  <- delete it any time; POST /api/reindex rebuilds it.`)
if (!existsSync(clientRoot)) {
  console.log('  client    not built - API only. "npm run build --workspace @gra/client"')
}
console.log('  Registration is closed. Accounts: npm run account --workspace @gra/server -- add <name>')
