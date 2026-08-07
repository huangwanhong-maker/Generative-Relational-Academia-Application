# Gaps between the repository and the papers

Written after reading all four papers. Each item names **what the repo says**, **what the papers
require**, and **the action**. Ordered by how much damage the divergence does.

---

## A. Conflicts that would make the repo non-conformant or misleading

### A1. "GRA Commit" is the wrong word — and it is the exact word the papers refuse

**Repo:** [README.md](../README.md) has a section headed *"GRA Commit Concept"*, and
the retired `plans/implementation_plan.md` used "Commit" throughout (Stage 1
"Semantic Commit System", "Create GRA commits", "commit types").

**Papers:** *"the epistemic unit is called a **transition** throughout, in place of a **commit**, since
the protocol is layered over version-control systems whose commits appear in the same repositories and
**the collision would mislead every implementer**."* (Paper I §2.7)

**Action:** rename everywhere → **transition**. ✅ Done in the README, the new plan, and the tool.

---

### A2. Flat "commit types" instead of the five-dimension factorisation

**Repo:** `implementation_plan.md` Stage 1 lists a single flat enumeration — Progress · Failure · New
problem · New idea · New question · Literature integration · Objection · Response · Synthesis.

**Papers:** *"A transition is typed along **five independent dimensions** with small closed
vocabularies, in place of a single enumerated list. An implementation **must not** define a single
enumerated type combining these dimensions."* (Paper I Req. 13.3; Paper IV Req. 6.1) — because
inter-rater agreement declines as categories rise, and deliberation over classification re-introduces
capture cost.

Also: the flat list has **no `unresolved` disposition**, which Paper IV Req. 6.3 makes mandatory and
non-extensible; without it *"a record admitting only acceptance and rejection would be systematically
false about the fields this protocol most concerns, and would exert pressure toward fabricated
closure."* And "Progress" is not an act at all.

**Action:** replace with `act × target × relation × trigger × disposition` (see
[glossary.md](glossary.md)). ✅ Done in the README, the new plan, and the tool.

---

### A3. Roadmap items that are forbidden scalars

**Repo:** `implementation_plan.md` Stage 4 — *"Generate progress reports"*; Stage 5 — *"Trajectory risk
analysis"*, *"Research obstacle detection"*, *"Similar trajectory search"*, *"Similar failure
discovery"*.

**Papers:** **R10 / Req. 20.4** — an implementation **fails conformance** where it computes, stores,
displays or exports **any total order or numeric measure over participants or over trajectories**,
including counts of transitions, counts of attestations, contribution shares, activity indices and
derived scores. Paper II Claim 8.4 adds that even an *absorption* score violates it. And Paper I §22.2:
R10 costs the arrangement *"the ability to report that a project is going well"* — that is precisely
what "progress report" and "trajectory risk analysis" name.

**Action:**
- Anything that ranks, scores, or reports "health/progress/risk" across trajectories or participants is
  **out of the protocol entirely**. It may exist as an **L3 application**, clearly labelled as outside
  conformance, and the papers note the party building it *"owns the consequences"*.
- Within-trajectory counts shown **without cross-trajectory or cross-participant comparison are
  permitted** (Req. 20.4, second sentence). A "what I ruled out this month" view is fine; a dashboard
  number is not.
- **Similar-trajectory / cross-field matching must additionally be removed from any adoption argument**
  (Paper II Claim 13.5): it is not decomposable by tier, returns nothing to any adopting party, and is
  "a late property of an adopted arrangement". Paper I Claim 18.3 says the same and adds that the
  matching problem itself is **unsolved and belongs at L3**.

---

### A4. The staging is inverted — the adoption-critical features are scheduled last

**Repo:** `implementation_plan.md` puts *"Generate paper outline from trajectory"* at Stage 4 and
integration/collaboration at Stages 2–3; there is no personal-tier ship point.

**Papers:** **R15 + Paper II Req. 11.4** — *"An arrangement is adoptable only where its minimal form is
worth adopting by a single participant with no other participants present."* And **R16 / Req. 12.7** —
**emission of a citable document from a release** is *the* mechanism that makes adoption possible under
the dominance argument (Paper II §14). The GRRP plan gets this right: **"M1 — Personal tier. Ship
here."**

**Action:** re-order so the personal tier (three acts + append-only log + derived views + `open`
register + **`export` on release**) is the first shippable unit, matching
[plans/implementation-plan.md](../plans/implementation-plan.md). ✅ Reflected in the README and in the
new single plan, whose M1 is marked as the ship point.

---

### A5. The two implementation plans disagreed with each other — *resolved*

**Repo:** `plans/implementation_plan.md` (Stages 0–7, commit-based, platform-flavoured: "Discussion
System", "Feedback System", "AI research assistant") and `plans/GRRP-implementation-plan.md` (M0–M5,
transition-based, CLI, no server, no account, no network).

They are not two views of one plan; they encode **different designs**. The GRRP plan is the one derived
from the specification.

**Action:** ✅ **`plans/implementation_plan.md` has been retired** (removed; recoverable from git
history), and `plans/GRRP-implementation-plan.md` has been folded into a single
[plans/implementation-plan.md](../plans/implementation-plan.md). The specification governs where that
plan and the papers differ.

---

## B. Claims the papers forbid

The papers spend a lot of length forbidding specific sentences. These are the ones most likely to
reappear in a README, a grant application, or a website.

| Do not write | Why | Cite |
|---|---|---|
| "makes scholarship less competitive" / "democratises recognition" / "dissolves hierarchy" | recognition is **positional**; attribution redistributes and does not create it. *"any passage implying otherwise is an error to be corrected"* | P-II Claim 6.2 |
| "GRA will increase serendipitous encounters" | no evidence; the best qualitative study reports **avoidance**. Only *cost of preparation* may be claimed | P-I Req. 3.2; P-II Claim 15.4 |
| "adopt this because it benefits scholarship collectively" | *"available to no individual party, and its repetition is the characteristic error of proposals in this field"* | P-II Claim 12.4 |
| "a trajectory record proves the work happened" | attestation asserts **registration at a time**, not truth, improvement, or understanding; **collusion is not eliminated** | P-IV Claim 8.4, §23.1 |
| "personal-tier records are verified / corroborated" | the personal tier carries **utility and no evidential weight**; every transition must be **marked unattested** | P-IV Req. 20.3 |
| "merge two branches" | no merge operation exists; the word must not appear | P-I Claim 14.1; P-IV Req. 10.5 |
| "restrict the instrument, open the reasoning" (as general policy) | correct under **rivalry**, **exactly wrong under hazard** — the reasoning is where the hazard lives | P-III Claim 4.1 |
| "publish the trajectory minus the dangerous parts" | value in reuse, evidential force and hazard are **the same component** | P-I Prop. 20.2; P-III Claim 9.3 |
| "sealed registration establishes priority" | it records that a party held a content at a time. **A timestamp is not priority** | P-IV Req. 15.7 |
| "the record makes a research process available" | a record carries **the articulable fraction**; capability does not transfer | P-I Claim 10.1, Def. 20.1 |

---

## C. Things the papers require that are missing from the repo entirely

1. **A declaration of interest.** Paper I §2.8 and Paper III Claim 11.6 both bind the author's society:
   *"the requirements imposed on a custodian apply to that society without exception, including that the
   specification be forkable and that stewardship of the specification be separated from operation of any
   implementation."* Paper IV Req. 19.4 makes it normative. **The repo, operated by Serendip Commons
   Society, should state this in the README.** ✅ Added.

2. **The four "findings that would show the specification inadequate"** (Paper IV §24.4) are the
   project's own evaluation plan and have no home in the repo. ✅ Added to README as an explicit
   failure-conditions section.

3. **The four unaddressed difficulties** (Paper II §17.2): assessment congestion, maintainer labour,
   regressive overhead incidence, recognition of attributed contribution. These are *known holes*, not
   oversights. ✅ Added to README.

4. **Licence — resolved: MIT.** ✅ Paper I Req. 16.2 property (4) requires the record to be *"licensed
   so that continuation elsewhere is permitted"*, and Paper IV Req. 19.4 requires the specification to be
   licensed so **any party may fork it**. CC BY-**NC** satisfied neither, and was not a software licence
   for `grrp` either. MIT discharges all three. The four PDFs still carry an embedded CC BY-NC notice and
   remain under it until their author revises them.

5. **An `open` register / entry-path affordance** is required by Req. 6.5 and is the answer to the
   bootstrap failure (Paper I §17). The GRRP plan has `grrp open` and calls it *"the entry path"*. Good.
   It should not be described anywhere as a nice-to-have.

---

## D. Implementation traps the papers name explicitly

Worth pinning here because each is described as *the* likely error.

- **Signature coverage** — *"Getting this wrong makes ordinary operation invalidate signatures — the
  single most likely implementation error."* Spec §8.3 says the signature covers the disclosure class;
  deployment §21.5 says commit signatures therefore break on scheduled release, and the workable
  arrangement is to hold the class **in a separate file the signature does not cover**. Follow §21.5.
- **A stored authoritative current state** — *"the requirement most often violated in practice, since a
  stored current state is convenient and fast. Where a stored snapshot is authoritative … every claim
  the protocol makes about credibility fails at once."* Caches must be reconstructible and marked
  derived. (Req. 4.4)
- **Unattended/default registration** — *"a default that registers unattended proposals violates the
  requirement, because the record's credibility rests on registration meaning something."* (Req. 4.3)
- **Exporting or indexing the event plane** — *"the failure with the largest consequence for
  participants and the one an implementer is most likely to introduce while improving a feature."*
  (Req. 3.1, §23.4)
- **Disclosure by inference** — revealing a record's existence through a gap, an identifier sequence, or
  the shape of a derived view. *"A genuine implementation hazard and easy to introduce accidentally."*
  (§11.4, §23.3)
- **Reconstruction of redacted content from its content-derived identifier** where the content is short
  and its space small → **apply a per-record secret before computing the identifier**, a decision that
  must be made **in advance**. (§13.5, §23.3)
- **Normalising received records** — invalidates their signatures and destroys the property that makes
  propagation worth having. (Req. 16.5)
- **Per-repository rather than per-record disclosure** — the git deployment *approximates and does not
  meet* Req. 11.5; class changes require **moving** a record, and the movement must be recorded as an
  administrative operation. (§21.5)

---

## E. Status of the repo's own actions

| Item | Status |
|---|---|
| Notes folder with per-paper notes + glossary | ✅ this folder |
| README rewritten against the papers | ✅ |
| Both old plans folded into one [plans/implementation-plan.md](../plans/implementation-plan.md) | ✅ |
| `grrp` reference implementation, M0 + M1 | ✅ [grrp/](../grrp/) — 36 tests passing, 3 skipped and named for M2–M4 |
| Licence settled as **MIT** — discharges Req. 19.4 (forkable specification) and Req. 16.2(4) (continuable record) | ✅ |

---

## F. Decisions taken while building M0/M1, and why

These touch the hard constraints, so they are recorded rather than buried in the code.

1. **Disclosure lives in a sidecar (`disclosure/<id>.yaml`), not inline in the transition file.**
   The illustrative skeleton shows it inline. Keeping it there forces a choice between two rules that
   both have to hold — *any edit under `transitions/` is detected* and *changing a class invalidates
   nothing*. The sidecar lets both stay strict, and it is what the specification's own git deployment
   (§21.5) recommends for the same reason. **Touches C3, C7, C8.**

2. **The identifier excludes `registration`; the signature (M3) will cover `{id, registrar, time}`.**
   Registrar cannot be inside the identifier, because at the group tier a proposal is registered by a
   *different* party later, and the identifier would change under its own children. **The cost, stated
   plainly: at the personal tier, where nothing is signed, editing the `registration` block is not
   detectable by `grrp check`.** Every covered field is. Acceptable only because the personal tier
   carries no evidential weight, and it closes at M3. **Touches C2, C3.**

3. **A keypair is generated at `init`, three milestones before anything is signed**, so that party
   identifiers recorded from the first day stay valid when signing arrives. The private key is written
   unencrypted; a passphrase belongs with signatures, not before them.

4. **`--abandon` is `cito:retracts`, not a new field.** The design names an abandonment relation that
   CiTO has a genuine counterpart for. Three relations it names have none (`generalises`,
   `specialises`, `transfers`); those are `local:` values, flagged as local, and need a charter.
   **Touches C12.**

5. **A challenge is answered by the graph, not by an edit.** A `transformation` or `decision` naming
   the challenge among its parents is what takes it off the open register. Nothing is rewritten.
   **Touches C3.**

6. **The opening question is a state and not a position.** It anchors the first claim (so even the
   first transition references an identified prior state), it stays on the open register until
   something answers it, and it is not a candidate for "the current state". **Touches C4.**

7. **Transitions are committed to git automatically when inside a work tree**, and only the paths
   `grrp` wrote — a researcher's tree is usually dirty, and committing anything else would be taking a
   decision that is not the tool's. `check` and every read command work on the files alone.

8. **Ordering follows the graph, not the clock.** Two transitions recorded in the same second are
   listed parents-first; recorded times only break ties among transitions with no path between them.

