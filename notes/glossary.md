# Glossary — GRA / GRRP

Terms as the four papers fix them. Where a term also has a settled sense in an adjacent literature, the
divergence is marked. **Bold** entries are the load-bearing ones.

---

## The record

**Trajectory** — the directed graph whose vertices are **states** and whose arcs are **transitions**;
an ordered record of the transitions a shared understanding has passed through, with the acts and the
parties to them. **A trajectory is identified by the record, and its current state is *derived* from
the record, never stored alongside it.** *(P-I §2.7, P-IV Def. 2.1)*

**State** — an identified condition of a shared understanding at a point in a trajectory: the recorded
content plus the identifier under which it is addressed. **Created by a transition and never modified.**
Its *form* is deliberately unspecified — prescribing the form of a scholarly claim would be prescribing
research practice. *(P-IV Def. 5.1)*

**Transition** — **the unit of record.** A change from one identified state to another, produced by a
typed act performed by a party and **registered by a party**. *(P-I Def. 2.8, P-IV Def. 2.1)*
> Called **transition**, never *commit* — the protocol is layered over version-control systems whose
> commits appear in the same repositories, and the collision would mislead every implementer.
> *(P-I §2.7)*

**Event** — an automatically generated record that *something occurred* (a meeting was held, a comment
posted, a file changed, a permission altered). **Asserts nothing about an understanding.** Near-zero cost,
possibly large volume. Lives on the **event plane**, private to participants by default. *(P-IV Def. 2.2,
Req. 3.1)*

**Artefact (reference)** — a produced object referenced by a record: document, dataset, recording,
transcript, release. Held by substrates, not by the protocol. *(P-IV Def. 2.2)*

**Promotion** — the act by which an **event becomes a transition**: a responsible party registers it.
Candidates may be proposed by any means (including model analysis of the event plane); **a proposal
becomes a transition only when a party registers it**, and a model-originated proposal must be marked as
such. *(P-IV Req. 4.3)*

**Administrative operation** — a record concerning *the arrangement* rather than the understanding
(disclosure class changed, key rotated, redaction performed, fork declared, attribution contested).
Same envelope, **mandatory `kind` field**, no act/target/relation/disposition. Must be distinguishable
from transitions — otherwise administrative activity inflates apparent generativity, and a position
holder could act without leaving an inspectable record. *(P-IV Req. 4.6)*

**Skeleton / content** — **skeleton** = identifier, kind, parent links, state references, typed fields,
parties, signature, disclosure class and ground. **content** = the material referred to. **Stored
separately, referenced by content-derived identifier**, so removing content leaves the skeleton valid and
the signature chain intact. This is what makes redaction possible in an append-only log. *(P-IV Def. 13.1,
Req. 13.2)*

---

## The factored type — five dimensions, small closed vocabularies

*(P-I Req. 13.3, P-IV Req. 6.1. Never flatten into one enumerated list: agreement between classifiers
declines as categories rise, and deliberation over classification re-introduces capture cost.)*

**act** *(fixed, 8)* — `question` · `claim` · `challenge` · `transformation` · `decision` ·
`connection` · `verification` · `release`
**target** *(charter-extensible)* — question · assumption · hypothesis · concept · theory · method ·
path · artefact
**relation** *(bound to CiTO)* — extension · modification · replacement · refinement · generalisation ·
specialisation · transfer
**trigger** *(charter-extensible)* — reflection · literature · experiment · simulation · observation ·
discussion · objection · prior failure · automated suggestion · **entry of a new party**
**disposition** *(fixed, 3)* — `accepted` · `contested` · **`unresolved`**

> **`unresolved` is required and the vocabulary is fixed because of it.** Most objections in theoretical
> work are never resolved: they stand, and the work proceeds beside them. A record admitting only
> acceptance and rejection would be **systematically false** about the fields this protocol most
> concerns, and would exert pressure toward **fabricated closure**. *(P-IV Req. 6.3)*

**Decision** — the act that records a direction taken or abandoned **with the reason**. *A path recorded
as abandoned without a reason cannot be revisited by anyone.* **The demanding act** — the one whose
purpose for its performer is weakest, and the one on which reuse of abandoned material depends.
*(P-IV §6.2, §22.4; P-II Claim 11.3)*

**Release** — **a declaration, never a judgement.** Declares a state published at a class and records
**the objections standing unresolved against it at that moment**. Must not be presented as certifying,
validating or approving. Also the object to which a priority claim attaches where a community honours
registration. *(P-IV Def. 12.5, Req. 12.6)*

**Synthesis** — a transformation with **two or more parents from distinct branches**, producing a state
its performer **composed** from what those branches reached. **The branches it draws on continue to
exist; a synthesis is a further state, not a resolution of the divergence.** *(P-IV Def. 10.4)*

**Divergence** — two or more transitions sharing a parent and producing distinct successors. **Both
preserved; neither designated principal, default, canonical or current; no ordering over branches may be
recorded or exported.** *(P-IV Def. 10.2, Req. 10.3)*
> **Disanalogy with software forks:** in software a fork is a coordination failure to be reunified. **In
> inquiry a fork is frequently the correct outcome, and plurality is the normal shape of a healthy
> record.** *(P-I §14.4)*

**Merge** — **does not exist.** Version control merges because changes to distinct text regions compose,
a conflict can be localised, and a test decides the result. **Two revisions of a concept satisfy none of
the three.** Integration appears only as a **synthesis** or an **absorption**. *The word must appear
nowhere in the specification or the UI.* *(P-I Claim 14.1, P-IV Req. 10.5)*

---

## Parties, credit, credibility

**Party** — an entity capable of performing and registering acts, **identified by a public key**.
**Continuity of identity is required; legal identity is not.** Pseudonymous participation must be
permitted at every tier. *(P-IV Def. 14.1, Req. 14.3)*

**Registration** — the act by which a transition enters the log.
**Attestation** — **registration performed by a party other than the one who proposed the transition**,
recorded with that party's identifier and signature. *(P-I Def. 2.9, P-IV Def. 2.3, Req. 8.1)*
> **What it asserts:** that an identified party registered a transition at a time.
> **What it does not assert:** that the change was an improvement, that the claim is true, or that the
> registering party understood it. *(P-IV Claim 8.4)*
> **Never counted.** Attestation depth is a scalar over trajectories and would be farmed by reciprocal
> registration. *(P-IV Req. 8.5)*

**Distributed attestation** — the design's answer to fabrication. **Credibility follows from the
distribution of registrations across parties who did not coordinate, and from no property of the
record's content, length or detail.** *This is why the design is a protocol and not a platform: a
platform operator is party to every entry and cannot supply the independence.* *(P-I Req. 12.2, Claim 12.3)*

**Attribution** — the recording of a party's part in an act, with a **CRediT** role. **Attaches to an
act, not to a finished work** — *a contributor statement says a person contributed to a paper; this
record says which change in the content of a claim a person produced.* *(P-IV Req. 9.1)*

**Absorption** — the taking of content from a state in one trajectory into a transition in another. The
**absorption link** records the state absorbed from, **the party who produced it**, and the transition
that took it. *(P-IV Def. 9.2, Req. 9.3)*
> **No veto (Req. 9.4).** An absorption link confers **attribution and no power to prevent, condition or
> reverse use** — the moral-rights construction, chosen to avoid the anticommons. **A party who does not
> wish their state absorbed has one instrument: its disclosure class.**

**Absorption test** — the criterion separating a **generative** arrangement from a **competitive** one:
*examine the record of the work that proceeded and look for transitions whose content originated in work
that was **not selected**, with attribution.* **Where such transitions are absent, the arrangement is
competitive whatever its constitution states.** Applied by readers, **never computed as a score.**
*(P-II Def. 8.1, Req. 8.2, Claim 8.4)*

**Competitive / generative arrangement** — turns entirely on **what becomes of unselected work**, not on
openness of entry, number of participants, or manner of decision. *An open arrangement discarding losing
proposals is competitive; a closed arrangement that takes up and credits a rejected proposal's method is
generative.* *(P-II Def. 8.1)*

**Encounter** — a transition performed by **a party who has performed no prior act in the trajectory**,
with a trigger identifying the occasion. **No new primitive** — the trigger dimension covers it.
*(P-I Def. 18.1)*
> Every claim about encounters is **envisagement** and must carry the counter-evidence (Irving et al.
> 2020: occupants of a building designed for serendipitous collaboration developed strategies to avoid
> it). What may be claimed is a lowered **cost of preparation** — never an increased frequency of
> encounter. *(P-I Req. 3.2, P-II Claim 15.4)*

---

## Disclosure

**Disclosure class** — a value attached to a **record** (not a repository, project or trajectory)
governing to whom it may be disclosed. **Ordered by inclusion. Enforced by the implementation, opaque to
the protocol, interpreted by the charter.** *(P-III Def. 2.1, P-IV Def. 11.1, Req. 11.5)*

**Ground** — the **declared reason** for restricting disclosure. **A property of a restriction, not of a
record** — the same content may be restricted on different grounds in different arrangements, with
different consequences. **A closed set of four.** *(P-III Def. 2.2, Req. 2.5)*

**Residue** — **what remains disclosable at the widest class while a restriction on that ground is in
force.** *A ground with an empty residue licenses total silence.* **The residue requirement is the
operative rule of the whole account** — without it every ground collapses into silence with a
justification attached. *(P-III Def. 2.3, Req. 2.6)*

| Ground | Condition | Object restricted | Residue | Named failure |
|---|---|---|---|---|
| **rivalry** | a resource admits limited simultaneous use | **access to the resource** | **the trajectory in full** | a restriction on access converted into a restriction on knowledge |
| **hazard** | propagation of the content creates risk | the **propagable content of a method** | existence, questions, decisions, interpretations, non-conveying results | widest restriction on the strongest justification, **unfalsifiable from outside** |
| **exploratory vulnerability** | exposure at this stage suppresses or distorts the work | **the timing of exposure** | **everything, at the scheduled time** | postponement converted into permanent withholding |
| **appropriability** | funding requires excludability | content whose disclosure destroys excludability | existence, questions, decisions, **negative results** | **rent-seeking secrecy** |

**Irreducible** — rivalry restricts a *resource*; the others restrict *content*. Hazard restricts what a
*reader* could do; appropriability what a *competitor* could sell. Vulnerability restricts a *time*; the
others a *set of parties*. *(P-III Claim 7.1)*
**Composition** — where several grounds obtain, each is declared separately and **the residue disclosed
is the intersection.** Declaring more grounds is **not free** — each is an assertion that can be found
false. *(P-III Req. 7.2)*
**Termini** — vulnerability ends **on a recorded schedule**; rivalry when the resource is uncontended
(unenforced); appropriability when the funding purpose is served (**known to the declaring party
alone**); **hazard does not end.** *A community wishing its record to open over time must prefer the
ground that ends.* *(P-III Claim 7.4)*

**Monotone disclosure** — **disclosure may widen and must not narrow.** No `unpublish` operation exists.
*Ground: a party who has read a record retains what they read, so an apparent withdrawal misdescribes to
participants a state of affairs obtaining outside the system.* A schedule may be **shortened, never
extended or cancelled**; any attempt must be recorded. *(P-III Claim 5.1, P-IV Req. 12.1, 12.4)*

**Redaction** — removal of **content** while the **skeleton remains**. The redacted record continues to
assert that a transition occurred, by whom, of what type, at what graph position. **The record of the
redaction must not be removed, the graph must not change, and redacted content must not be represented as
never having existed.** *(P-IV Def. 13.3, Req. 13.4–13.5)*

**Sealed registration** — publication of a **content-derived identifier** of a state, plus registering
party and time, **with the content disclosed to nobody**. Asserts that the party held that content at
that time. **Available at every class, including disclosure-to-nobody.** *(P-I Def. 19.1, P-IV Def. 15.1)*
> **A timestamp is not priority.** It evidences possession, not understanding. **It generates nothing
> while sealed** — no objection, no connection, no encounter; it purchases *the possibility of later
> opening*, not the benefits of early opening. It adjudicates nothing against independent arrival. And its
> time is evidence only if **anchored in a medium the implementation does not control.**
> *(P-IV Req. 15.6, 15.7, §15.5)*

**Conditional / structured access** — supplying a capability **without transferring the artefact that
confers it**, under conditions the supplier enforces. Applied here: a party is **admitted to a restricted
class** under a charter's assurance requirements, **with the admission and its ground recorded.** The
mechanism that makes work under the hazard ground possible at all. *(P-III Claim 4.3)*

---

## Structure and governance

**The four levels** *(P-I Def. 2.1)* — **L0 external law** (described, never encoded; reaches the design
only *negatively*, through structural incapacity) · **L1 operating norms** (the charter: which classes
exist, who belongs, retention, consent, conduct, assurance, extended vocabularies) · **L2 protocol** (the
capacity: state model, act vocabulary, registration, attribution, parent links, classes as opaque enforced
values, conformance) · **L3 application** (interfaces, capture assistants, search, matching, summarisation,
**assessment of content** — replaceable, and the protocol is implementable with none of it).
> **The protocol carries the capacity; the normative level carries the content.** *(Req. 2.2)*

**Operating charter** — an identified, **versioned** document a community adopts, stating its rules.
**The protocol references it by identifier and interprets nothing in it.** **The charter is where
everything contested lives.** A record must carry the charter identifier and version that governed it.
Amendments are **prospective only**. *(P-IV Def. 18.1, Req. 18.2–18.4)*

**Description language vs. interaction protocol** — a **description language** fixes a vocabulary for
recording what occurred and imposes no condition on what may occur (PROV, CRediT, CiTO, Web Annotation,
RO-Crate are all of this kind). An **interaction protocol** fixes **which acts are admissible, what each
does to a shared state, which party may perform each, and what conformance requires.** *This distinction
is where the word "protocol" in the title is meant literally.* *(P-I Def. 7.1, Claim 7.2)*

**Protocol vs. plan** — a **plan** specifies outcomes and the steps to them. A **protocol** specifies
admissible acts and their effect on a shared state, **and leaves every participant's trajectory
undetermined.** Relation = grammar to sentences. *Any drift into prescribing what participants should
record, conclude or value is an error to be corrected, not a position to defend.* *(P-I Def. 2.3)*

**Functional vs. structural position** — a position is **functional** where constituted by acts the
arrangement requires, recorded and attributable, with occupancy depending on continuing to perform them.
It is **structural** where occupancy confers persistent standing, or where others' capacity to act depends
on the holder's permission. *(P-I Def. 15.1)*
**Admissibility of authority** — two joint conditions: **(i)** the constituting acts are recorded and
attributable and visible; **(ii)** participants **retain the capacity to proceed without the holder's
permission**. *Visibility without exit produces documented autocracy; exit without visibility leaves
participants unable to judge whether to leave.* *(P-I Req. 15.2)*
> **Four positions the design generates** (not imports): **registrar** · **trajectory steward** ·
> **holder of disclosure authority** · **custodian of the specification.**

**Portability** *(five joint properties, P-I Req. 16.2)* — the complete record is **(1)** obtainable by
any participant **without permission** · **(2)** in a **self-describing format readable without the
producing software** · **(3)** carries **identifiers that stay resolvable when held elsewhere** ·
**(4)** **licensed** to permit continuation · **(5)** **continuable under the same protocol by an
implementation the original operator does not control.**
> **Property 5 is what distinguishes portability from export.** A data dump satisfies 1–4 and leaves
> departing participants with an archive.
> **Portability is the bound on the authority of every position** — the cost of exit, not any rule
> addressed to the holder. *(Claim 16.1)* But it **secures the record, not the participants, not the
> resources, and not the standing** — and it bounds the **restricting** authority weakly, because a
> departing party cannot take what they were never shown. *(P-III Claim 11.4)*

**Propagation** — the movement of **transitions** between trajectories (**lateral**) and between
independent implementations (**inter-implementation**). **Dissemination of finished artefacts is excluded
from the term.** *(P-I Def. 2.11, P-IV Def. 16.1)*
**Continuation** — obtaining the complete record without permission and continuing it elsewhere, with
appended transitions **referencing the obtained ones as parents so the result is one graph and not two.**
*(P-IV Req. 16.4)*
**Exchange minimum** — the only things two implementations must agree on: record structure, act and
disposition vocabularies, bound-vocabulary identifiers and versions, **content-derived identifier
construction**, and **signature scheme**. *The last two cannot be relaxed.* *(P-IV Req. 16.2)*

**Conformance tiers** *(cumulative)* — **personal** (one participant; three acts; **utility and no
evidential weight**) → **group** (attestation, roles, absorption, classes; **credibility begins**) →
**open** (propagation, distributed custody, deposit, charter reference; **exchange and stranger entry**).
*(P-IV Def. 20.1)*

**Open register** — the set of states whose disposition is `unresolved`, made available at each disclosure
class. **This is the entry path**: a party holding no prior position may reference such a state in a
`challenge`, `connection` or `verification`, decided on the act itself. *(P-I Req. 17.2, P-IV Req. 6.5)*

---

## Concepts from the argument

**Separating condition** — an artefact carries evidence of its producer's capacity **only while producing
it is more costly for a lower-capacity producer**, by a margin making it worthwhile for one and
unattractive for the other (after Spence 1973). **The evidence was never in the object; it was in the
difference between what the object cost different producers.** *(P-I Def. 11.1)*
> A **uniform fall in production cost** weakens the evidential function while the artefact, the practice
> and the systems reading it all remain in place — **and the failure is invisible from inside the
> practice.** *(Prop. 11.2)*

**Capture cost** — the documented cause of the non-adoption of every rationale-capture system since 1970:
**the work of recording falls on the party who gains least from the record, at the moment they can least
bear it, in a form that serves a different party later** (Grudin 1988). **The representational problem was
solved; this is what defeated it.** *(P-I Claim 8.1)*

**Byproduct principle (R1)** — every act the protocol defines is one a participant performs **for a reason
of their own**, with the record falling out of its performance. **An act existing so that a record should
exist will not be performed.** *(P-I Req. 8.2, P-IV Req. 4.2, test at Req. 20.6)*

**Articulable fraction** — that part of what a trajectory's participants held which they were able to put
into the record. **Its complement transmits, if at all, by working alongside them, and no property of the
record's design recovers it** (Collins 1974/2010; MacKenzie & Spinardi 1995). *(P-I Def. 20.1)*

**The omitted component** — what a finished artefact does not contain: approaches attempted and abandoned,
the reasons, the constraints discovered, the parameters that mattered, the practical technique.
> **It carries the value in reuse, the evidential force, AND the hazard — at once.**
> **No design publishes the trajectory minus its dangerous parts and retains the benefit, because the
> parts are the same parts.** All three scale together with the articulable fraction, and **no design
> alters the ratio.**
> *This is why the account is a typology of grounds separating **parties** rather than a filtering rule
> separating **content** — and why the **residue**, lying outside the component, is the only part of the
> design that gains something without giving something up.*
> *(P-I Prop. 20.2; P-III Def. 9.1, Prop. 9.2, Claims 9.3–9.5)*

**Generativity** — **the capacity of a relation to produce states that neither party held.** Distinguished
from the developmental-psychology sense and from Zittrain's platform sense (the capacity of a *technical
system* to admit contributions). *(P-I §3.2)*
> **Trajectory ≠ generativity (P-I Def. 10.2, Prop. 10.3).** A trajectory is the recorded sequence — an
> object that can be inspected. Generativity is a **capacity**, of which the trajectory is *one
> realisation among those that were possible*. **Two trajectories may coincide entirely in recorded
> appearance while differing entirely in the generativity of the relations that produced them.**
> *This is the deep ground of the no-scalar rule: a quantity computed over a trajectory measures a
> realisation, not a capacity, and that is an error no amount of data corrects.*

**No scalar (R10)** — the protocol defines **no scalar quantity over participants or over trajectories,
and admits no total order over either.** Local, two-valued acceptance conditions replace indicators
throughout. **Counts of records within a single trajectory, presented without comparison across
participants or trajectories, do not violate it.** *(P-I Req. 2.6, P-IV Req. 20.4)*
> Cost stated openly: cannot report that a project is going well, cannot rank contributors for a
> committee, cannot summarise a trajectory's standing in a number.

**Positional good** — a good whose value consists in the holder's **rank** among others, so the aggregate
available is **fixed by construction** and increases in supply do not increase it (Hirsch 1976). **Standing
is positional.** *(P-II Def. 2.2, Claim 6.1)*
> Therefore: **attribution redistributes recognition; it does not create it** — and parties who benefit
> from the present invisibility of others' contributions are made worse off, **which predicts resistance.**
> **No claim that the arrangement reduces competition, dissolves hierarchy, or increases recognition may
> stand anywhere in the series.** *(Claim 6.2)*

**Subtractable goods** — the four things a commons dilemma actually attaches to here: **review/assessment
capacity** (the one the design most strains) · **maintainer labour** · **the instrument** · **community
trust**. *(P-II Claim 3.3)* **Knowledge itself is non-rival — the tragedy of the commons has no object in
it, and its failure mode is underprovision, not overuse.** *(Claims 3.1–3.2)*

**Private-benefit sufficiency** — an arrangement is adoptable **only where its minimal form is worth
adopting by a single participant with no other participants present.** *An arrangement whose benefits
appear only at scale is never adopted, since no party is ever in a position to obtain them.*
*(P-II Req. 11.4; = R15)*

**Dominance argument** — in an environment rewarding output rate, a group adopting an arrangement with
**any net cost** is disadvantaged **irrespective of its epistemic merits**, and sustained, adopting groups
are **selected against**. *Two escapes only: net private benefit, and insulation from output-rate
selection.* *(P-II Claim 12.1)*

**Compatibility (R16)** — a participant must be able to obtain, **from a conforming record and without
additional work**, an artefact of the kind the incumbent reward system accepts. Mechanism: **emission on
release** — the state, its chain, contributors with roles, absorption links with attributions, and the
objections standing at release. *(P-II Req. 14.1, P-IV Req. 12.7)*
> **It postpones the conflict with incumbent interests and does not remove it — and the conflict returns
> at exactly the point at which the arrangement begins to succeed.** *(Claim 14.4)*

**Minimum viable adopting unit** — the smallest set of parties for which benefits exceed costs **without
participation by anyone outside the set**. **Group tier: two parties who register each other's
transitions. Open tier: one community with an implementation and a charter.** *A design whose minimum unit
was a discipline requires an agreement nobody can broker; a design whose minimum unit is a seminar requires
a decision two people can take on a Tuesday.* *(P-II Def. 13.3, Claim 13.4)*

**Sparsity / plurality** — of a selection: **sparsity** = the interval between selection events measured
against the interval over which a line of work develops; **plurality** = the number of applied criteria
**that cannot be combined into a single ordering**. **Plurality is not preserved under frequent
application, so sparsity is a *condition* of plurality.** Charter parameters, not protocol parameters.
*(P-II Def. 10.2, Claims 10.3–10.5)*

**Dissipation** — the aggregate effort entrants expend in a contest **in excess of what the selection
required**. Opening a selection to more entrants **increases** it, disproportionately burdening those for
whom preparation is a larger share of available time. *(P-II Def. 7.1, Claim 7.2)*

---

## Modal conventions used throughout the series

**Analysis** — states what is the case, supported by evidence or argument.
**Design** — states what a specification requires, supported by derivation from a requirement.
**Envisagement** — states what would follow in use; **supported by nothing available at present.**
> No envisagement sentence appears in a design section, and every envisaged consequence is stated
> conditionally with its conditions named. *(P-I Convention 2.4)*

**Formal / empirical / conjecture** *(Paper II's marking, Req. 2.3)* — **formal** follows from stated
assumptions; **empirical** is supported by cited studies with population and strength stated;
**conjecture** is neither, and is marked wherever it appears.

**Standard for a solution** *(Paper II Req. 2.4)* — a difficulty is **addressed** only where there is
**a mechanism**, **an identified party who bears its cost**, and **a stated condition under which the
mechanism fails**. A mechanism without an identified cost-bearer is recorded as **unaddressed**.

---

Sources: [Paper I](paper-I-design-and-requirements.md) · [Paper II](paper-II-incentives-and-adoption.md) ·
[Paper III](paper-III-grounds-of-restriction.md) · [Paper IV](paper-IV-grrp-specification.md)
