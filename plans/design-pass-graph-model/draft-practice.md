# GRA from the bench: node kinds, edge kinds, components, actions for working researchers

Lens: a small lab / theory group / field team, day to day. Every item below is tagged **[P]** protocol (in the signed record) or **[A]** applicative (mutable, never signed, never bundled), and mapped to the exact protocol mechanism — act / target / relation / trigger / disposition / artefact / field — or refused with the nearest lawful alternative. Nothing here proposes a new record type: node kinds are *presentation kinds* over the five-dimensional transition vocabulary; occasion and material kinds are realised by trigger + shared cited artefact, per the settled meeting precedent.

---

## 1. Node kinds

### 1.1 Act-kinds (presentation of the 8 closed acts) — all [P] facts, [A] rendering

| Node kind | Protocol realisation | Researcher reading |
|---|---|---|
| Question | `act: question`, origin of a trajectory | "what we are asking" |
| Claim | `act: claim` | a stated position or result |
| Challenge | `act: challenge` | an objection, anomaly, counterexample |
| Transformation | `act: transformation` | a reformulation, revision, derivation step |
| Decision | `act: decision` | a chosen path, an abandoned one |
| Connection | `act: connection` | a reified semantic edge (see §2) |
| Verification | `act: verification` | replication, check, confirmation |
| Release | `act: release` | disclosure event: preprint, dataset publication, talk |

No further act-kinds may exist (closed vocabulary). Every research-life "event node" below must resolve to one of these eight or be applicative.

### 1.2 Occasion-kinds — [A] grouping over [P] facts; **never** a record type

Realised uniformly as: shared cited artefact (same hash ⇒ one node, many edges) + `trigger` on the resulting transitions + CRediT `contributions` per act. An occasion that produced no transition is a calendar entry only (C1).

| Occasion kind | Trigger | Shared artefact (by hash or scheme) | Typical resulting acts |
|---|---|---|---|
| Lab meeting | `discussion` | minutes | decision, challenge, claim |
| Seminar / invited talk | `discussion` or `literature` | slides, abstract, recording hash | question, connection, challenge |
| Reading group / journal club | `literature` + `discussion` | the paper (`doi:`/`arxiv:`) — the external work itself is the shared node | challenge, connection, claim |
| Supervision meeting | `discussion` | meeting note | decision (student), with supervisor's part typed `credit:Supervision` in `contributions` — a role in an act, never a status |
| Whiteboard session | `discussion` | photo of the board (hash) | transformation, claim |
| Experiment run | `experiment` | run log, raw output (hash) | claim, challenge (anomaly), verification |
| Simulation / parameter sweep | `simulation` | config + output hashes | claim, challenge, verification |
| Field trip / observation session | `observation` | field notes, GPS-stripped-as-needed media (hash) | claim, question, challenge |
| Failed attempt | `failure` | whatever evidenced the failure | decision (abandon path), challenge |
| Conference attendance | `literature`/`discussion` | the talk's paper or notes | connection, question |
| Onboarding of a newcomer | `entering_party` | the material absorbed (see §6.14) | question, claim, connection with `absorption` filled |
| AI-assisted analysis session | `ai_suggestion` | model output artefact | any act — model may occasion, never perform/register |

**Occasion detection is derived, not stored**: the UI clusters transitions sharing an artefact hash + trigger + time window. No occasion identifier enters the record.

### 1.3 Material-kinds — [P] when cited, [A] while in workspace

A material node exists in the graph **only because at least one transition cites it** in `artefacts` (C1, C4). Before citation it is a workspace file, invisible to the record; a test already asserts upload changes no transition.

| Material kind | Realisation |
|---|---|
| Held artefact (data file, figure, script, minutes, draft, photo, transcript, calibration file, instrument config) | `state:`/hash reference in `artefacts`; bytes in project file store (C8: deletable, skeleton stays valid) |
| External paper | `doi:` / `arxiv:` / `isbn:` reference — same hash/id ⇒ one shared node lab-wide |
| Web resource / preprint server page / code repo URL | `url:` reference |
| Dataset (versioned) | each version = distinct hash = distinct material node; "new version" = transformation transition, target `artefact`, relation `modifies`, citing the new hash, parent = the transition that cited the old one (C4: specific prior state, never "the dataset" as a whole) |
| Code release | `release` act, target `artefact`, citing the archive hash and/or `url:` of the tag; day-to-day commits stay applicative (git is workspace) |
| Manuscript draft vN | hash of the draft; revision = transformation citing the new hash (see §6.10) |
| Ethics approval, grant letter, MTA, DUA | artefact cited by the `decision` it licensed |
| Physical specimen / sample | **cannot be hashed** — nearest lawful: its metadata sheet (ID, collection record) is the artefact; the specimen itself is applicative inventory (§5) |
| Instrument | **refused as record node** (a thing-as-a-whole violates C4's spirit; a person/thing-centric graph invites C6). Nearest lawful: instrument *settings/calibration file* as artefact; instrument registry + booking in the local plane |

---

## 2. Edge kinds

### 2.1 Structural (facts; no identity, no components, no actions)

| Edge | Source | Notes |
|---|---|---|
| Follows (parent, same trajectory) | `parents` list | the DAG; branching = divergence, permanent (C5: never combined, the word never appears) |
| Crosses (parent, other trajectory) | `parents` entry created by `grrp connect` | cross-question edges are ordinary parent edges |
| Cites-artefact | `artefacts` field | transition → material node |
| Registered-by (attestation) | `registration` field | shown per transition only; **never aggregated per registrar** (C6) |
| Absorbed | `absorption` field | newcomer's transition → the specific prior states absorbed |

### 2.2 Semantic (reified — each IS a connection transition, so it is a full node)

One presentation edge-kind per relation: the 16 CiTO bindings (`extends, modifies, refines, replaces, disagrees, agrees, supports, refutes, confirms, retracts, repliesTo, usesMethodIn, relates, supportedBy, usesDataFrom, disputes`) plus charter-local `generalises, specialises, transfers` (flagged, never presented as bound). Because the edge is a transition, it gets **every node component for free** — including workspace storage ("why this connection matters" can hold pages of argument, figures, worked examples). This is the answer to "edges should also have components": already true by reification; nothing to add at the protocol layer.

### 2.3 Derived presentation edges — [A] only, recomputed from files (C11), never stored, never exported

| Derived edge | Computed from | Guard |
|---|---|---|
| Same-occasion (two transitions cite the same minutes/run log) | shared artefact hash | no count displayed across occasions (C6) |
| Same-source (two transitions cite the same paper) | shared `doi:` | reading-group view |
| Chronological adjacency within one project | `performed` | within-project only, no cross-project comparison (C6) |

### 2.4 Refused edge features

- **Edge weights, strengths, confidence scores** — C6. Nearest lawful: the connection transition's *content* states the strength in prose; its `disposition` (accepted/contested/unresolved) is the only typed qualifier.
- **Person→person edges** (co-author graph, supervisor graph) — person-centric graph, C6/monitoring. Nearest lawful: none; CRediT roles live inside acts.
- **"Blocks/depends-on" task edges** — [A] task board only, never exported.

---

## 3. Components (the four classes, assigned per kind)

**Universal on every node and every reified edge** (the requested common component): **Local storage / workspace-facet** — `nodes/<transition>/`, ordinary mutable folder, records nothing; material enters the record only via a bridge action (§4.3).

### 3.1 Record-facet components (projections of signed fields; strictly read-only)

| Component | Fields shown | Carried by |
|---|---|---|
| Identity | hash id, full and copyable | all record nodes |
| Type | act, target, relation (with bound/local flag), trigger, disposition | all |
| Provenance | performer, `performed`, contributions (CRediT), absorption, registration (attested? by whom? signature) | all |
| Material list | `artefacts` with digests — reads as the per-node file list; **cite, not own** | all |
| Bearing | parents / children / crossings | all |
| Occasion badge | trigger + shared-artefact cluster | transitions from occasions |
| Rationale | the state file's content (the "why") | all; the payload of connection edges |

### 3.2 Sidecar-facet components (disclosure; widen-only, C7)

| Component | Content |
|---|---|
| Disclosure status | current audience; history of widenings |
| Ground of restriction | one of the four closed grounds (rivalry/hazard/vulnerability/appropriability) with its stated residue |
| Release schedule | `release_at` (vulnerability only); shorten-only; refused extensions are themselves recorded |
| Redaction notice | redaction ground; skeleton+signature remain valid (C8) |

### 3.3 Workspace-facet components (mutable, never bundled, deleting costs nothing)

Notes/scratch; draft material; run outputs awaiting citation; PDF annotation layer on cited papers; figure staging; code checkout; analysis notebooks; reviewer-response drafting table; onboarding tour bookmarks; task checklist (per node, not per person).

### 3.4 Local-plane-facet components (.grrp/events etc.; **never exported**)

Meeting details (time, place, video link, agenda); calendar entry; instrument booking; deadline entry (conference, grant, ethics renewal); reminder. **Commitments and chronology only, never activity** (settled). No attendee list anywhere, even locally: attendance is never recorded.

---

## 4. Actions (three classes)

### 4.1 Recording actions (each produces one transition through grrp; named by act)

`ask` (question — opens a trajectory), `claim`, `challenge`, `transform`, `decide`, `connect` (creates a semantic edge = full transition), `verify`, `release`. Plus **register/attest** (registrar ≠ performer at group tier, C2 — the credibility mechanism) and the administrative operations already in vocab: `disclosure_changed` (widen only), `redaction`, `key_rotation`, `fork_declared`, `attribution_contested`, `binding_recorded`, `deposit_recorded`.

### 4.2 Applicative actions (change workspace/local state; produce nothing in the record)

Schedule meeting; add-to-calendar; join-meeting (opens the link); book instrument; upload file to workspace; annotate PDF; edit notes; arrange/filter/pin the graph; add deadline; start onboarding tour; delete any of the above. A test-backed invariant: none of these touch the transitions directory.

### 4.3 Bridge actions (deliberate, visible promotion of workspace material into the record)

Cite-material (new transition whose `artefacts` includes the file's hash — usually a `connection` when attaching after the fact, per C3); cite-external (`doi:`/`arxiv:`/`url:`); attach-minutes (the meeting bridge); publish-dataset-version (release citing the hash); deposit (release + `deposit_recorded`). The bridge is always an act — there is no silent "sync folder to record".

---

## 5. Scenario walkthroughs (the daily-life checklist, each mapped)

1. **Lab meeting** — [A] schedule + details in local plane. During: notes in a workspace. After: attach-minutes bridge; each outcome its own transition, `trigger: discussion`, minutes hash shared ⇒ one meeting node, many edges; `contributions` per act. Nothing recorded ⇒ calendar entry only (C1). Attendance never recorded.
2. **Seminar** — same shape; external speaker without a key is not a performer: the lab member who took something from it performs (e.g. `connection`, relation `relates`/`extends`, `trigger: literature`) citing the abstract/slides.
3. **Reading group** — the paper (`doi:`) is the shared node. Per participant: `challenge` (relation `disputes`), `claim` (relation `agrees`/`supports`), `connection` (relation `usesMethodIn`) with `trigger: literature`; disagreements between members stay as sibling transitions with `disposition: contested` or `unresolved` — no combining (C5).
4. **Experiment + runs** — design: `decision`, target `method`, citing the protocol/SOP hash. Each run's outputs land in workspace (recording nothing — C1 protects against run-logging bureaucracy). A run that shifted understanding: `claim`/`challenge`/`verification`, `trigger: experiment`, citing run log + data hashes, parent = the specific hypothesis state (C4). Anomaly: `challenge`, `disposition: unresolved` — and it may lawfully stay unresolved forever. Deviation from protocol: charter-extended `target` (lab charter adds deviation types — explicitly anticipated).
5. **Datasets** — see §1.3; cross-trajectory reuse: `connection`, relation `usesDataFrom` (cito:usesDataFrom), which also makes the source transition a parent. Publication: `release` + `deposit_recorded`, DOI bound via `binding_recorded`.
6. **Code** — repo is workspace. A result depends on code: the transition cites the exact archive hash (`usesMethodIn` for someone else's code). Release: `release`, target `artefact`. CI, branches, issues: all [A].
7. **Instruments** — registry, booking, maintenance log: [A] local plane (booking is also presence-adjacent — never exported). Calibration file: artefact cited by the runs that depended on it. Restricted access: **rivalry** ground — the restriction covers access, never the trajectory (its stated residue).
8. **Field observations** — `trigger: observation`; field notes/media by hash; consent forms are artefacts cited by the `decision` to collect; personal data in content: redaction ground `personal_data` removes bytes, skeleton+signatures survive (C8). Works offline in the field (C9) — record at camp, register on return (C2 allows registrar later than performer).
9. **Peer review received** — reviewer with a key (best): they perform `challenge`, relation `disputes`, `trigger: objection`, we register (C2). Reviewer anonymous/external: we perform transitions responding, `trigger: objection`, citing the review report hash; response letter = `transformation` + `repliesTo`. Point conceded: `disposition: accepted` on our replying transition; point stood-beside: `unresolved` — the mandatory honesty case.
10. **Revision cycles** — each draft a hash; each revision a `transformation`, target `artefact`, relation `modifies` (cito:updates), parent = the previous draft's transition (C4). Camera-ready: `release`. The revision chain is the trajectory itself — no separate "version history" mechanism.
11. **Failed directions** — `decision`, target `path`, `trigger: failure`, relation `retracts` or `replaces` on the specific abandoned state; content says why. The branch stays in the DAG forever (C3) — presentation may render "closed path" leaves dimmed, never deleted, never scored.
12. **Conference deadlines** — [A] local calendar (commitment, legitimate). Submission: `release` citing the submitted PDF hash; acceptance letter an artefact; camera-ready another `release`. No countdown-pressure analytics beyond the plain date.
13. **External collaborations** — outsider gets a key ⇒ ordinary performer; `trigger: entering_party` on their first transitions with `absorption` filled. They may take the whole record and continue elsewhere without permission (C10); divergence is `fork_declared`, not a fight over the canonical copy. Disputed credit: `attribution_contested` — an operation, not an edit (C3). IP-constrained collaboration: **appropriability** ground; residue (existence, questions, decisions, negative results) stays visible.
14. **Student joining mid-project** — [A]: onboarding tour over the DAG (guided path through prior states — the graph *is* the onboarding document). [P]: their first acts carry `trigger: entering_party` + `absorption` referencing the specific states absorbed (C4 — never "joined the project"); their key registered; they attest others' acts immediately (C2 gives newcomers a real role from day one). Their naive `question` transitions are first-class — a newcomer's question is an origin state, not noise.
15. **Preregistration** — `release` of the hypothesis state before the experiment; later `verification`/`challenge` transitions parent it. **Vulnerability** ground with `release_at` for embargoed prereg; shorten-only.
16. **Grants / ethics / admin** — letters are artefacts cited by `decision` acts; `credit:FundingAcquisition` types the part; renewal dates are [A] calendar commitments. Grant reporting **must not** become a metrics surface: export for a funder is a bundle plus prose, never a dashboard (C6).

---

## 6. Refused, with nearest lawful alternatives

| Wanted in labs everywhere | Why refused | Nearest lawful |
|---|---|---|
| Person node / member page / profile graph | person-centric graph → C6, monitoring | CRediT contributions inside each act; filter view by performer is at most a transient [A] query, never a stored or exported view |
| Project node, project status | C4: nothing attaches to a project as a whole | the trajectory's question node is the anchor; chronology within one project is permitted, uncompared |
| Attendance, attendee list, RSVP tracking | settled: never recorded, even locally | meeting logistics without people; presence is inferred by no one |
| Activity heatmap, streaks, per-person timeline, leaderboard, h-anything | C6 verbatim | calendar of commitments; within-one-trajectory counts shown without comparison |
| Merge of divergent branches | C5; the word never appears | a new transition citing both states as parents *as a claim about their relation* (`connection`) — divergence remains visible |
| Edit/annotate a past transition "to fix it" | C3 | new transition, relation `replaces`/`retracts` |
| Mark-answered / close-question button | dispositions closed; fabricated closure | a new `decision` or `verification` with `disposition: accepted`; or it stays `unresolved`, which is the point |
| Meeting/experiment as new record types | closed act vocabulary; portability | occasion pattern (trigger + shared artefact + contributions) |
| Auto-record every run / every commit | C1 byproduct-only; recording cost kills adoption | workspace holds everything; bridge actions promote deliberately |
| Progress %, importance stars, priority ranks | C6 scalars | disposition + prose in state content |
| Unpublish / retract-from-view | C7 widen-only | `retracts` relation (the retraction is public); redaction removes bytes only, with a stated ground |
| AI agent authoring or registering transitions | performer/registrar are keyed parties | `trigger: ai_suggestion` marks provenance; a person performs |

---

## 7. Priorities from this lens

The occasion pattern (minutes-hash + trigger + contributions) covers meetings, seminars, reading groups, runs, and field sessions with **zero new protocol surface** — invest in making the bridge actions (attach-minutes, cite-material) one gesture each, because C1 means anything slower simply won't be recorded. Second: reviewer keys and `entering_party` onboarding, since peer review and mid-project joins are where the record either earns trust (attested challenges, honest `unresolved`) or gets bypassed. Everything a forge would ship as a dashboard is either the [A] commitments calendar or refused.