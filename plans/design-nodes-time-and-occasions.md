# Design note — node panels, per-node files, calendar, meetings

Written before building, at the point where four proposals arrived at once and
three of them touch a constraint. Nothing here is implemented yet.

The short version: **all four are buildable, none needs a new vocabulary, and
two of them have a version that would quietly break the design.** The
difference is worth writing down before it gets decided by whichever screen was
easiest to draw.

---

## 1. The node panel — safe, and the dead space is already there

Clicking a node opens a modal today. That is wrong for something you want to
keep open while you read the graph. A bottom panel that fills on selection, and
stays, is better; it also uses the space below the drawing that is currently
empty.

Tabs inside the panel:

| tab | what it holds |
|---|---|
| **Details** | act, target, relation, trigger, disposition; performer; whether it is attested and by whom; the identifier, in full and copyable |
| **Material** | the artefacts this node cites, by hash — see §2 |
| **Bearing** | what it follows, what follows from it, and what it crosses to under other questions |
| **Provenance** | contributions (CRediT), absorption, and the registration signature |

No constraint touches this. It is presentation of fields that already exist.

One rule: **the panel shows what is in the record, and nothing computed.** No
"influence", no "downstream count", no "centrality". A node with many edges is
not more important; it is a node with many edges.

---

## 2. Per-node files: nodes **cite**, they do not **own**

The request was a small file system per node. The honest version is close but
not the same, and the difference is C3.

A transition is never edited (C3, append-only). If a node owned a mutable
folder, the node would mean something different tomorrow than it meant when it
was signed, and the signature would still verify — which is worse than it
failing, because nothing would tell you.

So:

- Material lives in the **project's** file store.
- A transition **cites** material by the hash of its bytes, through the
  `artefacts` field the skeleton already carries.
- The node panel shows *the material this node cites*. That reads as a per-node
  file list and is true.
- Adding material to a node after the fact is **a new transition** citing it —
  ordinarily a `connection`. That is what append-only means in practice.

Two changes worth making to the project file store:

- **Allow folders.** `files/` is flat today and rejects `/` in a name. Nested
  paths are fine as long as traversal is still refused; the guard becomes
  per-segment instead of whole-name.
- **Keep showing the digest.** It is the only thing that makes a citation
  possible, and it is what a reader elsewhere checks.

---

## 3. Calendar — and the version of it that is forbidden

There is a legitimate calendar here and an illegitimate one, and they look
alike until you ask what is being plotted.

### Forbidden

A contribution graph. Activity per day, per person, per project. This is C6
without disguise: a quantity over participants, and the one every forge has
trained people to read as worth. It would also be the most-copied screen in the
product, so it is worth naming now: **there will be no activity heatmap, no
streak, no per-person timeline.**

### Legitimate, and already in the record

The record already contains dated commitments that nobody can currently see:

- **Scheduled disclosure.** `release_at` on a restriction. The protocol allows
  a schedule only under *exploratory vulnerability*, and `grrp disclose`
  refuses to extend one — a schedule may be shortened, never lengthened, and a
  refused extension is itself recorded. A calendar of these is a calendar of
  promises the record is holding you to. That is worth showing.
- **Embargo expiry** under the other grounds, where one was stated.
- **A chronology of one project.** `performed` is on every transition. Shown
  within a project, in order, without comparison to another project — the same
  rule that makes a per-trajectory count permissible.

So: **a calendar of commitments and chronology, never of activity.** If the
question a screen answers is "how much has this person done", it does not get
built.

---

## 4. Meetings — where the real trap is

A meeting node that "associates with any node it wants" is easy to build and is
one short step from the thing this project exists to refuse.

`actions.initialise` already says it, about the local event plane:

> A complete log of who attended, who commented and whose files changed is a
> monitoring record by construction, and it is the failure with the largest
> consequence for participants.

That is why `.grrp/events/` is gitignored and never exported. A meeting node
carrying attendance, exported with the record, is that log — rebuilt on the
front of the system instead of the back, and portable.

### What a meeting is, in this model

A meeting is an **occasion**. Occasions enter the record through what they
produced, and the protocol already carries every part:

| the meeting | in the record |
|---|---|
| that it happened, and what kind of occasion it was | `trigger: discussion` on each transition that came out of it |
| the meeting itself, as one shared node | its minutes as an **artefact**, cited by every transition arising from it — same hash, so one node, many edges |
| who did what in it | `contributions`, bound to CRediT — a role in an act, not a presence at an event |
| what came out of it | the transitions themselves: a decision, a challenge, a changed position |

That gives exactly "one meeting node connected to everything it touched",
without a new record type and without an attendance list.

### The case it does not cover, and what to do about it

A meeting that produced nothing recorded. Under C1 — byproduct only — that is
not a record entry, and writing one is recording for the record's sake, which
is the adoption failure Paper II predicts. It is a **calendar** entry.

So the split is:

- **Calendar**: meetings scheduled and held. Local, not exported, not part of
  any bundle. It may live in the event plane, where this kind of thing already
  belongs.
- **Record**: what the meeting changed. Artefact + trigger + contributions.

A meeting becomes visible in the graph exactly when it changed something. If
that feels like it is losing information, the information it is losing is
attendance, and losing it is the point.

---

## 5. What is actually missing, ranked

All four proposals are **views over a record the browser still cannot write
to**. That should be said plainly before any of them is built.

1. **Recording acts from the page.** claim, challenge, transform, decide,
   verify. Until this exists the site is a viewer with a good drawing.
2. **Attestation.** Two accounts exist; nothing lets one register the other's
   act. C2 is the entire credibility mechanism and it is unreachable from the
   interface. This is the one that makes the system mean anything.
3. Node panel (§1) — cheap, and improves everything above.
4. Per-node material (§2) — small, once §1 exists.
5. Calendar of commitments (§3) — needs `disclose` to be reachable first, or it
   has nothing to plot.
6. Meetings (§4) — is mostly §2 plus a workflow, once §2 is there.

Suggested order: **1, 2, 3, 4, then 5 and 6 together.**

---

## Decisions this note is asking for

- Per-node files: **cite, not own**. Confirmed by C3, unless there is an
  argument against.
- Calendar: **commitments and chronology only**. No activity view, ever.
- Meetings: **occasion + artefact + contributions**, with scheduling in the
  local plane and out of every bundle. Not a new record type.
- Build order: acts and attestation before any further views.
