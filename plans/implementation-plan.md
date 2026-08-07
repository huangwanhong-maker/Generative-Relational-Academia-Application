# GRRP — implementation plan

Single plan for the reference implementation of the **Generative Relational Research Protocol v0.1**.
Supersedes `implementation_plan.md` and `GRRP-implementation-plan.md`, both retired.

**Authority.** The specification governs where this document and the papers differ:
[*Specifying the GRRP*](../papers/GRA-paper-IV-Specifying-the-GRRP.pdf). This plan restates only what
a builder needs, and cites the requirement behind each item so a disputed choice can be traced.

**Where the work is.** [`grrp/`](../grrp/) · notes: [Paper I](../notes/paper-I-design-and-requirements.md)
· [II](../notes/paper-II-incentives-and-adoption.md) · [III](../notes/paper-III-grounds-of-restriction.md)
· [IV](../notes/paper-IV-grrp-specification.md) · [glossary](../notes/glossary.md)

---

## Status

| Milestone | | |
|---|---|---|
| **M0** Skeleton — layout, canonical hashing, `init` | ✅ done | 1–2 days |
| **M1** Personal tier — **ship here** | ✅ done | 1 week |
| **M1** usability pass — editor prompts, defaulted references, `show` | ✅ done | 1 day |
| **Gate** Use it on real work for two weeks | ⬜ **not started — blocks M2** | 2 weeks |
| **M2** Integrity — chain verification, separability, redaction | ⬜ | 3–4 days |
| **M3** Group tier — keys, signatures, attestation, disclosure grounds | ⬜ | 1 week |
| **M4** Open tier — bundle, continue, profile, deposit | ⬜ | 1 week |
| **M5** Conformance suite | ⬜ | 3–4 days |

49 tests pass; 4 are skipped — three named for M2, M3 and M4, one platform-specific.

---

## 0. The constraint register

Never violated. Where a decision touches one, it is recorded in
[notes/gaps-and-repo-actions.md §F](../notes/gaps-and-repo-actions.md) rather than settled quietly.

| | Constraint | Consequence for the code | Requirement |
|---|---|---|---|
| **C1** | **Byproduct only** | Every command serves a purpose the user has anyway. Its `--help` names that purpose. A command whose only purpose is that a record should exist is not written. | R1 · P-IV Req. 4.2, 20.6 |
| **C2** | **Attested registration** | At group tier and above the registrar must differ from the performer. Refuse when the keys are identical. | R3 · P-IV Req. 8.1–8.2 |
| **C3** | **Append-only** | Nothing is edited or deleted. A correction is a further transition referencing the one corrected. Current state is derived on demand. | R5 · P-IV Req. 4.4 |
| **C4** | **Granularity** | A transition references a specific identified prior state. Project-, repository- or person-level records are rejected. | R4 · P-IV Req. 4.5 |
| **C5** | **No merge** | No operation combines two divergent states. The word appears nowhere in the interface. | R6 · P-IV Req. 10.5 |
| **C6** | **No scalars** | No count, score, ranking or index over participants or trajectories — not computed, stored, displayed or exported. Counts *within* one trajectory, shown without comparison, are permitted. | R10 · P-IV Req. 8.5, 20.4 |
| **C7** | **Monotone disclosure** | Disclosure may widen, never narrow. No `unpublish` exists. A schedule may be shortened, never extended. | R11 · P-IV Req. 12.1, 12.4 |
| **C8** | **Separability** | Content lives in files separate from the skeleton, referenced by hash. Removing content leaves the skeleton and its signature chain valid. | R12 · P-IV Req. 13.2 |
| **C9** | **Independence** | Works with no model, no network, no service. AI assistance is optional and additive. | R14 · P-IV Req. 20.5 |
| **C10** | **Portability** | Any participant obtains the complete record and continues it elsewhere without permission. | R7 · P-IV Req. 16.4 |
| **C11** | **Plain durable formats** | The authoritative record is human-readable text. No database is the system of record; caches are reconstructible. | R13 · P-IV Req. 17.1 |
| **C12** | **Bind, do not reinvent** | Relations → CiTO, contributor roles → CRediT, provenance → PROV. | R2 · P-IV Req. 7.1 |

---

## M0 — Skeleton ✅

- [x] Repository layout: `.grrp/` and `trajectories/<id>/{states,transitions,disclosure,releases}/`
- [x] `profile.yaml` — protocol version, tier, hash, canonicalisation, party, bound vocabularies
- [x] `.grrp/.gitignore` — `events/` and `keys/*.key`, so the event plane is never committed *(P-IV Req. 3.1)*
- [x] Canonical serialisation — JSON, sorted keys, no insignificant whitespace, UTF-8
- [x] Content hashing — `state:sha256:<hex>` over the exact bytes written *(P-IV Req. 5.2)*
- [x] Transition identifier over the **covered payload and parent identifiers**, excluding
      `registration` and `disclosure` *(P-IV Req. 8.3 — the named most-likely serious bug)*
- [x] `grrp init` — profile, keypair, layout
- [x] **Test:** two runs over the same payload produce the same identifier
- [x] **Test:** altering a covered field, or a parent, changes the identifier
- [x] **Test:** adding `registration` or `disclosure` does **not** change the identifier

---

## M1 — Personal tier ✅ · *ship here*

The tier that has to be worth using by one person, alone, on the first day. It delivers **utility and
no evidential weight**, and the two must never be confused. *(R15 · P-II Req. 11.4 · P-IV Req. 20.2)*

### Acts
- [x] `grrp new "<question>"` — open a trajectory; the question anchors the first claim *(C4)*
- [x] `grrp claim` — state a position
- [x] `grrp challenge <state>` — object to an identified state; **does not alter it** *(P-IV §6.2)*
- [x] `grrp transform <state> [--answering <tx>]` — produce the successor
- [x] `grrp decide <state> [--abandon]` — record a decision **with its reason** *(the demanding act)*
- [x] `grrp release <state>` — publish, enumerating the objections standing *(P-IV Req. 12.6)*

### Record and views
- [x] Append-only writer; refuses to rewrite a recorded transition *(C3)*
- [x] Five-dimension factored type: `act × target × relation × trigger × disposition` *(P-IV Req. 6.1)*
- [x] `disposition` fixed at exactly three values, `unresolved` among them *(P-IV Req. 6.3)*
- [x] `grrp state` — live positions, derived; **no branch marked principal** *(P-IV Req. 10.3)*
- [x] `grrp log` — parents before children; **graph order, not clock order** *(P-IV Req. 10.1)*
- [x] `grrp open` — the register of unresolved states: **the entry path** *(P-IV Req. 6.5)*
- [x] `grrp export <release>` — citable document with lineage, contributors, standing objections *(R16 · P-IV Req. 12.7)*
- [x] `grrp check` — identifier recomputation, acyclicity, vocabulary, granularity, scalar exclusion
- [x] `grrp profile` — what another implementation needs to read the record
- [x] Every transition marked **unattested**, on every display and every export *(P-IV Req. 20.3)*
- [x] Commit to git automatically when inside a work tree — **only the paths grrp wrote**

### Tests
- [x] The philosophy case: claim → objection → transformation answering it → an objection that is
      never resolved → divergence → release enumerating it *(P-IV Case 22.3)*
- [x] The mathematics case: claim → `decide --abandon` with the reason; the direction is retired and
      the reason kept *(P-IV Case 22.1)*
- [x] A challenge does not supersede the state it challenges
- [x] Divergence preserves both directions and designates neither
- [x] Every command's `--help` contains `Purpose (for you):` *(C1)*

---

### M1 usability pass ✅

Not features — the difference between a tool that gets used on a Tuesday and one that does not. The
byproduct principle is a claim about *cost to the participant*, so friction on the acts is a
conformance concern and not a matter of polish *(C1 · P-II Claim 11.1)*.

- [x] **Omitting `-m` opens `$GRRP_EDITOR` / `$EDITOR`**, with a prompt for the act being performed.
      Writing a paragraph inside shell quotes is friction, and it falls hardest on the **decision**
      act — the one whose purpose for the performer is weakest and on which reuse depends entirely
- [x] The prompt sits below a cut line and is never recorded; an empty message records nothing
- [x] A 30-line editor launcher rather than a dependency — `typer` 0.27 no longer bundles `click`,
      and every command still accepts `-m` and `--file`, so an environment with no editor loses nothing
- [x] **`challenge`, `transform`, `decide`, `release` default to the live position** — no copying a
      hash out of one command's output into the next. Still references a specific identified prior
      state *(C4)*
- [x] A divergence **refuses and lists both positions with their text**, rather than picking —
      nothing in the design gives a basis for picking *(P-IV Req. 10.3)*
- [x] **`grrp show`** — one screen per trajectory: question, live positions, what is unanswered, what
      has been released. Derived; per-trajectory; nothing compared across trajectories or people; no
      number summarising how it is going *(C6)*
- [x] Refusals reach the user as guidance on stderr, naming the constraint and what to do instead
- [x] `new` points at the next act

---

## Gate — use it, before writing another line ⬜

The point of M1 is to find out whether the tool is worth using at all. M2 onward invites architecture
the early tiers do not need.

- [ ] Use `grrp` on real work for two weeks
- [ ] Record what was annoying — **those notes are the input to M2 and beyond, and they belong in a
      trajectory**
- [ ] Check the two signals the papers name as diagnostic:
  - [ ] Is the **`decision` act rare while transformations are common**? That would mean the act on
        which reuse depends is not being performed, and making it cheap was insufficient
        *(P-IV §24.4, finding 2)*
  - [ ] Did anything want to be a score, a ranking or a dashboard? Record what, and refuse it *(C6)*

---

## M2 — Integrity ⬜

- [ ] Complete the act vocabulary — `grrp connect <state> --to <ref>` and `grrp verify <state>`
      *(the eight acts, P-IV Def. 6.2)*
  - [ ] External references carry a persistent identifier and its scheme, **or** enough descriptive
        information plus **the date the reference was made** *(P-IV Req. 5.5)*
- [ ] `grrp check` verifies the **whole chain**, not each record in isolation
  - [ ] An altered early transition invalidates every descendant
  - [ ] Detection requires a second custodian where a party holds the only copy — say so in the output
        *(P-IV §23.1)*
- [ ] Content held **outside the versioned tree** and referenced by identifier, so redaction does not
      need history rewriting *(P-IV §21.5, weakness 3)*
- [ ] `grrp redact <state> --ground <g>`
  - [ ] Removes content; the skeleton stays valid and verifiable *(C8)*
  - [ ] Recorded as an **administrative operation** with performer, time and ground *(P-IV Req. 13.4)*
  - [ ] **The graph is unchanged** — parent links, state references and the induced ordering survive
        *(P-IV Req. 13.5)*
  - [ ] The record of the redaction is itself never removable; redacted content is never represented
        as never having existed
  - [ ] Reconstruct affected caches; **record which emitted documents referenced redacted content**
        so a party can pursue them outside the system *(P-IV Req. 13.6)*
- [ ] **Decide and record: the per-record secret.** Where content is short and drawn from a small
      space, its content-derived identifier permits recovery by exhaustive search. A secret must be
      applied **before** the identifier is computed, so this is decided in advance or not at all
      *(P-IV §13.5)* — **touches C8; flag before implementing**
- [ ] Administrative operations use the same envelope with a mandatory `kind` and an `operation`
      field, and are **never presented as transitions** *(P-IV Req. 4.6)*
- [ ] **Test 4:** editing any file under `transitions/` is detected *(already passing; extend to the chain)*
- [ ] **Test 6:** after `grrp redact` the chain verifies, the graph is unchanged, and the redaction is recorded

---

## M3 — Group tier ⬜

Where credibility begins. **Minimum viable adopting unit: two parties who register each other's
transitions** *(P-II Claim 13.4)*.

### Identity and signatures
- [ ] `grrp key add <name> <pubkey>` — known parties in `.grrp/keys/`
- [ ] Detached ed25519 signatures over `{id, registrar, time}` — **never over `disclosure` or any
      field a later lawful operation may change** *(P-IV Req. 8.3)*
- [ ] Passphrase on the private key *(deferred from M0 deliberately)*
- [ ] **Pseudonymous participation at every tier** — no legal name, telephone number, affiliation or
      government identifier may be required to hold a party identifier *(P-IV Req. 14.3)*
- [ ] Optional **bindings** to external identifiers: recorded as operations, visible wherever the
      party is shown, attributed, revocable *(P-IV Req. 14.4–14.5)*
- [ ] Assurance **by class and by act kind, never as an entrance gate** — gating a stranger's
      challenge to a publicly disclosed claim reproduces the bootstrap failure *(P-IV Req. 14.6)*
- [ ] Key rotation by an operation **signed with the old key**; loss via a charter procedure that is
      **marked as weaker than a signature** *(P-IV Req. 14.7)*
- [ ] Compromise = revocation with a date; prior registrations stay, marked

### Attestation
- [ ] `grrp propose ...` — any act, unregistered
- [ ] `grrp register <tx>` — **refuse when performer and registrar are identical** *(C2)*
- [ ] No automatic registration on a party's behalf; no holding another's credentials. A standing
      arrangement (a supervisor routinely registering a student's transitions) is **recorded, not
      forbidden** *(P-IV Req. 8.2)*
- [ ] `grrp register` withdrawal is a further **challenge** referencing the attestation; the original
      stays in the log *(P-IV Req. 8.7)*
- [ ] **No aggregate over attestations** — not counts, depths, ratios or derived scores *(C6)*

### Attribution and absorption
- [ ] `grrp attribute <tx> --party <key> --role <credit-role>` — CRediT, bound not restated *(C12)*
- [ ] `grrp absorb <tx> --from <state> --party <key>` — the link records the state, **the party who
      produced it**, and the transition that took the content *(P-IV Req. 9.3)*
- [ ] Absorption links **presented alongside the transition wherever it is displayed**
- [ ] **No veto.** No mechanism by which the named party can block, condition or reverse the use.
      A party who does not want their state absorbed has **one instrument: its disclosure class**
      *(P-IV Req. 9.4)*
- [ ] `grrp challenge` on an attribution — contested attribution is a record, not a matter to
      adjudicate; **no party is empowered to resolve it** *(P-IV Req. 9.5)*
- [ ] **No measure of the influence of an absorbed state** *(C6)*

### Disclosure
- [ ] `grrp disclose <tx> --class <c> --ground <g> [--release-at <date>]`
- [ ] Classes exist, are **ordered by inclusion**, are enforced, and are **opaque to the protocol** —
      identity and membership come from a charter *(P-IV Def. 11.1)*
- [ ] **Four grounds, closed set:** `rivalry` · `hazard` · `vulnerability` · `appropriability`.
      A community may not declare a new one *(P-III Req. 2.5)*
- [ ] **Reject a restriction that declares no ground**, and display the ground wherever the
      restriction is shown *(P-IV Req. 11.3)*
- [ ] **Surface the residue.** When a ground is declared, show what that ground leaves disclosable —
      *the only part of the design that gains something without giving something up*
      *(P-III Req. 2.6 · P-IV Req. 11.4)*

  | ground | object restricted | residue that must still be disclosed |
  |---|---|---|
  | rivalry | access to the resource | **the trajectory in full** |
  | hazard | the propagable content of a method | existence, questions, decisions, interpretations, non-conveying results |
  | vulnerability | the timing of exposure | **everything, at the scheduled time** |
  | appropriability | content whose disclosure destroys excludability | existence, questions, decisions, **negative results** |

- [ ] **Composition = intersection of residues.** Declaring more grounds is not free: each is an
      assertion that can be found false *(P-III Req. 7.2)*
- [ ] **Monotone enforcement** *(C7)*
  - [ ] No operation narrows a class; no `unpublish`
  - [ ] Restrictive default; **never widen as a side effect of another operation** *(P-IV Req. 12.2)*
  - [ ] A schedule fires **without a further act by any party**; may be shortened; **an attempt to
        extend or cancel is refused and recorded as an operation with its ground** *(P-IV Req. 12.4)*
  - [ ] `--release-at` offered only for **vulnerability** — it is the only ground with a recorded
        terminus, and hazard has none at all *(P-III Claim 7.4)*
- [ ] **Per-record**, never per repository or per trajectory. Records within one trajectory carry
      different classes *(P-IV Req. 11.5)*
  - [ ] Under the git deployment this means a class change **moves** a record between
        repositories, and the movement is recorded as an operation *(P-IV §21.5, weakness 1)*
- [ ] Views computed **over the records that reader may see**; **never disclose a record's existence
      by omission, ambiguity or a gap in numbering** — *a genuine implementation hazard, easy to
      introduce accidentally* *(P-IV §11.4, §23.3)*
- [ ] Charter reference: `charter.yaml` with identifier **and version**; a record carries the version
      that governed it; amendments are **prospective only** *(P-IV Req. 18.3–18.4)*
- [ ] Reject a record referencing a charter that does not state its minimum content *(P-IV Req. 18.2)*
- [ ] **Test 5:** changing a class, or a schedule firing, invalidates no signature
- [ ] **Test 7:** `grrp register` refuses when performer and registrar keys are identical

---

## M4 — Open tier ⬜

- [ ] `grrp bundle [<traj>] -o traj.zip` — the complete record: transitions, skeletons, signatures,
      attributions, absorption links, parent structure — **obtainable without anyone's permission** *(C10)*
- [ ] `grrp continue traj.zip` — appended transitions reference the obtained ones as parents, so the
      result is **one graph and not two** *(P-IV Req. 16.4)*
- [ ] Restricted content travels **only where the receiving implementation honours the class**;
      otherwise transfer the skeleton and **record that content was withheld**
- [ ] `grrp profile` emits a machine-readable **declaration**: protocol version, tier, identifier
      construction, signature scheme, bound vocabularies with versions *(P-IV Req. 16.3)*
  - [ ] A receiving implementation **records the declaration under which records arrived**
- [ ] Received records: verify what can be verified; **retain what cannot, marked unverified; never
      alter — and that includes normalisation** *(P-IV Req. 16.5)*
- [ ] Failure cases handled explicitly *(P-IV §16.5)*
  - [ ] Version mismatch — retain, do not process as own version
  - [ ] Vocabulary drift — no reconciliation by the protocol
  - [ ] Partial records — mark missing parents unresolved; **never synthesise them**
  - [ ] Divergent continuation — **a divergence; both retained, neither principal, no reconciliation**
- [ ] Resolvable identifiers obtained from a repository service for every state referenced from
      outside, with the correspondence recorded *(P-IV §21.5, weakness 2)*
- [ ] `grrp deposit <release>` — archival package to an **independent** service, identifier recorded
      in the trajectory. **Released material only** — depositing sealed or restricted content would
      place it outside the regime governing it *(P-IV Req. 17.5)*
- [ ] Distributed custody: at least **two parties who do not share an operator**; record which
      parties hold copies *(P-IV Req. 17.4)*
- [ ] Publish **succession arrangements** — what becomes of the records if the operator ceases.
      **Durability must not be claimed without one** *(P-IV Req. 17.6)*
- [ ] Redaction notices accepted, acted on, **forwarded onward**, and recorded *(P-IV Req. 13.6)*
- [ ] Sealed registration *(P-IV §15)*
  - [ ] `grrp seal` — content-derived identifier, party, time, signature, **content disclosed to nobody**
  - [ ] Available at every class, including disclosure-to-nobody; **disclosure never a condition of
        registration** *(Req. 15.2)*
  - [ ] `grrp openseal` — any party can verify from the record alone that the content yields the
        registered identifier; failures recorded, nothing removed *(Req. 15.4)*
  - [ ] **Anchor the time in a medium the implementation does not control**, and record which method
        was used — *a sealed registration is evidence only if its time is credible to someone who does
        not trust the registrant* *(P-IV §15.5)*
  - [ ] **Never** describe it as establishing priority; **never** rank or order parties by
        registration time; **no inference from precedence** *(Req. 15.6–15.7)*
- [ ] **Test 8:** bundle on machine A, continue on machine B with no shared service; one graph

---

## M5 — Conformance suite ⬜

- [ ] Automated tests for **C1–C12**, each naming the constraint it enforces
- [ ] The three conformance tests as executable checks inside `grrp check` *(P-IV Req. 20.4–20.6)*
  - [ ] **Scalar test** — fails on any total order or numeric measure over participants or
        trajectories. Within-trajectory counts shown without comparison pass
  - [ ] **Independence test** — the record can be created, registered, read, verified, exported and
        continued **with a text editor and a version-control system**
  - [ ] **Byproduct test** — every required act has a purpose *for the party performing it*, stated
        in the documentation
- [ ] `grrp check --self-declare` emits the conformance declaration *(P-IV Req. 20.7)*
- [ ] Container run with **no network and no model**: create, register, verify, export, bundle, continue
- [ ] Field documentation published **outside the implementation**: vocabularies with versions,
      identifier construction, signature construction *(P-IV Req. 17.2)*
- [ ] Attack cases from P-IV §23 exercised: collusive fabrication, retroactive alteration, backdating,
      flooding, registrar gatekeeping, misapplied grounds, disclosure by inference, reflexive
      confirmation

---

## Level 3 — applications, outside conformance

**The protocol is implementable with none of it, and requires none of it** *(C9 · R14)*. Anything here
is optional, additive, and clearly marked as outside conformance.

- [ ] Capture assistant proposing candidate transitions from the local event plane
  - [ ] A model may **occasion** a transition and may **not author or register one**; a
        model-originated proposal is **marked** *(P-IV Req. 4.3)*
  - [ ] Registration stays an **affirmative act** — a default that registers unattended proposals is
        forbidden, because the record's credibility rests on registration meaning something
- [ ] Visualisation of a trajectory graph — **no branch marked principal, no ordering exported**
- [ ] Retrieval over one's own record
- [ ] Import of git history / OSF projects / DOI-identified works as **artefact references and
      external references**, never as transitions *(C4)*

### Excluded, and not by taste

| | Why |
|---|---|
| progress reports, "project health", trajectory risk analysis | scalars over trajectories *(C6, R10)* |
| contribution scores, reputation, contributor ranking | scalars over participants *(C6)* |
| absorption counts, attestation depth | scalars, and **farmable by reciprocal registration** *(P-II Claim 8.4 · P-IV Req. 8.5)* |
| similar-trajectory search, cross-field matching **as an adoption argument** | not decomposable by tier, returns nothing to any adopting party, and the matching problem is unsolved *(P-II Claim 13.5 · P-I Claim 18.3)* |
| automatic classification of a user's work by a model without confirmation | *(C1, C9)* |
| any merge, auto-reconciliation, or canonical-branch selection | *(C5)* |
| a new identifier service | content hashes locally, repository DOIs on deposit |
| a web application, hosted service, or accounts | not in v0.1 |

---

## Open decisions — needed from the maintainer ⬜

- [x] **Licence — settled: MIT.** Discharges both dependent requirements: **the specification is
      forkable** *(P-IV Req. 19.4)*, so custodianship is a service rather than a position; and **a
      record is licensed to permit continuation elsewhere** *(P-I Req. 16.2, property 4)*, which is
      the property that distinguishes portability from export.
  - [ ] The four PDFs still carry an embedded **CC BY-NC 4.0** notice and remain under it until their
        author revises them. Regenerate the licence block if MIT is intended there too.
- [ ] **Per-record secret before hashing redactable content** *(M2 above)* — decided in advance or not
      at all, because it changes identifier construction.
- [ ] **Custodial separation.** Serendip Commons Society would maintain the specification and operate
      an implementation. Req. 19.4 requires the two functions separated, **or the conflict recorded
      with the arrangements limiting it.** Which, and where is it recorded?

---

## Evaluation — what would show this was wrong

Not a retrospective. These are stated in advance so they can be looked for.

- [ ] **Personal-tier adoption without progression to the group tier**, over a substantial population
      and period → private utility without the attested records on which every evidential claim rests.
      The tool would have become **a note-taking convention** *(P-IV §24.4 · P-II Claim 16.1 — the
      prediction the account is most exposed on)*
- [ ] **`decision` acts rare while transformations are common** → the act on which reuse depends is
      not being performed
- [ ] **Group-tier declarations alongside pairs who register only each other** → attestation operating
      as a formality
- [ ] **A widely used external score computed over conformant records** → the scalar exclusion
      displacing the dynamic rather than preventing it

And the difficulties the papers record as **unaddressed** — no mechanism with an identified cost-bearer
for whom bearing it is rational. Nothing in this plan solves them: **assessment capacity** *(the one
most likely to determine whether a conforming arrangement survives at scale)*, **maintainer labour**,
**the regressive incidence of overhead**, and **recognition of attributed contribution**
*(P-II §17.2)*.

---

## Sequence

1. ✅ M0, M1.
2. ⬜ **Use it for two weeks on real work.** Write down what was annoying.
3. ⬜ Those notes are the input to M2 and beyond — and they belong in a trajectory.
4. ⬜ M2 → M3 → M4 → M5, in order. Do not start M3 before the group tier has a second party willing
   to register.
