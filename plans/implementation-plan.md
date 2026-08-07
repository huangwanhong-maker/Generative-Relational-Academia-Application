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
| **Gate** Use it on real work for two weeks | ⬜ **deferred by decision** | 2 weeks |
| **M2** Integrity — full act vocabulary, chain verification, redaction | ✅ done | 3–4 days |
| **M3a** Group tier — keys, signatures, attestation | ✅ done | 3 days |
| **M3b** Attribution and absorption | ✅ done | 2 days |
| **M3c** Disclosure classes, grounds, monotone release | ✅ done | 3 days |
| **M4** Open tier — bundle, continue, profile, deposit | ⬜ | 1 week |
| **M5** Conformance suite | ⬜ | 3–4 days |

118 tests pass; 2 are skipped — one named for M4, one platform-specific.
Acceptance tests 1–7 pass; test 8 (bundle here, continue there) awaits M4.

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

## M2 — Integrity ✅

- [x] Complete the act vocabulary — `grrp connect <state> --to <ref>` and `grrp verify <state>`
      *(the eight acts, P-IV Def. 6.2)*
  - [x] External references carry a persistent identifier and **its scheme**, plus **the date the
        reference was made** — a reference to something since changed is uninterpretable without it
        *(P-IV Req. 5.5)*
  - [x] A connection to another **state** needs no new field: the transition that produced it becomes
        a parent, so the link is in the graph and travels with the record
  - [x] A **failed** verification is recorded `unresolved`, so it stands on the open register until
        something answers it — which is also where a stranger could take it up
  - [x] Neither connection nor verification supersedes the state it concerns
- [x] `grrp check` verifies the **whole chain**, not each record in isolation
  - [x] An altered early transition invalidates every descendant (parents are inside the payload)
  - [x] Content missing **without a recorded redaction** is a failure, not an absence
- [x] Administrative operations: same envelope, **mandatory `kind`**, `act`/`target`/`relation`/
      `disposition` **absent**, an `operation` field in their place; never presented as transitions
      *(P-IV Req. 4.6)*
- [x] `grrp redact <state> --ground <g>`
  - [x] Removes content; the skeleton stays valid and verifiable *(C8)*
  - [x] Recorded as an operation with performer, time and **ground covered by the identifier**, so a
        ground that could be altered afterwards would be no ground at all *(P-IV Req. 13.4)*
  - [x] **The graph is unchanged** — parent links, state references and the induced ordering survive
        *(P-IV Req. 13.5)*
  - [x] The redaction record is not removable; redacted content is **never represented as never
        having existed** — `show`, `log` and `export` all say so, with the ground
  - [x] Confirmation before removal, and a plain statement that **earlier git commits still contain
        the text** and that a copy already obtained by another party is beyond reach of both

### Decided in the course of M2 — flagged, not settled quietly

- **Content stays inside the versioned tree.** The specification prefers content held outside it
  (§21.5, weakness 3), because git history is immutable and a redaction cannot reach a prior commit.
  Moving it out would mean a `git clone` no longer carries the record, and portability would then
  depend on `grrp bundle`, which does not exist until M4. So content is versioned, `redact` removes
  it from the working tree, and the tool **says plainly what it has and has not achieved**.
  *Revisit at M4, when bundle can carry content.* **Touches C8, C10.**
- **Redaction grounds are a local vocabulary** (`erasure_request`, `consent_withdrawn`,
  `personal_data`, `hazard`, `legal_order`). No deployed vocabulary covers *why content was removed*,
  and this is deliberately separate from the four closed grounds of **restriction**, which concern
  disclosure rather than removal. A charter may replace it. **Touches C12.**
- **The per-record secret is still not decided** — see Open decisions. It has to be settled before any
  short redactable content is hashed, because it changes identifier construction.
  - [ ] Decide it.

---

## M3 — Group tier ⬜

Where credibility begins. **Minimum viable adopting unit: two parties who register each other's
transitions** *(P-II Claim 13.4)*.

### Identity and signatures ✅
- [x] `grrp key add <name> <pubkey>` — known parties in `.grrp/keys/`; `grrp key mine` prints what to
      hand to a colleague; adding a second party's key **moves the record to the group tier**
- [x] Detached ed25519 signatures over `{id, registrar, time}` — **never over `disclosure` or any
      field a later lawful operation may change** *(P-IV Req. 8.3)*
- [x] **Pseudonymous participation** — nothing anywhere requires a legal name, telephone number,
      affiliation or government identifier *(P-IV Req. 14.3)*
- [ ] Passphrase on the private key *(still deferred; a signature is what it protects)*
- [ ] Optional **bindings** to external identifiers: recorded as operations, visible wherever the
      party is shown, attributed, revocable *(P-IV Req. 14.4–14.5)*
- [ ] Assurance **by class and by act kind, never as an entrance gate** — gating a stranger's
      challenge to a publicly disclosed claim reproduces the bootstrap failure *(P-IV Req. 14.6)*
- [ ] Key rotation by an operation **signed with the old key**; loss via a charter procedure that is
      **marked as weaker than a signature** *(P-IV Req. 14.7)*
- [ ] Compromise = revocation with a date; prior registrations stay, marked

### Attestation ✅
- [x] At the group tier **an act is a proposal**, not a log entry — a party cannot register their own
      act, so what they perform waits for someone else. Proposals live outside `transitions/`, so
      registering never edits a file under it *(C2, C3)*
- [x] `grrp pending` — what waits on you, and what of yours waits on someone else
- [x] `grrp register <tx>` — **refuses when performer and registrar are identical**, naming the
      constraint and what to do instead *(C2 · acceptance test 7)*
- [x] Registration is **outside the identifier**, so registering a proposal does not change the thing
      its children point at
- [x] `grrp check` verifies the signature, and catches a record marked attested whose registrar is
      its own performer
- [x] `grrp withdraw <tx>` — a further **challenge** that retracts, naming the registration among its
      parents. Nothing is deleted; a reader sees both *(P-IV Req. 8.7)*. **A withdrawal is itself an
      act, so at the group tier it too must be registered by another party** — the rule does not bend
      for the party undoing something
- [x] **No aggregate over attestations** — not counts, depths, ratios or derived scores *(C6)*
- [ ] A standing arrangement (a supervisor routinely registering a student's transitions) **recorded,
      not forbidden** *(P-IV Req. 8.2)*

**Decided:** `GRRP_KEY` selects which local key acts, for a machine two parties share and for the
tests, which need a second party to exercise registration at all. One key is the ordinary case.

### Attribution and absorption ✅
- [x] `--contributor name=Role` on every act — CRediT identifiers stored, **never display labels**,
      because a record holding the word "Methodology" is uninterpretable once a second vocabulary
      uses it differently *(C12 · P-IV Req. 7.3)*
- [x] `--from <state>` on every act — the link records the state, **the party who produced it**
      (looked up from the record, so nobody types a key), and the transition that took the content
      *(P-IV Req. 9.3)*
- [x] `grrp attribute <proposal>` — adds contributors or absorption **to a proposal**, before anyone
      has registered it. A recorded transition is never edited, and attempting it **refuses with C3
      and points at `grrp contest`** *(C3)*
- [x] Absorption links **presented alongside the transition wherever it is displayed** (`export`)
- [x] **No veto.** No `approve`, `deny`, `block`, `veto`, `permit` or `consent` anywhere in the
      command surface, and a test that keeps it that way. A party who does not want their state
      absorbed has **one instrument: its disclosure class** *(P-IV Req. 9.4)*
- [x] `grrp contest <tx>` — a challenge that **disputes** (`cito:disputes`), naming the transition
      among its parents. Nothing deleted or altered; **no party is empowered to resolve it**
      *(P-IV Req. 9.5)*
- [x] **No measure of the influence of an absorbed state** *(C6)*
- [x] `grrp transform --with <state>` — a **synthesis**: a state its performer composed from what
      several branches reached. It does **not** close them, and nothing is combined by rule
      *(P-IV Def. 10.4, Req. 10.5)*

**Found and fixed in the course of it:** the release record stored an `attested` flag captured when
the release was still a proposal, so an exported document went on saying "unattested" after the
release had been registered. Now derived at export time from the log — the stored-derived-value
mistake, in miniature *(P-IV Req. 4.4, 5.3)*.

### Disclosure ✅
- [x] `grrp disclose <tx> --class <c> --ground <g> [--release-at <date>]`
- [x] `grrp charter adopt --classes a,b,c` — classes exist, are **ordered by inclusion** (narrowest
      first), are enforced, and are **opaque to the protocol**. **No model charter and no default
      set**: a specification supplying one would be a specification of governance *(P-IV §18.5)*.
      Without a charter there is nothing to disclose at, and the tool says so
- [x] `grrp charter adopt` again bumps the version; amendments are **prospective only** *(Req. 18.4)*
- [x] **Four grounds, closed set.** A value outside it is refused, naming the four *(P-III Req. 2.5)*
- [x] **Reject a restriction that declares no ground**, and display the ground wherever it is shown
      *(Req. 11.3)*
- [x] **Surface the residue.** Declaring a ground prints what it leaves disclosable **and the named
      failure it becomes if misapplied**. `grrp grounds` prints the whole typology
      *(P-III Req. 2.6 — the only part of the design that gains without giving something up)*
- [x] **Composition = intersection of residues**, and the tool says declaring more grounds is not
      free, since each is an assertion a reader may find false *(P-III Req. 7.2)*
- [x] **Monotone enforcement** *(C7)*
  - [x] Narrowing is refused, naming C7 and why a withdrawal cannot be effected
  - [x] No `unpublish`, `unrelease`, `hide`, `conceal` or `restrict` command exists
  - [x] A schedule **fires without a further act by any party** — derived from the log and the clock,
        so there is nothing to fire and nothing that can be forgotten *(Req. 12.4)*
  - [x] A schedule may be **shortened**; **extending or cancelling is refused and the attempt
        recorded** as an operation, because a charter may in some circumstances allow it and it
        should be visible that it was made
  - [x] `--release-at` **only with `vulnerability`** — the only ground with a terminus. Rivalry and
        appropriability end unobservably from here, and **hazard does not end** *(P-III Claim 7.4)*
- [x] **Per record**, never per repository or trajectory: records in one trajectory carry different
      classes *(Req. 11.5)*
- [x] Charter identifier **and version** recorded on every disclosure *(Req. 18.3)*
- [x] `grrp show` surfaces what is restricted, on what ground, and when it widens

### Decided in the course of M3c — flagged, not settled quietly

- **An undisclosed record is not a restriction without a ground.** Req. 12.2 fixes a restrictive
  default and Req. 11.3 demands a ground for anything below the widest class; read together they
  would demand a ground for every record ever made. The reading taken: a record with no disclosure
  operation is **not yet published**, which is a different thing from **withheld**. The ground
  requirement bites when a restriction is imposed. **Touches C7.**
- **Redaction grounds and grounds of restriction are separate vocabularies**, as flagged at M2 —
  one concerns removal, the other disclosure. `grrp grounds` prints only the four.
- **Operations carry `subject` and `payload`** rather than a field per operation type. Both are
  covered by the identifier, so a declared ground that could be altered afterwards would be no
  ground at all. Redaction was migrated to the same envelope.
- **Disclosure operations chain**, each taking the previous as a parent. Ordering by recorded time
  does not work: two changes made in the same second have no path between them, and the tie would be
  broken by identifier, which is arbitrary. *(Found by a failing test, not by argument.)*

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
