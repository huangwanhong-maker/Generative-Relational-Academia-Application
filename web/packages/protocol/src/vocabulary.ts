/**
 * The typed vocabularies.
 *
 * The type of a transition is factored into five independent dimensions with
 * small closed vocabularies, rather than one flat list of several dozen tags.
 * Agreement between two people classifying the same event declines as the
 * number of categories rises, and a vocabulary that requires deliberation
 * reintroduces the recording cost the whole design exists to avoid.
 *
 * Relations bind to CiTO and contributor roles to CRediT (C12). Values no
 * deployed vocabulary covers are marked `local:` and must be defined by a
 * community charter; they are accepted and flagged, never silently presented
 * as though they were bound.
 */

export const VOCABULARIES = {
  relation: { prefix: 'cito', namespace: 'http://purl.org/spar/cito/' },
  contributor: { prefix: 'credit', namespace: 'https://credit.niso.org/contributor-roles/' },
  provenance: { prefix: 'prov', namespace: 'http://www.w3.org/ns/prov#' },
} as const

/**
 * Fixed by the protocol. Not extensible: acts are what interoperability rests
 * on, and a record whose act vocabulary varied by community could not travel.
 */
export const ACTS = [
  'question',
  'claim',
  'challenge',
  'transformation',
  'decision',
  'connection',
  'verification',
  'release',
] as const
export type Act = (typeof ACTS)[number]

/** Extensible by charter: mathematics wants obstruction types, a lab wants deviations. */
export const TARGETS = [
  'question',
  'assumption',
  'hypothesis',
  'concept',
  'theory',
  'method',
  'path',
  'artefact',
] as const
export type Target = (typeof TARGETS)[number]

/**
 * Bound to CiTO. The friendly name on the left is a convenience for typing;
 * the CiTO identifier on the right is what is stored, because a record storing
 * the word "extends" is uninterpretable once a second vocabulary uses the same
 * word differently.
 */
export const RELATIONS = {
  extends: 'cito:extends',
  modifies: 'cito:updates',
  refines: 'cito:qualifies',
  replaces: 'cito:corrects',
  disagrees: 'cito:disagreesWith',
  agrees: 'cito:agreesWith',
  supports: 'cito:supports',
  refutes: 'cito:refutes',
  confirms: 'cito:confirms',
  retracts: 'cito:retracts',
  repliesTo: 'cito:repliesTo',
  usesMethodIn: 'cito:usesMethodIn',
  relates: 'cito:citesAsRelated',
  supportedBy: 'cito:obtainsSupportFrom',
  usesDataFrom: 'cito:usesDataFrom',
  disputes: 'cito:disputes',
} as const

/**
 * Relations named in the design for which CiTO has no counterpart. Available
 * as local values, requiring a charter to define them. Using one warns.
 */
export const LOCAL_RELATIONS = ['generalises', 'specialises', 'transfers'] as const

export const TRIGGERS = [
  'self',
  'literature',
  'experiment',
  'simulation',
  'observation',
  'discussion',
  'objection',
  'failure',
  'ai_suggestion',
  'entering_party',
] as const
export type Trigger = (typeof TRIGGERS)[number]

/**
 * Exactly three values. Fixed by the protocol, never extended or reduced.
 *
 * `unresolved` is why the vocabulary is closed. Most objections in theoretical
 * work are never resolved: they stand, and the work proceeds beside them. A
 * record admitting only acceptance and rejection would be systematically false
 * about the fields this protocol most concerns, and would exert pressure
 * toward fabricated closure.
 */
export const DISPOSITIONS = ['accepted', 'contested', 'unresolved'] as const
export type Disposition = (typeof DISPOSITIONS)[number]

export const TIERS = ['personal', 'group', 'open'] as const
export type Tier = (typeof TIERS)[number]

/**
 * The four closed grounds on which disclosure may be restricted. Each has an
 * object, a residue and a named failure; nothing else is a ground.
 */
export const GROUNDS = ['rivalry', 'hazard', 'exploratory', 'appropriability'] as const
export type Ground = (typeof GROUNDS)[number]

/** A transition as it appears in the log. */
export interface Transition {
  id: string
  protocol: string
  kind: string
  trajectory: string
  parents: string[]
  prior_state: string | null
  posterior_state: string | null
  act: Act | null
  target: Target | null
  relation: string | null
  trigger: Trigger | null
  disposition: Disposition | null
  operation?: string | null
  subject?: string | null
  payload?: Record<string, unknown> | null
  performer: string
  performed: string
  contributions?: Record<string, string[]> | null
  absorption?: unknown
  artefacts?: unknown
  registration?: {
    registrar: string
    time: string
    attested: boolean
    signature?: string
  }
}
