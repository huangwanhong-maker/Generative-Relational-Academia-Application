/**
 * Accounts: a password in front of a public key.
 *
 * An account is **not** what makes a record credible, and being exact about
 * that is the whole discipline here, because every system with accounts
 * eventually starts treating them as the thing that matters.
 *
 *   An *identity* is a keypair. It signs. It is what attribution and
 *   attestation rest on, and it works with no server in the picture.
 *
 *   An *account* is a name and a password that let a person reach this server
 *   through a browser. It is access control. It signs nothing.
 *
 * The private key never arrives here. It is generated in the browser and stays
 * there; the server is told only the public half. That is not a policy anyone
 * has to trust -- there is no column it could be stored in.
 *
 * Registration is closed. A signed-up stranger is not a party to anything
 * until somebody registers their acts, so open sign-up would add accounts and
 * no credibility. Accounts are made by whoever runs the server.
 */

import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from 'node:crypto'
import { promisify } from 'node:util'

import { eq } from 'drizzle-orm'

import type { Db } from './database.js'
import { users } from './db.js'

const scrypt = promisify(scryptCallback) as (
  password: string,
  salt: Buffer,
  keylen: number,
) => Promise<Buffer>

/** Whether the sign-in page will make an account for a stranger. */
export const REGISTRATION_OPEN = false

const KEYLEN = 32
export const NAME_PATTERN = /^[a-z0-9][a-z0-9._-]{0,31}$/

export class Refused extends Error {}

export interface Account {
  id: number
  name: string
  party: string
  displayName: string | null
}

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16)
  const derived = await scrypt(password, salt, KEYLEN)
  return `scrypt$${salt.toString('base64url')}$${derived.toString('base64url')}`
}

async function matches(password: string, stored: string): Promise<boolean> {
  const [algorithm, salt, digest] = stored.split('$')
  if (algorithm !== 'scrypt' || !salt || !digest) return false
  const expected = Buffer.from(digest, 'base64url')
  const derived = await scrypt(password, Buffer.from(salt, 'base64url'), expected.length)
  return derived.length === expected.length && timingSafeEqual(derived, expected)
}

export async function createAccount(
  db: Db,
  input: { name: string; password: string; party: string; displayName?: string },
): Promise<Account> {
  const name = input.name.trim().toLowerCase()
  if (!NAME_PATTERN.test(name)) {
    throw new Refused(
      `${JSON.stringify(name)} will not do as a name: lower-case letters, digits, and . - _ , ` +
        'up to 32 characters. The name is for typing; the identity is the key, and nothing ' +
        'requires either to be your legal name.',
    )
  }
  if (input.password.length < 8) {
    throw new Refused(
      'a password of at least 8 characters. This guards browser access to this server; it ' +
        'does not guard the record, which is guarded by signatures.',
    )
  }
  if (!input.party.startsWith('key:ed25519:')) {
    throw new Refused('an account needs the public half of a keypair generated in your browser')
  }
  const row = {
    name,
    party: input.party,
    passwordHash: await hashPassword(input.password),
    displayName: input.displayName ?? null,
    createdAt: new Date().toISOString(),
  }
  try {
    const [created] = await db.insert(users).values(row).returning()
    return toAccount(created!)
  } catch (error) {
    if (String(error).includes('UNIQUE')) {
      throw new Refused(
        `there is already an account here under that name or that key. Two identities under ` +
          `one name would make the record say one party acted where two did.`,
      )
    }
    throw error
  }
}

/**
 * Check a name and password.
 *
 * Refuses with one sentence either way. Saying which half was wrong would
 * disclose who has an account here, which is a directory of participants by
 * another route.
 */
export async function authenticate(db: Db, name: string, password: string): Promise<Account> {
  const [row] = await db
    .select()
    .from(users)
    .where(eq(users.name, name.trim().toLowerCase()))
    .limit(1)
  // Hash regardless of whether the account exists, so a missing name and a
  // wrong password take about the same time.
  const stored = row?.passwordHash ?? `scrypt$${randomBytes(16).toString('base64url')}$${'A'.repeat(43)}`
  const ok = await matches(password, stored)
  if (!row || !ok) throw new Refused('that name and password do not go together')
  return toAccount(row)
}

export async function byName(db: Db, name: string): Promise<Account | null> {
  const [row] = await db.select().from(users).where(eq(users.name, name)).limit(1)
  return row ? toAccount(row) : null
}

function toAccount(row: typeof users.$inferSelect): Account {
  return { id: row.id, name: row.name, party: row.party, displayName: row.displayName }
}
