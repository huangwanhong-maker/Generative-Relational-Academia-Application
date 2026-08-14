/**
 * Making accounts, since the page will not.
 *
 * Registration is closed, so this is how a person comes to have a way in. It
 * is the operator's tool and is not reachable over HTTP.
 *
 * A caveat stated rather than glossed: when this command generates a keypair,
 * the private half exists in this process for as long as it takes to print it,
 * and the operator is trusted to hand it over and not keep it. That is weaker
 * than a key generated in the browser, which is what the sign-up flow does
 * when registration is open. Prefer `--party` with a key the person generated
 * themselves; generation here is a bootstrap convenience.
 */

import { resolve } from 'node:path'

import { generate } from '@gra/protocol'

import { Refused, createAccount } from './accounts.js'
import { openDatabase } from './database.js'
import { users } from './db.js'

const [action, name, ...rest] = process.argv.slice(2)
const flags = new Map<string, string>()
for (let i = 0; i < rest.length; i += 1) {
  const flag = rest[i]!
  if (flag.startsWith('--')) flags.set(flag.slice(2), rest[i + 1] ?? '')
}

const db = openDatabase(resolve(process.env['GRA_DB'] ?? 'data/index.sqlite'))

function usage(): never {
  console.log('usage: account add <name> [--password <p>] [--party key:ed25519:...]')
  console.log('       account list')
  process.exit(1)
}

try {
  if (action === 'list') {
    // By name. Any other ordering of participants ranks them, however it is
    // labelled, and there is no ordering of people here.
    const rows = await db.select().from(users)
    rows.sort((a, b) => a.name.localeCompare(b.name))
    for (const row of rows) console.log(`${row.name}  ${row.party}`)
    if (!rows.length) console.log('no accounts yet - account add <name>')
  } else if (action === 'add') {
    if (!name) usage()
    const password = flags.get('password') ?? ''
    if (password.length < 8) {
      console.error('--password of at least 8 characters is required')
      process.exit(1)
    }
    let party = flags.get('party') ?? ''
    let secret: string | null = null
    if (!party) {
      const keypair = generate()
      party = keypair.party
      secret = Buffer.from(keypair.secret).toString('base64url')
    }
    const account = await createAccount(db, { name, password, party })
    console.log(`${account.name} can sign in, and signs as ${account.party}`)
    if (secret) {
      console.log('')
      console.log('  Their private key, shown once and stored nowhere:')
      console.log(`    ${secret}`)
      console.log('')
      console.log('  Hand it to them and forget it. This server keeps only the public half,')
      console.log('  which is what makes an attestation from here worth anything.')
    }
  } else {
    usage()
  }
} catch (error) {
  console.error(error instanceof Refused ? error.message : error)
  process.exit(1)
}
