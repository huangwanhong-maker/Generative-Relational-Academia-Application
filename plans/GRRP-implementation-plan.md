# GRRP — project introduction and implementation plan

Reference implementation of the **Generative Relational Research Protocol v0.1**, specified in
*Specifying the Generative Relational Research Protocol: Architecture, Conformance, and Deployment over Existing Repositories*.

This document is for building. It restates only what a builder needs; the specification governs where the two differ.

---

## 1. What this is

Scholarly work produces artefacts. It also produces a **trajectory**: the sequence of changes an understanding passes through, the objections that forced them, the directions abandoned and why. The trajectory is where most of the information is, and it is what current arrangements discard.

`grrp` is a command-line tool that records trajectories as **typed transitions** in an ordinary git repository, using plain text files, with no server, no account, and no network.

### The unit of record

Not a document. Not a comment. A **transition**: an identified prior state became an identified posterior state, through a typed act performed by a party and registered by a party.

```
state s_k  --[ challenge / transformation / decision / ... ]-->  state s_k+1
```

A **trajectory** is the directed graph of these. The "current state" is *computed* from the graph and never stored as an authority.

### Why a tool and not a platform

Credibility of a trajectory record comes from its **distribution across parties who did not coordinate**, not from any property of its content. A platform operator is party to every entry and cannot supply that. So: a file format, a small tool, and existing substrates.

### Who it is for on day one

One researcher, alone, with no collaborators. If the tool is not worth using by a single person on the first day, nothing that follows happens. That constraint drives the whole design.

---

## 2. Hard constraints

These are not preferences. An implementation violating any of them is non-conformant.

| # | Constraint | Consequence for the code |
|---|---|---|
| C1 | **Byproduct only** | Every command must serve a purpose the user has *anyway*. No command exists solely so that a record exists. |
| C2 | **Attested registration** | At group tier and above, the registering party must differ from the performing party. Reject when they coincide. |
| C3 | **Append-only** | Nothing is edited or deleted. A correction is a new transition. Current state is derived on demand. |
| C4 | **Granularity** | A transition references a specific identified prior state. Project-level or repo-level records are rejected. |
| C5 | **No merge** | No operation combines two divergent states automatically. Never use the word "merge" in the UI. |
| C6 | **No scalars** | No count, score, ranking or index over participants or trajectories. Not computed, not stored, not displayed, not exported. |
| C7 | **Monotone disclosure** | Disclosure may widen, never narrow. No "unpublish" operation exists. |
| C8 | **Separability** | Content lives in separate files referenced by hash. Removing content must leave the skeleton and its signature chain valid. |
| C9 | **Independence** | Everything must work with no model, no network, no service. Any AI assistance is optional and additive. |
| C10 | **Portability** | Any participant can obtain the complete record and continue it elsewhere without permission. |
| C11 | **Plain durable formats** | The authoritative record is human-readable text. No database is the system of record. |
| C12 | **Bindings, not reinvention** | Relations bind to CiTO, contributor roles to CRediT, provenance to PROV. Do not invent parallel vocabularies. |

### Explicit non-goals

- No web application, no hosted service, no accounts — not in v0.1.
- No recommendation, ranking, matching or "trajectory health" features. (Refused in the specification.)
- No automatic classification of a user's work by a model without confirmation.
- No new identifier service. Use content hashes locally and repository DOIs when depositing.

---

## 3. Data model

### Directory layout (inside any git repository)

```
.grrp/
  profile.yaml          # protocol version, tier, hash + signature scheme, bound vocab versions
  charter.yaml          # optional: identifier + version of the operating charter
  keys/<party>.pub      # public keys of known parties
  events/               # LOCAL EVENT PLANE — gitignored by default, never exported
trajectories/
  <traj-id>/
    trajectory.yaml     # id, title, question, creator, charter ref, parent trajectories
    states/<state-id>.md        # CONTENT (separable, redactable)
    transitions/<tx-id>.yaml    # SKELETON (append-only, signed)
    releases/<rel-id>.yaml
```

### Transition skeleton

```yaml
id:            sha256:...          # over canonical payload + parent ids (excludes mutable fields)
kind:          transition          # transition | operation
protocol:      grrp/0.1
parents:       [sha256:..., ...]   # one or more; empty only for the opening transition
prior_state:   state:...           # identifier of the state altered
posterior_state: state:...         # identifier of the state produced
act:           challenge           # question|claim|challenge|transformation|decision|connection|verification|release
target:        assumption          # question|assumption|hypothesis|concept|theory|method|path|artefact
relation:      cito:disagreesWith  # bound vocabulary identifier
trigger:       discussion          # self|literature|experiment|simulation|observation|discussion|objection|failure|ai_suggestion|entering_party
trigger_ref:   event:...           # optional
disposition:   unresolved          # accepted | contested | unresolved
performer:     key:ed25519:...
contributions: [{party: key:..., role: credit:Conceptualization}]
absorption:    [{state: state:..., party: key:...}]   # content taken from elsewhere, with attribution
artefacts:     [{ref: "doi:...", note: "..."}]
disclosure:                       # NOT covered by the signature
  class:    private
  ground:   vulnerability          # rivalry|hazard|vulnerability|appropriability
  release_at: 2027-01-01
registration:                      # appended when registered
  registrar: key:ed25519:...
  time:      2026-08-06T12:00:00Z
  signature: ...
```

**Signature coverage excludes** `disclosure` and any field a later lawful operation may change (scheduled release, redaction marks). Getting this wrong makes ordinary operation invalidate signatures — the single most likely implementation error.

### State file

Plain markdown. Identified by `sha256` of its bytes. Never edited: a change produces a new state file and a transition connecting them.

### Administrative operation

Same envelope with `kind: operation`, an `operation` field (`disclosure_changed`, `redaction`, `key_rotation`, `fork_declared`, `attribution_contested`), and no act/target/relation/disposition.

---

## 4. Command surface

### Personal tier (M1) — must be useful alone

```
grrp init                              # set up .grrp, profile, keypair
grrp new "<question>"                  # open a trajectory
grrp claim  <traj> -m "<text>"         # state a position → new state
grrp challenge <state> -m "<text>"     # object to an identified state
grrp transform <state> -m "<text>" --relation modifies
grrp decide <traj> -m "<reason>" --abandon <state>
grrp connect <state> --to <ref>
grrp verify <state> -m "<outcome>"
grrp release <state>                   # publish; enumerates standing objections
grrp log [<traj>]                      # the transition history
grrp state <traj>                      # DERIVED current state(s)
grrp open [<traj>]                     # register of unresolved states  ← the entry path
grrp export <release>                  # citable document + lineage appendix
grrp check                             # conformance self-test
```

### Group tier (M3)

```
grrp key add <name> <pubkey>
grrp propose ...                       # any act, unregistered
grrp register <tx>                     # ATTEST — registrar must differ from performer
grrp attribute <tx> --party <key> --role <credit-role>
grrp absorb <tx> --from <state> --party <key>
grrp disclose <tx> --class <c> --ground <g> [--release-at <date>]
```

### Open tier (M4)

```
grrp bundle [<traj>] -o traj.zip       # complete record, portable
grrp continue traj.zip                 # continue under a different implementation
grrp profile                           # print the declaration another implementation reads
grrp deposit <release>                 # write archival package + record the identifier
grrp redact <state> --ground <g>       # remove content, keep skeleton, record the operation
```

---

## 5. Milestones

**M0 — Skeleton (1–2 days).** Repo layout, `profile.yaml`, canonical YAML serialisation, content hashing, `grrp init`. Test: two runs over the same payload produce the same id.

**M1 — Personal tier (1 week).** Acts `claim`, `challenge`, `release` plus `transformation` and `decision`; append-only writer; derived `state`, `log`, `open`; `export`. **Ship here.** This is the tier that has to be worth using alone.

**M2 — Integrity (3–4 days).** Hash chaining over parents, `grrp check` verifying the whole chain, separability of content, `redact` keeping the skeleton valid, tamper detection test.

**M3 — Group tier (1 week).** Keypairs, detached signatures, `register` with the performer≠registrar rule, contributions bound to CRediT, absorption links, disclosure classes with grounds, monotone-disclosure enforcement.

**M4 — Open tier (1 week).** `bundle`/`continue` with identifier resolution preserved, `profile` declaration, deposit packaging, redaction notices.

**M5 — Conformance suite (3–4 days).** Automated tests for C1–C12, including the three specification tests below.

---

## 6. Acceptance tests

These decide conformance and should be written as failing tests before the features exist.

1. **Scalar test.** Grep the whole codebase and all output for any aggregate over participants or trajectories. Any count comparable across trajectories fails. Counts *within* one trajectory, shown without comparison, pass.
2. **Independence test.** In a container with no network and no model available, create a trajectory, register a transition, verify signatures, export a release, bundle and continue it elsewhere. All must succeed.
3. **Byproduct test.** For every command, the help text must state the purpose it serves *for the person running it*. A command whose only stated purpose is "so that a record exists" fails.
4. **Append-only test.** Editing any file under `transitions/` must be detected by `grrp check`.
5. **Signature-coverage test.** Changing a disclosure class or executing a scheduled release must **not** invalidate any signature.
6. **Redaction test.** After `grrp redact`, the chain still verifies, the graph is unchanged, and the record of the redaction is present.
7. **Attestation test.** `grrp register` must refuse when performer and registrar keys are identical at group tier and above.
8. **Portability test.** `bundle` on machine A, `continue` on machine B with no shared service; appended transitions reference the obtained ones as parents; one graph, not two.

---

## 7. Technology

- **Python 3.11+**, `click` or `typer`, `ruamel.yaml` (round-trip, ordered), `cryptography` or delegation to `ssh-keygen -Y sign`.
- **git** used as a subprocess; no library binding required.
- No database. No web framework. No model API.
- Single installable package, `pipx install grrp`.

Rationale: the tool must be trivially auditable, must run where researchers already work, and must survive its own dependencies. Anything that cannot be read in an afternoon by a suspicious reviewer is the wrong choice here.

---

## 8. Sequence of work

1. Read §4 (Event, Transition, Artefact model), §6 (Act Vocabulary), §8 (Attestation) and §20 (Conformance) of the specification. Nothing else is needed to start.
2. Build M0 and M1. Use it yourself for two weeks on real work before writing another line.
3. Record what was annoying. Those notes are the input to M2 and beyond, and — appropriately — they belong in a trajectory.
