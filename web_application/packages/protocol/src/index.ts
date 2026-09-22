/**
 * GRRP v0.1 in TypeScript.
 *
 * The unit of record is a **transition**, never a commit. The word is avoided
 * throughout, and so is "merge", because a vocabulary is how a design either
 * holds or quietly becomes the thing it was built not to be.
 */

export * from './canonical.js'
export * from './keys.js'
export * from './vocabulary.js'
