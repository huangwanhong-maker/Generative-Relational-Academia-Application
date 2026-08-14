/**
 * Party identity: a keypair, and the operations over it.
 *
 * A party is identified by a public key. Nothing requires that a party
 * correspond to a natural person, that a person hold one key, or that a key be
 * connected to a legal name. What is required is *continuity*: the same
 * identifier across acts is what makes attribution meaningful and what makes
 * registration by a distinct party checkable.
 *
 * This module exists in TypeScript for one reason. If the server signs, the
 * server can forge, and an attestation from a host that holds both parties'
 * keys is bookkeeping rather than evidence. Signing therefore happens where
 * the key is, and the key belongs in the browser.
 */

import { ed25519 } from '@noble/curves/ed25519.js'

export const PREFIX = 'key:ed25519:'

export interface Keypair {
  /** The party identifier. Public, quotable, and safe to publish. */
  party: string
  /** Raw 32 bytes. Never transmitted, never logged, never persisted in clear. */
  secret: Uint8Array
}

export function b64url(raw: Uint8Array): string {
  let binary = ''
  for (const byte of raw) binary += String.fromCharCode(byte)
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export function unb64url(text: string): Uint8Array {
  const padded = text.replace(/-/g, '+').replace(/_/g, '/')
  const binary = atob(padded + '='.repeat((4 - (padded.length % 4)) % 4))
  return Uint8Array.from(binary, (character) => character.charCodeAt(0))
}

export function partyId(publicKey: Uint8Array): string {
  return PREFIX + b64url(publicKey)
}

export function publicKeyOf(party: string): Uint8Array {
  if (!party.startsWith(PREFIX)) {
    throw new Error(`a party identifier looks like ${PREFIX}<key>, not ${JSON.stringify(party)}`)
  }
  return unb64url(party.slice(PREFIX.length))
}

export function generate(): Keypair {
  const secret = ed25519.utils.randomSecretKey()
  return { party: partyId(ed25519.getPublicKey(secret)), secret }
}

export function fromSecret(secret: Uint8Array): Keypair {
  return { party: partyId(ed25519.getPublicKey(secret)), secret }
}

export function sign(secret: Uint8Array, data: Uint8Array): string {
  return b64url(ed25519.sign(data, secret))
}

/**
 * Whether `signature` over `data` was made by the holder of `party`.
 *
 * A false result means the record does not say what it appears to say. It does
 * not mean the content is wrong, and it does not mean the party who signed
 * understood what they were registering: an attestation asserts that an
 * identified party registered a transition at a time, and nothing more.
 */
export function verify(party: string, data: Uint8Array, signature: string): boolean {
  try {
    return ed25519.verify(unb64url(signature), data, publicKeyOf(party))
  } catch {
    // Any failure is a failure to verify. There is no partial credit.
    return false
  }
}
