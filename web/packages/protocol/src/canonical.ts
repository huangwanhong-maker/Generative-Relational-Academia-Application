/**
 * Canonical serialisation, hashing, and identifier construction.
 *
 * This is a **second implementation** of what `grrp/src/grrp/canonical.py`
 * already does in Python, and the two must agree on every byte. That is not
 * duplication for its own sake: a protocol nobody has implemented twice is a
 * protocol whose specification has not been tested. The shared vector file
 * (`vectors.json`, generated from Python) is what holds them together, and a
 * disagreement there is a specification bug, not a porting bug.
 *
 * Two independent things are hashed, and they are kept apart on purpose.
 *
 * *State content* is hashed over the exact bytes written to disk, so a state
 * file can be verified by anyone holding it with no knowledge of any tool.
 *
 * *Transition skeletons* are hashed over a canonical form of the covered
 * payload only, which excludes every field a later lawful operation may
 * change. Getting that exclusion wrong is the most likely serious bug here:
 * ordinary operation would begin invalidating signatures, and an
 * implementation would then either forbid the operation or ignore the failure.
 * Both defeat the purpose.
 */

import { sha256 } from '@noble/hashes/sha2.js'

export const CANONICALISATION = 'json-sorted/1'
export const HASH = 'sha256'

/**
 * Fields of a transition covered by its identifier. Everything not listed is
 * excluded by construction. Adding one changes every identifier in existence,
 * which is why the protocol version pins this list.
 */
export const COVERED_FIELDS = [
  'protocol',
  'kind',
  'trajectory',
  'parents',
  'prior_state',
  'posterior_state',
  'act',
  'target',
  'relation',
  'trigger',
  'disposition',
  'operation',
  'subject',
  'payload',
  'performer',
  'performed',
  'contributions',
  'absorption',
  'artefacts',
] as const

/** Fields explicitly excluded from the identifier and from any signature. */
export const EXCLUDED_FIELDS = ['id', 'registration', 'disclosure'] as const

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json }

const encoder = new TextEncoder()

/**
 * Sort by Unicode code point, which is what Python's `sort_keys` does.
 *
 * JavaScript's default `Array.sort` compares UTF-16 code units, so it orders
 * a non-BMP key before some BMP ones where Python orders it after. Every key
 * in the skeleton is ASCII today and the two agree, but `payload` is
 * open-ended, and a divergence there would produce a different identifier for
 * the same record on two machines -- which no test would catch until somebody
 * with a non-Latin key tried to verify a colleague's record.
 */
function byCodePoint(a: string, b: string): number {
  const left = [...a]
  const right = [...b]
  for (let i = 0; i < Math.min(left.length, right.length); i += 1) {
    const x = left[i]!.codePointAt(0)!
    const y = right[i]!.codePointAt(0)!
    if (x !== y) return x - y
  }
  return left.length - right.length
}

/**
 * Deterministic byte encoding of a JSON-compatible value.
 *
 * Written out rather than delegated to `JSON.stringify` with a replacer,
 * because the replacer form does not give control over key order for nested
 * objects on every engine, and because the failure it would produce is
 * silent: a record that verifies here and not elsewhere.
 */
export function canonicalText(value: Json): string {
  if (value === null) return 'null'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw new Error('NaN and Infinity have no canonical form and are refused')
    }
    // Integers only, in practice. A float would be a place where two
    // implementations could format the same value differently.
    return JSON.stringify(value)
  }
  if (typeof value === 'string') return JSON.stringify(value)
  if (Array.isArray(value)) {
    return `[${value.map(canonicalText).join(',')}]`
  }
  if (typeof value === 'object') {
    const keys = Object.keys(value).sort(byCodePoint)
    const parts = keys.map((key) => `${JSON.stringify(key)}:${canonicalText(value[key] as Json)}`)
    return `{${parts.join(',')}}`
  }
  throw new Error(`${typeof value} has no canonical form`)
}

export function canonicalBytes(value: Json): Uint8Array {
  return encoder.encode(canonicalText(value))
}

export function sha256Hex(data: Uint8Array): string {
  return Array.from(sha256(data), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * The whitespace stripped from the ends of lines and of the document.
 *
 * Named explicitly, and deliberately ASCII only. This began as `/\s+$/u` here
 * and as `rstrip()` in Python — the obvious spelling in each language — and
 * they disagree in both directions: `\s` matches U+FEFF and Python's does not,
 * while Python treats U+001C..U+001F as whitespace and `\s` does not. Two
 * implementations therefore computed two different identifiers for the same
 * document, which is the failure C10 cannot survive.
 *
 * ASCII, because that is implementable identically anywhere without a Unicode
 * table, and because a non-breaking or ideographic space at the end of a line
 * is plausibly something the author typed on purpose. Silently deleting it
 * would alter what somebody wrote.
 */
const TRAILING = /[ \t\n\v\f\r]+$/
const LEADING = /^[ \t\n\v\f\r]+/

/**
 * Normalise state content before it is hashed and written.
 *
 * Applied once, at creation. The bytes written are the bytes hashed, so a
 * holder of the file can verify the identifier without this function ever
 * having existed.
 */
export function normaliseContent(text: string): string {
  const joined = text
    .normalize('NFC')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .split('\n')
    .map((line) => line.replace(TRAILING, ''))
    .join('\n')
  return `${joined.replace(LEADING, '').replace(TRAILING, '')}\n`
}

/** Identifier of a state, over the exact bytes of its content file. */
export function stateId(content: string): string {
  return `state:${HASH}:${sha256Hex(encoder.encode(content))}`
}

/** The part of a transition record its identifier commits to. */
export function coveredPayload(record: Record<string, unknown>): Record<string, Json> {
  const covered: Record<string, Json> = {}
  for (const field of COVERED_FIELDS) {
    covered[field] = (record[field] ?? null) as Json
  }
  return covered
}

/**
 * Identifier of a transition, over its covered payload and parent ids.
 *
 * `parents` sits inside the covered payload, so identifiers chain: altering
 * an earlier transition invalidates every descendant, which is what makes the
 * log append-only in fact rather than by convention (C3).
 */
export function transitionId(record: Record<string, unknown>): string {
  return `${HASH}:${sha256Hex(canonicalBytes(coveredPayload(record)))}`
}

/**
 * The bytes a registrar signs.
 *
 * Covers the transition identifier -- and so its whole covered payload and its
 * parents -- the registrar, and the time of registration. It does not cover
 * disclosure, redaction marks, or the signature itself, because all three may
 * lawfully change afterwards.
 */
export function signingInput(id: string, registrar: string, time: string): Uint8Array {
  return canonicalBytes({ id, registrar, time })
}

/** Abbreviate an identifier for display. Never used for storage or lookup. */
export function short(identifier: string, length = 12): string {
  return identifier.split(':').pop()!.slice(0, length)
}
