/**
 * The two implementations must agree, byte for byte.
 *
 * These vectors are generated from the Python reference implementation by
 * `grrp/tools/make_vectors.py`. Nothing here is written by hand, and nothing
 * here should ever be "adjusted to match" — a failure means Python and
 * TypeScript disagree about what a record's identifier is, which means a
 * record recorded on one would not verify on the other, which means C10 is
 * false. The fix belongs in whichever side turns out to be wrong about the
 * specification, and often in the specification itself.
 */

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

import {
  CANONICALISATION,
  COVERED_FIELDS,
  EXCLUDED_FIELDS,
  HASH,
  canonicalBytes,
  canonicalText,
  normaliseContent,
  sha256Hex,
  signingInput,
  stateId,
  transitionId,
  type Json,
} from '../src/canonical.js'
import { PREFIX } from '../src/keys.js'

interface Vectors {
  canonicalisation: string
  hash: string
  covered_fields: string[]
  excluded_fields: string[]
  canonical: { name: string; value: Json; text: string; sha256: string }[]
  content: { name: string; input: string; normalised: string; state_id: string }[]
  transitions: {
    name: string
    record: Record<string, unknown>
    id: string
    same_as?: string
  }[]
  signing: { id: string; registrar: string; time: string; text: string }[]
  keys: { prefix: string }
}

const vectors: Vectors = JSON.parse(
  readFileSync(fileURLToPath(new URL('./vectors.json', import.meta.url)), 'utf-8'),
)

const decoder = new TextDecoder()

describe('the two implementations name the same things', () => {
  it('agrees on the canonicalisation and the hash', () => {
    expect(CANONICALISATION).toBe(vectors.canonicalisation)
    expect(HASH).toBe(vectors.hash)
    expect(PREFIX).toBe(vectors.keys.prefix)
  })

  it('agrees on which fields an identifier covers', () => {
    // Order matters as much as membership: this list is what the protocol
    // version pins, and a field added on one side alone splits every id.
    expect([...COVERED_FIELDS]).toEqual(vectors.covered_fields)
    expect([...EXCLUDED_FIELDS]).toEqual(vectors.excluded_fields)
  })
})

describe('canonical form', () => {
  for (const vector of vectors.canonical) {
    it(`serialises ${vector.name} identically`, () => {
      expect(canonicalText(vector.value)).toBe(vector.text)
      expect(sha256Hex(canonicalBytes(vector.value))).toBe(vector.sha256)
    })
  }

  it('refuses values with no canonical form', () => {
    expect(() => canonicalText(Number.NaN)).toThrow()
    expect(() => canonicalText(Number.POSITIVE_INFINITY)).toThrow()
  })
})

describe('content normalisation', () => {
  for (const vector of vectors.content) {
    it(`normalises ${vector.name} identically`, () => {
      expect(normaliseContent(vector.input)).toBe(vector.normalised)
      expect(stateId(normaliseContent(vector.input))).toBe(vector.state_id)
    })
  }

  it('is idempotent, because content is normalised once and hashed forever', () => {
    for (const vector of vectors.content) {
      const once = normaliseContent(vector.input)
      expect(normaliseContent(once)).toBe(once)
    }
  })
})

describe('transition identifiers', () => {
  for (const vector of vectors.transitions) {
    it(`computes ${vector.name} identically`, () => {
      expect(transitionId(vector.record)).toBe(vector.id)
    })
  }

  it('ignores registration and disclosure, which arrive after the fact', () => {
    const byName = new Map(vectors.transitions.map((v) => [v.name, v]))
    for (const vector of vectors.transitions) {
      if (!vector.same_as) continue
      const other = byName.get(vector.same_as)!
      expect(transitionId(vector.record)).toBe(transitionId(other.record))
    }
  })

  it('changes when a covered field changes', () => {
    const base = vectors.transitions[0]!.record
    for (const field of COVERED_FIELDS) {
      const altered = { ...base, [field]: 'something-else-entirely' }
      expect(transitionId(altered)).not.toBe(transitionId(base))
    }
  })

  it('chains through parents, so altering an ancestor invalidates descendants', () => {
    const base = vectors.transitions[0]!.record
    const child = { ...base, parents: [transitionId(base)] }
    const alteredParent = { ...base, performed: '2026-01-01T00:00:01Z' }
    const orphan = { ...base, parents: [transitionId(alteredParent)] }
    expect(transitionId(child)).not.toBe(transitionId(orphan))
  })
})

describe('signing input', () => {
  for (const vector of vectors.signing) {
    it('builds the bytes a registrar signs identically', () => {
      expect(decoder.decode(signingInput(vector.id, vector.registrar, vector.time))).toBe(
        vector.text,
      )
    })
  }
})
