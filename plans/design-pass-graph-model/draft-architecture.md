# The component/action machinery — modularity specification

Scope: the entity-component model for GRA. Node kinds and edge kinds are **presentation kinds over protocol facts** — the machinery below lets a community add kinds without touching protocol code, and guarantees that a record made under a community kind is still readable as plain GRRP anywhere.

---

## 0. Two invariants everything below obeys

1. **Kinds are lenses, not types.** No manifest ever adds a field to a transition, changes what `grrp` writes, or mints a new record type. A kind is a way of *reading* protocol facts (act, trigger, relation, artefact scheme) plus a bundle of applicative affordances. Delete every manifest and the record is untouched.
2. **Writes go through `grrp`.** A recording action is an argv template for the reference implementation, never a skeleton constructed by the UI (this is already the rule in `web/packages/server/src/records.ts`). Manifests can therefore never produce an unlawful record: `grrp` refuses, and the refusal is surfaced verbatim.

---

## 1. What a component IS

A **component** is a named facet of a subject (a node or a reified edge), belonging to exactly one of four **classes**. The class — not the manifest — fixes where its data lives, who may write it, and whether it travels.

| class | data lives at | written by | mutable? | travels in a bundle? | in git? |
|---|---|---|---|---|---|
| `record-facet` | signed transition YAML (`trajectories/<t>/transitions/*.yaml`), state files, `files/` digests | `grrp` only, via recording actions | never (C3) | **yes — it *is* the record** | yes |
| `sidecar-facet` | disclosure sidecar beside the skeleton | `grrp disclose` / `grrp redact` only | widens only (C7) | yes | yes |
| `workspace-facet` | `nodes/<subject>/…` (per-subject) or `files/…` (project) | any authenticated party, through the app | freely; deleting costs nothing | **never** | yes (ordinary files) |
| `local-plane-facet` | `.grrp/events/`, `.gra/calendar/` | the host application | freely | **never** | **no — gitignored, never exported** |

`<subject>` is the last segment of the subject's identifier (`nodeArea()` already does this), so it works identically for a transition id and for an artefact hash — which is what lets material nodes and reified edges get workspaces with zero new machinery.

### 1.1 Component *types* are a closed application registry; manifests *instantiate* them

Communities configure instances; they never define new classes and never define new storage semantics. The registry:

| type | class | what it shows / holds |
|---|---|---|
| `identity` | record-facet | the id, in full, copyable |
| `details` | record-facet | act, target, relation, trigger, disposition, performer, attested-by |
| `bearing` | record-facet | parents / children / crosses (from `parents`, reverse index) |
| `material` | record-facet | artefacts cited by hash; digests shown |
| `provenance` | record-facet | contributions (CRediT), absorption, registration signature |
| `projection` | record-facet | **configurable, community-definable**: a read-only field selection (§1.2) |
| `disclosure` | sidecar-facet | class, ground, `release_at`; widen-only controls |
| `workspace` | workspace-facet | the `nodes/<subject>/` folder: list, upload, delete, digest per file |
| `note` | workspace-facet | one named markdown file in the workspace, e.g. `nodes/<subject>/agenda.md` |
| `form` | workspace-facet | one named YAML file in the workspace with a declared schema, e.g. `calibration-setup.yaml` |
| `schedule` | local-plane-facet | a calendar entry (when/where/link). Never exported. **No attendee list field exists in its schema.** |
| `commitments` | record-facet | dated promises already in the record (`release_at`, embargo expiry) — read-only calendar |

### 1.2 The `projection` mini-language (how communities get custom read-only facets safely)

```yaml
- use: projection
  id: certificate
  title: Calibration certificate
  select:
    - field: artefacts
      where: { scheme: state }        # filter by exact field equality only
    - field: trigger
    - field: performed
```

`select` permits **field selection and equality filtering only**. No arithmetic, no `count`, no `sum`, no sort-by, no cross-trajectory reach. C6 is enforced structurally: the language cannot express a scalar over participants because it has no aggregation forms at all.

### 1.3 How the UI discovers a subject's components

Resolution, at render time, per subject:

```
subject (transition | artefact | reified edge)
  → collect candidate kinds whose `match` block fits (§3)
  → pick the most specific (most match fields); charter kinds beat builtins at equal specificity
  → components = universal set (§5) ∪ family defaults ∪ the kind's declared list, in declared order
  → no kind matches → family fallback (generic transition / generic artefact / generic connection)
```

The panel's tabs are exactly the resolved component list. Nothing computed is ever added by resolution — a kind can add facets, never metrics.

---

## 2. What an action IS

An **action** is a declared affordance on a kind, in one of three classes:

| class | records? | via | example |
|---|---|---|---|
| `recording` | **yes** — exactly one `grrp` invocation | argv template over a declared input form | *reply to this dispute* → `grrp record --act challenge --relation repliesTo …` |
| `applicative` | **no** — touches workspace or local plane only | app code (file write, calendar write) | *add to calendar*, *edit agenda note* |
| `bridge` | **yes** — promotes workspace material into the record by citing its hash | `grrp connect`/`record` with `--artefact state:sha256:…` | *cite these minutes* |

An action declaration:

```yaml
- id: reply
  class: recording
  label: "Reply"
  inputs:
    - { name: body, type: markdown, required: true }
  grrp: ["record", "--act", "challenge", "--relation", "repliesTo",
         "--parent", "{subject.id}", "--body", "{inputs.body}"]
  preconditions:
    - has-open-question            # C4: an identified prior state exists
    - registrar-differs            # C2, applies at group tier+
```

**Preconditions** come from a closed vocabulary owned by the app (manifests may only cite them): `has-open-question`, `registrar-differs`, `tier: {personal|group|open}`, `subject.act|trigger|relation|disposition in […]`, `artefact-hashed` (bridge only), `charter-declares: <value>` (the extended trigger/target is actually in the project's charter), `disclosure-permits`.

**What an action produces**: `recording` and `bridge` produce exactly one transition (its id comes back from `grrp`, never computed by the app); `applicative` produces file/calendar state and **a test-enforced nothing** in `transitions/` (the existing upload test generalises: *every applicative action leaves the transitions directory byte-identical*).

**Refusals surface at four distinct layers**, and the layer is part of the design:

1. **Never offered.** Constitutive refusals are enforced by the manifest *loader*, not by absence: a denylist rejects any manifest declaring merge/combine, edit/delete-transition, mark-resolved, attendance, weight, score, count-across, or person/project kinds (§4.3). A bad manifest fails to load *entirely*, with the reason; it is never partially honoured.
2. **Disabled, with the reason shown** — a precondition unmet (`registrar must differ from performer at this tier`). The button stays visible: the affordance exists, the condition doesn't.
3. **Refused by `grrp` at execution** — stderr surfaced verbatim, nothing written. One implementation owns lawfulness.
4. **Refused and recorded** — where the protocol itself records refusals (e.g. a refused extension of a disclosure schedule), the app shows the recorded refusal as a fact of the record, not as an error.

---

## 3. The kind manifest

One YAML file per kind. Locations (resolution order, most local wins only on *equal specificity*):

```
web/packages/server/kinds/*.kind.yaml            # builtin, ships with the app
~/.gra/kinds/<charter-id>/<charter-version>/     # community kinds, installed from the charter package
```

Community kinds are **distributed with the charter** (the charter is already an identified, versioned, locatable document — Req 18.1/18.3), cached by charter id + version. They are applicative material: **never inside `.grrp/`, never in a bundle.** A project's trajectory already records its charter id+version, which is how a host knows *which* kind package to fetch — and the record is complete without it.

Common header:

```yaml
kind: <namespaced id>        # gra.* reserved for builtins; charter kinds use <charter-id>/<name>
family: act | occasion | material | edge
version: 1                   # integer; bump on any change. Kind versions are NOT protocol
                             # or charter versions and never share a numbering (Req 19.2)
title: <label>
charter: null | { id: <charter-id>, version: <v> }
match: { … }                 # protocol facts only — never workspace state
degrades-to: transition | artefact | connection   # what a manifest-less host shows (§4.2)
components: [ … ]
actions: [ … ]
```

`match` may test only: `subject` (transition/artefact), `act`, `trigger`, `relation`, `target`, `artefact-scheme`, `cited-with-trigger` (for artefact subjects: the trigger on citing transitions). Nothing mutable, nothing computed.

### 3.1 Example — builtin occasion-kind: `meeting`

```yaml
kind: gra.occasion.meeting
family: occasion
version: 1
title: Meeting
charter: null
match:
  subject: artefact                 # the meeting node IS the shared minutes artefact —
  cited-with-trigger: discussion    # same hash, one node, many edges (settled design)
degrades-to: artefact
components:
  - use: identity
  - use: note                       # workspace-facet
    id: agenda
    file: agenda.md                 # lives at nodes/<hash>/agenda.md — mutable, unbundled
  - use: material                   # record-facet: the minutes bytes, digest shown
  - use: bearing                    # record-facet: every transition that cites this hash
  - use: schedule                   # local-plane-facet: when/where/link. .gra/calendar/,
                                    # gitignored. Schema has no attendee field.
actions:
  - id: add-to-calendar
    class: applicative
    label: "Add to calendar"
    writes: local-plane             # transitions/ provably unchanged
  - id: join-meeting
    class: applicative
    label: "Join"
    opens: "{schedule.link}"        # opens the link from the local plane; records nothing (C1)
  - id: cite-minutes
    class: bridge
    label: "Cite the minutes from an act"
    inputs:
      - { name: act, type: enum, values: [claim, challenge, decision, transformation] }
      - { name: body, type: markdown, required: true }
    grrp: ["record", "--act", "{inputs.act}", "--trigger", "discussion",
           "--artefact", "{subject.id}", "--body", "{inputs.body}"]
    preconditions: [has-open-question, artefact-hashed]
```

Note what is *absent*: no attendance component, no `mark-held` recording action. A meeting that produced nothing recorded is a calendar entry (C1) — the `schedule` component alone, in the local plane, is that entry.

### 3.2 Example — **community** occasion-kind: `instrument calibration` (no protocol code touched)

The community's charter declares an extended trigger `calibration` (triggers are charter-extensible; `grrp` stores it as `local:calibration`, accepted and flagged, per `vocab.py`). The charter package ships this manifest:

```yaml
kind: metrology-lab-charter/instrument-calibration
family: occasion
version: 2
title: Instrument calibration
charter: { id: "charter:metrology-lab", version: "3.1" }
match:
  subject: artefact
  cited-with-trigger: local:calibration
degrades-to: artefact
components:
  - use: identity
  - use: form                        # workspace-facet: structured setup notes, mutable
    id: setup
    file: calibration-setup.yaml
    schema:
      instrument: string
      reference-standard: string
      environment: string
  - use: projection                  # record-facet, read-only, no aggregation (§1.2)
    id: certificate
    title: Certificate
    select:
      - field: artefacts
        where: { scheme: state }
      - field: performed
      - field: performer
  - use: schedule                    # next calibration due — a commitment, not activity
actions:
  - id: schedule-calibration
    class: applicative
    label: "Schedule"
    writes: local-plane
  - id: record-calibration
    class: recording
    label: "Record calibration outcome"
    inputs:
      - { name: outcome, type: markdown, required: true }
      - { name: certificate, type: workspace-file, required: true }
    grrp: ["record", "--act", "verification", "--target", "method",
           "--trigger", "calibration",
           "--artefact", "{inputs.certificate.digest}",
           "--body", "{inputs.outcome}"]
    preconditions:
      - has-open-question
      - charter-declares: "trigger:calibration"
      - registrar-differs
```

The lab got: a recognisable node kind, a structured workspace form, a certificate facet, a due-date calendar, and a one-click lawful recording path — from one YAML file and one charter line. `grrp` was not modified; the act is `verification` (closed vocabulary), only the *trigger* is extended.

### 3.3 Example — edge-kind: `dispute` (a reified semantic edge)

A semantic edge is already a node: a `connection` transition carrying a CiTO relation, with the cross-question parent edge. The kind matches the transition, and the graph draws it as an edge while the panel opens it as a node.

```yaml
kind: gra.edge.dispute
family: edge
version: 1
title: Dispute
charter: null
match:
  subject: transition
  act: connection
  relation: cito:disputes
degrades-to: connection
components:
  - use: identity
  - use: details                    # relation shown with its CiTO binding, disposition shown
  - use: endpoints                  # record-facet (edge-family default): the two states it joins,
                                    # each openable — from parents + the connection's own reference
  - use: workspace                  # inherited universal (§5): nodes/<transition>/ — the dossier
                                    # of the disagreement lives HERE, on the edge itself
actions:
  - id: annotate
    class: applicative
    label: "Add working notes"
    writes: workspace
  - id: reply
    class: recording
    label: "Reply"
    inputs: [ { name: body, type: markdown, required: true } ]
    grrp: ["record", "--act", "challenge", "--relation", "repliesTo",
           "--parent", "{subject.id}", "--body", "{inputs.body}"]
    preconditions: [has-open-question]
  - id: cite-evidence
    class: bridge
    label: "Cite evidence bearing on this dispute"
    grrp: ["record", "--act", "verification", "--relation", "supports",
           "--parent", "{subject.id}", "--artefact", "{inputs.file.digest}",
           "--body", "{inputs.body}"]
    inputs:
      - { name: file, type: workspace-file, required: true }
      - { name: body, type: markdown, required: true }
```

Note the absences again: no `resolve` action (dispositions are closed; a dispute's standing changes only when a later transition changes it), no `weight`, no `strength`. **Structural edges** (`follows`/`crosses`/`cites`) get none of this machinery at all: they are facts read off `parents` and `artefacts`, have no identity of their own, take no components, take no actions, and appear in no manifest. Only *claims* — connections — are reifiable, because only claims have content to hold.

---

## 4. Versioning, extension, and travel

### 4.1 What may be extended, and by whom

| dimension / thing | extensible? | by | mechanism |
|---|---|---|---|
| `act` (8) | **never** | — | interoperability rests on it; a manifest naming a ninth act fails to load |
| `disposition` (3) | **never** | — | `unresolved` is the point; no manifest may add, remove, or alias one |
| grounds of restriction (4) | **never** | — | free invention of grounds makes withholding free |
| `target` | yes | charter | value + definition in the charter (Req 18.2); stored as `local:` until/unless bound |
| `trigger` | yes | charter | same |
| `relation` | the three named locals only, plus charter-defined `local:` values | charter | CiTO stays the binding for everything CiTO covers (C12); locals flagged, never presented as bound |
| kinds, components-instances, actions | yes | charter package or builtin | manifests, this spec |

Amendment is prospective (Req 18.4): a kind manifest at version *N+1* changes how *future* screens render; it never re-interprets records, because it never interpreted them — it lensed them.

### 4.2 A record made under a community kind, arriving at a host without the manifest

The record must read as plain protocol, and it does, because the kind contributed nothing to it. The calibration transition on disk:

```yaml
# trajectories/tq7/transitions/<id>.yaml — this is ALL that travels
id: trn:sha256:9f2a…
act: verification            # closed vocabulary — understood everywhere
target: method
relation: null
trigger: local:calibration   # retained unchanged, flagged as local (Req 16.5, vocab.py)
disposition: accepted
parents: [trn:sha256:1c44…]
prior_state: state:sha256:77b0…
posterior_state: state:sha256:e01d…
performer: key:ed25519:…
performed: 2026-08-14T09:12:00Z
artefacts:
  - { scheme: state, ref: "state:sha256:ab31…" }   # the certificate bytes, by hash
registration: { registrar: key:ed25519:…, attested: true, signature: … }
charter: { id: "charter:metrology-lab", version: "3.1" }
```

A manifest-less host: verifies the signature; renders it with the **family fallback** (generic transition node: `verification` of a `method`, trigger shown as `local:calibration — charter-defined, charter:metrology-lab@3.1`, artefact by digest); offers only the universal components and generic actions. Nothing is missing *from the record* — what is missing is a nicer tab layout and a pre-filled form. The host may fetch the charter package by the id+version the record itself carries and gain the lens; it must never rewrite the record to fit a lens it has (no normalisation — Req 16.5).

### 4.3 The manifest loader's denylist (constitutive refusals, enforced at load)

A manifest is rejected in full, with the reason, if it declares: a kind matching persons or parties (person-centric graph → C6/monitoring) · a project-level kind (C4) · any component named or shaped as attendance, presence, activity, streak, progress, importance, score, rank, weight, or count-across-trajectories (C6) · any action whose `grrp` template edits or deletes (C3) · any merge/combine action, under any name (C5) · any action setting or adding a disposition value outside the closed three · a `projection` using forms outside §1.2 · a `schedule` schema extended with people fields.

---

## 5. Composition rules

1. **Universal components** — every node kind and every edge kind, non-removable, prepended automatically: `identity`, `workspace` (the brief's premise: storage is common to all nodes *and edges*), `provenance` where the subject is a transition.
2. **Family defaults**, added unless the kind is a stricter match that already covers them:
   - *act-family*: `details`, `bearing`, `material`, `disclosure`
   - *occasion-family*: `material`, `bearing`, `schedule`
   - *material-family*: `bearing` (who cites it), digest display; external works (doi/arxiv/url) get a resolver link, no workspace upload of other people's bytes
   - *edge-family*: `details`, `endpoints`
3. **Reified-edge inheritance**: an edge kind's subject is a transition, so it inherits the full universal set *as a node* — same workspace path scheme (`nodes/<transition>/`), same provenance, same disclosure sidecar. The manifest may **add** edge-specific components; it may never remove a universal one. One subject, one component set, two renderings (drawn as an edge in the graph; opened as a node in the panel).
4. **Additivity**: resolution unions components; conflicts on `id` resolve to the more specific kind's instance. Actions never union across kinds — exactly one kind's action list is offered (the resolved one), so a community cannot *shadow* a builtin recording action with a differently-wired one at equal match specificity: builtins win ties on actions, charters win ties on components (a lens may be enriched; a recording path may not be quietly swapped).
5. **Class discipline is per-instance and static**: a component's class comes from its type, fixed in the app registry; no manifest field can move data between classes, which is what makes "does it travel?" answerable by grep.

---

**Relevant files**: `c:\Users\Micro\Desktop\relational_being_infrastructure\research\projects\Generative-Relational-Academia-Application\grrp\src\grrp\vocab.py` (closed vocabularies the denylist mirrors), `web\packages\server\src\records.ts` (the `nodeArea`/`runGrrp` seams the component classes and recording actions attach to), `notes\paper-IV-grrp-specification.md` §§16–19 (travel and charter rules §4 binds to), `plans\design-nodes-time-and-occasions.md` (the meeting/occasion precedent §3.1 encodes).