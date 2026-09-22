/**
 * Start the server.
 *
 * Binds to loopback unless told otherwise, because the default for something
 * holding other people's work should be the cautious one.
 */

import { existsSync } from 'node:fs'

import { buildApp } from './app.js'
import { runtimePaths } from './runtime.js'

const { recordsRoot, databaseFile, clientRoot } = runtimePaths()
const host = process.env['GRA_HOST'] ?? '127.0.0.1'
const port = Number(process.env['GRA_PORT'] ?? 8001)

const { fastify } = await buildApp({
  recordsRoot,
  databaseFile,
  ...(existsSync(clientRoot) ? { clientRoot } : {}),
})

await fastify.listen({ host, port })

console.log(`GRA on http://${host}:${port}/`)
console.log(`  records   ${recordsRoot}   <- retained research records and signing material.`)
console.log(`  accounts  ${databaseFile}  <- retained accounts plus rebuildable record indexes; back up the complete database.`)
if (!existsSync(clientRoot)) {
  console.log('  client    not built - API only. "npm run build --workspace @gra/client"')
}
console.log('  Registration is closed. Accounts: npm run account --workspace @gra/server -- add <name>')
