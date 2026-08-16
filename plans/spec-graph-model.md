# The graph model: node kinds, edge kinds, components, actions

**Specification, v1 — draft for discussion.** Applicative-layer specification over GRRP v0.1.
Builds on [design-nodes-time-and-occasions.md](design-nodes-time-and-occasions.md); where they
overlap, this document governs.

How it was produced: three independent design passes (research practice, component architecture,
adversarial conformance), then three verification passes (constraint audit — 17 findings,
completeness — 28 gaps, simplicity — 22 cuts). Every finding is either incorporated below or
answered in §10. The synthesis leans deliberately toward the simplicity verdict: **v1 commits to a
small kernel, and defers the extension machinery until a second real community exists.**

---

## 1. The model, affirmed

The requested reading — *each vertex is an event; relations are typed; both nodes and edges carry
types, components, and actions* — is not a departure from the protocol. It **is** the protocol:

| requested | in GRRP |
|---|---|
| an event | a **transition** — something happened to an understanding |
| an event's type | the five-dimension factored type: act × target × relation × trigger × disposition |
| a typed relation | a `parents` entry (structural) or a **connection transition** carrying a CiTO relation (semantic) |
| a relation with components | already true: a semantic relation *is* a transition, so it has content, artefacts, provenance — and a workspace |

Two invariants govern everything below:

**I1 — Kinds are lenses, not types.** No kind adds a field to a transition, mints a record type, or
changes what `grrp` writes. Delete every kind and the record is untouched. This is what makes the
whole applicative layer safe to build, rebuild, and throw away.

**I2 — `grrp` is the sole record-writer.** Every record-writing action is a thin form over exactly
one `grrp` invocation. The UI never constructs a transition skeleton, never computes an identifier,
and surfaces `grrp`'s refusals verbatim. One implementation owns lawfulness. (Already the rule in
`web/packages/server/src/records.ts`.)

---

## 2. Subjects — what can be selected

A **subject** is a thing that can be selected, carries components, and offers actions.

### v1 subjects

| subject | identity | exists when |
|---|---|---|
| **transition** (any of the 8 acts, connections included) | its id | recorded |
| **material** — held artefact | `state:sha256:…` over its bytes | **cited by at least one transition** |
| **material** — external work | `doi:` `arxiv:` `isbn:` `url:` | cited by at least one transition |

A workspace file that nothing cites is not a subject and does not appear in the graph (C1, C4).

### Deliberately not subjects

- **Structural edges** (`parents` entries, artefact citations). They are facts inside a signed
  payload, not claims — no identity, no components, no actions. *To contest a parent link,
  challenge the **child** transition: the link lives in its signed payload, and C4 hands you the
  specific state.* This paragraph exists so that edge identity is never added "just for
  commenting" — the request will come, and this is the answer.
- **States.** A state is reached through the transition that produced it. Pickers pick states;
  the panel opens the producing transition. One subject per event.
- **Persons, projects.** Refused outright — §8.

---

## 3. Node kinds

Three families, hardcoded in v1 (no plugin machinery — §9).

### 3.1 Transition kinds — the eight acts, as they read to a person

| label shown | act underneath | disposition default |
|---|---|---|
| Question | `question` | unresolved — and it stays so; that is the design |
| Position | `claim` | accepted |
| Position, changed | `transformation` | accepted |
| Objection | `challenge` | unresolved / contested |
| Decision | `decision` | accepted |
| Connection | `connection` | accepted |
| Check | `verification` | accepted (or unresolved when it failed) |
| Release | `release` | accepted |

**Label discipline (C12):** labels map 1:1 onto acts; the protocol term is always inspectable one
gesture away (shown in the record panel); labels are never persisted into anything that travels.
No ninth label may exist, because no ninth act exists.

### 3.2 Material kinds

- **Held artefact** — bytes in the project store or a workspace, identified by hash. The digest is
  always displayed: it is what a transition cites and what a reader elsewhere checks.
- **External work** — `doi:` / `arxiv:` / `isbn:` / `url:`. Renders **fully offline** (identifier +
  citing transitions); live metadata fetch is an optional enhancement cached under C11, never a
  dependency (C9). The same identifier cited from anywhere in the project is **one node** — this is
  how a paper read by the whole group appears once with many edges.

### 3.3 Occasion kinds — derived, never created

An **occasion** (meeting, experiment run, observation session, reading, failure…) is not a record
type and not a creatable node. It is a *reading* of the graph:

> an artefact node whose citing transitions carry an occasion trigger
> (`discussion`, `experiment`, `observation`, `simulation`, `literature`, `failure`, or a
> charter-local trigger).

The trigger is the label: an artefact cited with `discussion` presents as a meeting-like occasion.
Three rules, each of which closes a hole the review found:

1. **No create-occasion affordance exists.** An occasion with no transitions behind it is a
   calendar entry, not a node (C1). The button will be asked for; it does not get built.
2. **No roster, ever.** The occasion panel lists its *transitions*. It never unions their
   performers into a "participants" view — that would rebuild the attendance list from signed
   parts, and it is the single most likely quiet violation in this design.
3. **Occasion membership is the citation itself.** No time-window clustering, no inference: the
   shared artefact's citing edges *are* the gathering.

---

## 4. Edge kinds

### 4.1 Structural — facts

| edge | read from | drawn |
|---|---|---|
| follows | `parents`, same trajectory | plain line |
| crosses | `parents`, another trajectory | distinct line — the structure the graph view exists to show |
| cites | `artefacts` | dashed line to the material node |
| absorbs | `absorption` | shown in the panel; drawn on demand |
| registered-by | `registration` | a badge on the node — **never aggregated per registrar** (C6) |

No identity, no components, no actions (§2).

### 4.2 Connection — the reified semantic edge

One presentation covers **all** relations: the sixteen CiTO bindings and the three charter-locals
(`generalises`, `specialises`, `transfers` — flagged as unbound, never presented as CiTO). Not
nineteen kinds; one kind that renders its `relation` field.

- **Drawn as an edge** in the graph (its parent link to what it connects); **opened as a node** in
  the panel. One subject, two renderings.
- **Multi-parent connections are first-class.** A transition citing two divergent states as parents
  — saying in its content what it makes of the divergence — is the lawful neighbour of the refused
  combining operation (C5). It draws as a fan; it is still one subject.
- **This is where "edges have components" is true** — and only here. A connection has content, a
  workspace (the dossier of a disagreement lives *on the edge*), provenance, disclosure. Each
  component earned its place on this subject under the same twelve constraints as anywhere else;
  nothing is inherited "for free".

---

## 5. Components — exactly four

One per storage class. The class fixes where data lives, who writes it, and whether it travels —
so "does it travel?" is answerable by grep.

| component | class | lives at | written by | in a bundle? | in git? |
|---|---|---|---|---|---|
| **Record panel** | record-facet | signed YAML + state files | `grrp` only | **yes — it is the record** | yes |
| **Disclosure panel** | sidecar-facet | disclosure sidecar + operations | `grrp disclose` / `redact` | yes | yes |
| **Workspace** | workspace-facet | `nodes/t/<id>/` · `nodes/a/<hash>/` | any project party, via the app | **never** | yes |
| **Calendar entry** | local-plane | `.gra/calendar/` | the host app | **never** | **no — gitignored** |

### 5.1 Record panel

The whole signed payload, read-only: act (with its presentation label *and* the protocol term),
target, relation (with its CiTO binding, or flagged `local:`), trigger, disposition, performer,
contributions (CRediT), absorption, **the state content rendered as markdown**, artefact citations
with digests, attestation status, and the identifier in full.

- **Two timestamps.** Registration may lawfully be later than performance (offline field work;
  C2 applies at registration, not at recording). Chronology orders by `performed`; the panel shows
  both times whenever they differ materially. This is the honesty surface for offline recording.
- **Counts live here and only here.** The C6 carve-out (counts within one trajectory, uncompared)
  renders exclusively in the *selected* subject's panel — "this question has 4 objections, 2
  unanswered" — never as decorations across the canvas. Badges on many nodes at once are
  comparison by juxtaposition.

### 5.2 Disclosure panel

Class, ground (with its object and residue), `release_at` (shorten-only — and a refused extension
shows here **as a recorded fact, not an error**), plus the operations history touching this
subject: disclosure changes, redaction notices (with ground), contested attributions. **Operations
render as panel facts, never as graph nodes.**

### 5.3 Workspace

The one **universal** component: every transition subject and every material subject carries one —
which, by reification, means every semantic edge carries one (the requirement that edges have
storage, satisfied structurally). Folders allowed; the path guard already refuses escape.

**The workspace is project-shared scratch, not private.** It travels with a git clone (though never
in a bundle), and every project party can read it. Anything private — personal notes, drafts not
for colleagues, pins — belongs in the **local plane**, which never leaves the machine. The
review found the drafts quietly contradicting each other here; this paragraph is the ruling.

Deleting workspace content costs nothing and records nothing — test-enforced: *every applicative
action leaves `transitions/` byte-identical* (the existing upload test, generalised).

### 5.4 Calendar entry

When / where / link. **The schema contains no people fields** — not attendees, not organiser, not
RSVP. Attached to occasion subjects where one exists; **future occasions are free-standing entries**
in `.gra/calendar/`, attached to nothing (the meeting node cannot exist before its minutes are
cited — the review caught that a subject-bound schedule would pressure someone into building a
create-meeting-node path).

Legitimate calendar content: scheduled occasions, `release_at` commitments, embargo expiries,
deadlines *of the calendar's owner*. Never: anyone's activity, anyone's presence, a deadline
attached to a question or an objection ("resolve by Friday" — the vocabulary keeps `unresolved`
precisely so closure is never owed on a date).

---

## 6. Actions — exactly two classes

The review considered and rejected two more (a separate "bridge" class, and a declarative
precondition vocabulary). Both rejections are load-bearing:

- **Citing material is a parameter, not an action.** A free-standing "cite this file" button would
  produce a transition that exists so that a record exists (C1). Instead, every recording form
  carries an **artefact picker** — material is cited from *within* a real act with real content.
  That picker is the entire bridge between the layers, and crossing it is always deliberate.
- **No precondition layer beside `grrp`.** A declarative lawfulness vocabulary drifts from the
  implementation, and both candidates the drafts proposed encoded violations: an "open question"
  test would quietly mint the fourth disposition the protocol refuses, and a registrar-differs gate
  at recording time would block lawful offline work (C2 constrains *registration*, which may come
  later). The UI checks exactly one thing — a parent state is selected where the act needs one
  (C4) — and everything else is `grrp`'s refusal, shown verbatim.

### 6.1 Record-writing actions (through `grrp`; exactly one invocation each)

**Acts** — each a form: content (required, markdown) · parent/subject picker (C4; defaults to the
live position when unambiguous; `grrp` refuses ambiguity and the refusal is shown) · artefact
picker (optional; workspace files by digest, external ids by scheme) · vocabulary pickers
constrained to the bound sets, charter-locals flagged · contributions (optional; CRediT role per
named party — unilateral, and contestable by that party through `attribution_contested`, which is
the protocol's own consent mechanism).

| action | act | notes |
|---|---|---|
| Ask | `question` | opens a trajectory; the origin state |
| Take a position | `claim` | |
| Change a position | `transformation` | parent = the position changed |
| Object | `challenge` | disposition `unresolved` is the honest default |
| Decide | `decision` | including abandoning a path (`trigger: failure`) |
| Check | `verification` | outcome in content; a failed check stays `unresolved` |
| Connect | `connection` | relation required, from the bound set; cross-trajectory target makes that transition a parent |
| Release | `release` | disclosure act about specific states and artefacts — never a project-status marker |

**Operations** — same class, same discipline (one `grrp` invocation, refusal verbatim):

| action | operation | notes |
|---|---|---|
| **Register a colleague's act** | registration | completes an existing unattested transition. Refused when the keys are identical (C2). **Attestation is witnessing, not approval** — it asserts that an identified party registered an act at a time, and nothing about the content. Endorsement-as-record is an `agrees`/`supports` connection under the endorser's own key. |
| Widen disclosure | `disclosure_changed` | ground with object + residue; `release_at` shorten-only |
| Redact content | `redaction` | ground from the redaction vocabulary; bytes go, skeleton and signatures stay (C8) |
| Continue a bundle | import | unknown *act* → `grrp` rejects (closed vocabulary); unknown `local:` values → retained and flagged; same id with different bytes → refused loudly; dangling parents → rendered as "not held here" stubs |
| Declare a fork | `fork_declared` | C10 made first-class, not an edge case |
| Contest an attribution | `attribution_contested` | the dispute path for contributions |
| Record a binding / deposit | `binding_recorded` / `deposit_recorded` | DOI and archive identifiers, shown in the record panel |

**Global actions** (no subject yet exists): create a project, open a question, import a bundle,
generate/register a key. These live on the project shell, not on kinds — most are already built.

### 6.2 Applicative actions (record nothing — test-enforced)

Workspace file operations · calendar add/edit · **the join launcher** — a hyperlink stored in the
calendar entry that opens `{link}` and *writes nothing anywhere*; the moment joining leaves a trace
it is presence logging · private local-plane pins and bookmarks (invisible to every other party,
uncounted) · search (filters; any transient match ordering is never displayed as a number, never
persisted, never applied to performers) · bundle export (reads the record, writes a file; C10 is
owed, so friction here is a bug).

### 6.3 Where refusals surface

1. **Never offered** — the constitutive refusals of §8 have no UI surface at all.
2. **Disabled with the reason shown** — the one UI precondition (no parent selected).
3. **Refused by `grrp`** — stderr verbatim; nothing written.
4. **Refused and recorded** — where the protocol itself records refusals (a refused schedule
   extension), shown as a fact of the record, not as an error.

---

## 7. The meeting, end to end

The motivating example, run through the whole model:

**Before.** A free-standing calendar entry in `.gra/calendar/` — when, where, link. Agenda drafted
wherever its author likes (a workspace, the local plane). *Add to calendar* and *Join* are
applicative; join opens the link and writes nothing. There is no attendee field to fill in, because
the schema has none. Nothing has been recorded (C1).

**After, if it changed something.** The minutes land in a workspace. Each outcome is recorded as
its own act — a decision, an objection, a changed position — with `trigger: discussion`, citing the
minutes' digest through the artefact picker, contributions typed per act (CRediT: who conceived,
who analysed, who supervised — a role in an act, never a presence at an event).

**The meeting node** is the minutes artefact: same hash, one node, its citing edges are the
gathering. Components: record panel (the citing transitions, the digest), workspace (source
notes, follow-ups), calendar entry (the past schedule, locally). The panel lists transitions —
never a merged list of people.

**After, if nothing came of it.** It remains a calendar entry. That is not a failure to record;
that is C1 working.

---

## 8. Constitutive refusals — one page, closed

Each will be asked for. Each answer is one sentence a user can accept.

| refused | constraint | the sentence |
|---|---|---|
| Person / profile nodes; per-performer views, filters, timelines | C4, C6 | The moment a person is a node, everything they did aggregates to them and the graph becomes a dossier; a performer is a key on a transition, not a place things pile up. |
| Project-level nodes, project status | C4 | Nothing in the record attaches to a project as a whole; the record's version of stopping is silence. |
| Attendance, RSVP rosters, presence dots, "last active" | event-plane ruling | A log of who was present is a monitoring record by construction — presence is never written down in any layer that travels, and not in the ones that don't. |
| Shared bookings pairing a name with a time and place | C6 | Book slots, not people: shared state shows taken/free; your own bookings stay in your own local plane. |
| Activity feeds across projects, heatmaps, streaks, nudges | C1, C6 | Silence is a permitted state of work; an operation that exists so that a record exists is the definition of the failure. |
| Progress bars, importance, priority, weights, scores, centrality, size-by-degree, canvas count badges | C6 | Any computed prominence is a ranking with extra steps; a node with many edges is a node with many edges. |
| Kanban columns | closed dispositions, C12 | A column is a disposition vocabulary in disguise: "done" is the fourth value the protocol deliberately refused. |
| Reactions, emoji, votes | C1, C2, C6 | A reaction is an endorsement with no content and no attestation that exists to be counted; the record's 👍 is an `agrees` connection where you say why, under your key. |
| View counts, read receipts | C6, monitoring | Counting reads requires logging readers — a record of attention on both sides of the number. |
| Relevance as a standing index | C6 | Search filters; a stored ranking over trajectories is a measure adopted to direct attention. |
| Combining divergent states — and the word never appears | C5 | Both remain true records of what was understood; a transition may take both as parents and say what it makes of the divergence, but nothing collapses them. |
| Edit-in-place, delete, unpublish | C3, C7 | The signature covers the bytes; a corrected understanding is a new transition, so the record shows both that you were wrong and that you noticed. Others may have continued from what you shared — the ground under their work cannot be pulled back. |
| Mark-answered / close-question | closed dispositions | The lawful neighbour: record a decision or check that *answers* it, standing beside the objection forever; or it stays unresolved, which is the point. |
| Approval as a gate | C2, C10 | Nobody's permission is required to continue the record — including yours; endorsement is a record, never a lock. |
| Model as performer or registrar | C2 | `trigger: ai_suggestion` marks that a model occasioned a transition; a person performs it, and attestation between a person and their own tool is theatre. |
| Auto-recording runs/commits; template-solicited records | C1 | The workspace holds everything; the record holds what somebody deliberately said changed their understanding. |
| Occasion rosters | C6, monitoring | The occasion panel lists transitions, never a merged list of the people behind them. |

---

## 9. Extension — deferred, and why deferring is safe

The architecture pass designed a full manifest system: community kinds distributed with charters,
`degrades-to` fallbacks, a loader denylist, a projection mini-language. It is good design and it is
**not in v1** — it is a plugin architecture for an ecosystem of zero communities, and every piece
of it polices an extension surface that does not need to open yet.

What a charter can already extend **today**, through `grrp` alone: `target` values, `trigger`
values, local relations, and the redaction-grounds set (a local vocabulary by design). A community
occasion — "instrument calibration" — is a charter-declared trigger plus this spec's occasion
pattern, with no new machinery.

Deferral is safe **because of I1**: kinds are lenses that never touch the record. Any future
manifest system can re-read everything v1 writes. When a second real community exists, the
manifest sketch (three worked examples included) lives in the design pass records.

---

## 10. Rulings on the sharp questions the review surfaced

- **Redaction aftermath.** The node stays; the record panel shows *(redacted, on the ground of X)*
  where content was; kind matching never depends on bytes, only on signed fields, so redaction
  changes no node's kind. The app must purge its own derived caches (search text, previews) on
  redaction. Workspace copies of redacted material are the holder's obligation, surfaced as a
  notice — the git-history tension that paper IV itself names is real and stays open here too.
- **Import conflicts.** Same identifier, different bytes: refused loudly — that is tampering
  surfacing, not a a situation to smooth over.
- **Restricted disclosure rendering.** Each ground's stated residue determines which panel fields
  render for an out-of-audience viewer. The detailed per-ground table is deferred to the
  disclosure-UI milestone — marked open, not silently skipped.
- **Workspace path collisions.** Workspaces key by family-prefixed id (`nodes/t/…`, `nodes/a/…`),
  so a transition and an artefact sharing a digest tail cannot collide.
- **The charter as a subject.** A plain page rendering `charter.yaml` — which values it defines,
  which version — added to the build order; cheap, and the `local:` flags link to it.
- **Contributions consent.** Attribution is unilateral and contestable (`attribution_contested`).
  The spec states this rather than inventing a countersign flow the protocol does not have.

---

## 11. Build order

Unchanged in spirit from the design note; sharpened by this spec:

1. **Recording acts from the page** — the §6.1 act forms. The system is a viewer until this exists.
2. **Attestation** — register-a-colleague's-act (§6.1 operations). C2 is the credibility mechanism
   and is currently unreachable; two accounts already exist to test it.
3. **The panel → this spec's four components** (record, disclosure, workspace, calendar).
4. **The meeting flow** (§7): free-standing calendar entries + the artefact picker polish.
5. **Disclosure & redaction UI** (with the per-ground rendering table, resolving §10's open item).
6. **Import / fork surfaces.**

The standing gate remains: **use it on real work for two weeks** before building further layers on
top. Nothing in this specification has been lived with yet.

---

## 12. Open decisions

1. **Workspace = project-shared scratch** (travels with a clone, readable by all parties; private
   material goes to the local plane). This is a privacy ruling — confirm it.
2. **The manifest/plugin system stays out of v1.** Confirm the deferral.
3. **Contributions are unilateral and contestable** — the protocol's own mechanism, no countersign
   flow. Confirm.
4. Tab naming: this spec uses "graph" for the whole-project view currently labelled
   *Trajectories*. Rename or keep?
