/**
 * The path guard, tested by behaviour rather than by reading it.
 *
 * Its character class contains literal control characters, which are invisible
 * in an editor. A guard nobody can verify by eye has to be verified by test —
 * and writing this one caught the reverse mistake first: a test string whose
 * backslashes had been eaten in transit, so `data\raw` was a carriage return
 * and the guard was right to refuse it.
 */

import { describe, expect, it } from 'vitest'

import { safeFilePath } from '../src/records.js'

const BACKSLASH = String.fromCharCode(92)
const NUL = String.fromCharCode(0)
const SOH = String.fromCharCode(1)

describe('file paths', () => {
  it('allows ordinary names and folders', () => {
    for (const name of ['notes.md', 'data/raw/run-1.csv', 'a-b_c.2.md', 'Figure 3.png']) {
      expect(() => safeFilePath(name), name).not.toThrow()
    }
  })

  it('refuses anything that could escape the area or reach the record', () => {
    for (const name of [
      '../.grrp/profile.yaml',
      '.gra-host.json',
      '..',
      'a/../../b',
      `a${BACKSLASH}..${BACKSLASH}b`,
      '',
      'a/.hidden/b',
      'a|b',
      'con:x',
      `a${SOH}b`,
      `a${NUL}b`,
    ]) {
      expect(() => safeFilePath(name), JSON.stringify(name)).toThrow()
    }
  })

  it('treats a backslash as a separator rather than as a character in a name', () => {
    expect(safeFilePath(`data${BACKSLASH}raw${BACKSLASH}run-1.csv`)).toBe('data/raw/run-1.csv')
  })

  it('refuses rather than silently shortening', () => {
    // Stripping to the last segment would be equally safe and would store
    // something other than what was asked for.
    expect(() => safeFilePath('../secrets.txt')).toThrow()
  })

  it('refuses a path deep enough to be a mistake', () => {
    expect(() => safeFilePath('a/b/c/d/e/f/g/h/i/j.txt')).toThrow()
  })
})
