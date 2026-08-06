# Notes — Paper I: *Designing Generative Relational Academic Infrastructure*

**Subtitle:** A Protocol Framework for Collaborative Knowledge Evolution and Propagation
**Author:** Wanhong Huang (huangwanhong@serendip.ngo) · working draft, 2026 · CC BY-NC 4.0
**Length:** 76 pp, 26 sections. Source: [papers/GRA-paper-I-...pdf](../papers/GRA-paper-I-Designing-Generative-Relational-Academic-Infrastructure.pdf)

**Role in the series:** the *design and standardisation* paper. States the problem, concedes prior
art, derives **16 requirements**, sketches the architecture. Does **not** specify the protocol
(→ Paper IV) and reports **no implementation**.

---

## 1. The one-paragraph argument

Scholarly communication transmits finished artefacts and discards the *trajectory* that produced
them. Two developments make that discard worth revisiting. (a) **Evidence:** an artefact carried
information about its producer's capacity only because producing it was costly *in a way that
discriminated between producers*; when production cost collapses for everyone at once, the
discrimination is lost while the artefact and the systems reading it stay in place. (b) **Reuse:**
the omitted material (failures, abandoned directions, objections) is not worthless — it transfers to
problems its authors never considered. So attention moves to the trajectory. But a trajectory record
is *as cheaply fabricated* as the artefact whose function it would inherit. Therefore its credibility
must rest on **distribution across parties who did not coordinate** — and that requires a
**protocol, not a platform**, because a platform operator is party to every entry.

---

## 2. Six method instruments (§2) — these govern everything downstream

### 2.1 The four levels (Definition 2.1) — *the single most load-bearing instrument*

| Level | Held by | Contains |
|---|---|---|
| **L0** external law | jurisdictions | consent, data protection, erasure rights. **Described, never encoded.** Enters L2 only *negatively*, as a constraint ruling designs out. |
| **L1** operating norms | communities + custodian | which disclosure classes exist, who belongs to them, retention periods, conduct, review templates. Adoptable/revisable. |
| **L2** protocol | the specification | state model + act vocabulary; registration/attestation; attribution + absorption links; parent links + divergence; disclosure classes **as opaque enforced values**; conformance. |
| **L3** application | implementers/users | interfaces, capture assistants, search, structural matching, summarisation, visualisation, **evaluation of content**. Replaceable; protocol implementable with *none* of it. |

> **Requirement 2.2 (Capacity and content).** An element belongs to L2 only where interoperability
> requires agreement on it *and* it survives change in surrounding technology.
> **The protocol carries the capacity; the normative level carries the content.**

Consequences: all analytical/AI capability is L3. A data model that cannot express redaction
forecloses lawful operation in every erasure-rights jurisdiction — no charter repairs that.

### 2.2 Protocol vs plan (Def. 2.3)
A **plan** specifies outcomes and steps to them. A **protocol** specifies which acts are admissible,
what each does to a shared state, and what conformance is — and *leaves every participant's
trajectory undetermined*. Relation = grammar to sentences. Any drift into prescribing what
participants should record/conclude/value is **an error to be corrected, not a position to defend**.

### 2.3 Modal marking (Convention 2.4)
Three modes, never mixed: **analysis** (what is the case, with evidence) · **design** (what a spec
requires, by derivation) · **envisagement** (what would follow in use — supported by nothing yet).
No envisagement sentence in a design section.

### 2.4 Borrowed analogies carry stated boundaries
From version control: append-only history, content addressing, parent links, branching.
**Not merging.** From network protocols: layering, implementation-independence, conformance.
**Not** delivery guarantees, formal verification, packet semantics.

### 2.5 No redefinition (Req. 2.5)
Where a deployed standard defines a needed vocabulary, **bind to it**. New terms only where
nothing deployed covers the case. Cost: dependency on vocabularies the project doesn't maintain.

### 2.6 No scalar (Req. 2.6) — *the most counterintuitive constraint*
**No scalar quantity over participants or over trajectories; no total order over either.**
Local two-valued acceptance conditions replace indicators throughout.
Cost stated openly: cannot report "a project is going well", cannot rank contributors for a hiring
committee, cannot summarise standing in a number. Anyone wanting one computes it at L3 and owns
the consequences. Grounds: (i) reactivity/Goodhart — a measure adopted for evaluation becomes the
object of effort (Espeland & Sauder 2007); (ii) deeper — a quantity over a trajectory measures a
**realisation, not a capacity** (Prop. 10.3).

### 2.7 Fixed terms
- **Trajectory** — ordered record of the transitions a shared understanding has passed through, with
  the acts and the parties. *Current state is derived from the record, never stored alongside it.*
- **Transition** — a change from one identified state to another, by an act of a stated type,
  referencing the prior state, registered by a party.
- **Attestation** — registration of a transition **by a party distinct from the one proposing it**,
  with identifier and signature.
- **Disclosure class** — value governing to whom a record may be disclosed; enforced at L2,
  interpreted at L1. **Ground** — the stated reason for restricting, which determines both what is
  restricted and what remains disclosable.
- **Propagation** — movement of transitions *between* trajectories and *between independent
  implementations*. Excludes mere dissemination of finished artefacts.
- Terminology note: the epistemic unit is called a **transition**, never a "commit", to avoid
  collision with version-control commits in the same repositories.

### 2.8 Declaration of interest
Author founds a society that would host an implementation and is a candidate custodian. Two rules:
the society's activity is evidence for nothing; and every requirement on custodians applies to it
without exception (forkable spec; stewardship separated from operation).

---

## 3. Motivating conditions (§3) — *motivation, not evidence*

**Encounter condition.** Much of what changes an inquiry arrives from outside its plan
(Merton's serendipity pattern; Dunbar 1997 on lab meetings as sites of analogical conceptual change).
Present arrangements make such encounters structurally improbable.
- **Claim 3.1** is narrow: the design lowers the **cost of preparation** — a recorded, available
  state is preparation externalised so another party's preparation may meet it. *Not* a claim about
  the frequency of encounter.
- **Req. 3.2:** every statement about encounters is envisagement, and the counter-evidence must be
  cited alongside it. Counter-evidence: Irving et al. 2020 — occupants of a building designed for
  serendipitous collaboration developed strategies to *avoid* it.

**Generativity condition.** *Generativity* here = the capacity of a **relation** to produce states
neither party held. Distinguished from the developmental-psychology sense and from Zittrain's
platform sense (capacity of a technical system to admit contributions).
Evidence that artefact volume/composition is changing (Glynn 2024; Liang et al. 2024 on 6–17%
AI-modified text in CS peer reviews; redundant-publication growth 2022–24) — but **no study measures
the evidential value of an artefact directly**, so the whole argument is explicitly conditional.

C2PA content provenance is the instructive parallel: it certifies *who asserted what and when*, not
truth; and embedded credentials get stripped on redistribution. Both limitations reappear here and
force the two answers: **registration by a distinct party** and **portability**.

---

## 4–10. The survey (concessions) — *what is already occupied*

### §4 Correspondence networks
Mersenne, Hartlib, Oldenburg. The circulating unit was a **state of an inquiry**, not a result;
circulation was mediated by a party who held the network; the record was retained **privately**.
*Philosophical Transactions* (1665) began as a **periodic digest of Oldenburg's post** — i.e. the
periodical **compressed an existing layer and then displaced it** (Claim 4.1), keeping the
**registration of priority** and shedding the **warranting detail** (Shapin & Schaffer 1985 on
Boyle's circumstantial "literary technology"; Bazerman 1988 on the contraction).
**The countersigned laboratory notebook** — bound, paginated, signed by a witness who was not the
inventor — is the nearest historical precedent for attestation, *and it shows attestation is
compatible with keeping the content private*.
Boundary: establishes precedent only. Nothing about feasibility, desirability, or magnitude at
present scale.

### §5 The reputation-mediated model
Cycle: standing → resources → work → standing (Merton 1968, Matthew effect).
**Two functions conceded without qualification and which any proposal must preserve:**
(1) concentration of resources on evidenced capacity; (2) **priority as the reward that makes early
disclosure rational** (Merton 1957).
Documented difficulties: low inter-assessor agreement (Cole et al. 1981; Pier et al. 2018; Fang et
al. 2016); competition consumes ~the value of the awards (Gross & Bergstrom 2019); **penalty on
novel combination** (Boudreau et al. 2016; Wang et al. 2017) — assessment computes expected value
from precedent (Claim 5.1).
Political economy: standing is a **positional good** (Hirsch 1976) — competition for it cannot be
dissolved by increasing supply; credentialing is consumed cheaply by parties who bear none of its
cost; incumbency is concentrated while reform benefit is diffuse (Olson 1965). **Adoption cannot be
expected on merit.**
Boundary: every cited study samples producers who *entered* the procedures — silent by construction
about the population the diagnosis concerns.

### §6 Open platforms
Conceded in full: preregistration + Registered Reports (pre-commitment works, but only where the
outcome lies in the future); repositories/identifiers/deposit (**taken as substrate, never
reimplemented**); **Octopus** — 8 publication types along research stages, hierarchical linkage,
priority registered at every stage, open post-publication review; ResearchEquals; open commentary.
**Limitation that matters:** a comment attaches to an *artefact*; where it persuades an author, the
relation between comment and change is **recorded nowhere**.
**Claim 6.1** — nothing surveyed takes *the transition between two identified states* as its unit,
and four functions are absent throughout: attested registration; absorption attribution;
portability as a bound on authority; grounded restriction.
Structural note: every system here is a **platform** (operator, database, location).

### §7 Standards — bind, don't redefine
PROV (entities/activities/agents, derivation, attribution) · CRediT (contributor roles) · CiTO
(typed citation relations) · W3C Web Annotation (body/target/motivation + selectors) · RO-Crate/FAIR
packaging · micro/nanopublications · repository notification + federation protocols.
**Definition 7.1 / Claim 7.2 — the pivot of the paper:** all of these are **description languages**
(fix a vocabulary for recording what occurred, impose no condition on what may occur). GRA specifies
an **interaction protocol** (which acts are admissible, what each does to a shared state, which
party may perform each, what conformance requires). None of the standards requires registration by a
second party, constrains record order, or defines conformance *for a process* rather than a document.

### §8 Rationale capture — *the decisive section*
IBIS (Kunz & Rittel 1970) → gIBIS (Conklin & Begeman 1988) → Compendium/dialogue mapping;
design rationale QOC (MacLean et al. 1991); scholarly claim ontologies (ScholOnto, Buckingham Shum
et al. 2000; micropublications, Clark et al. 2014).
> **Claim 8.1. The representational problem is solved** — since 1970, repeatedly, by capable
> funded people, connected to deployed standards. **The recorded cause of non-adoption is capture
> cost:** the work of recording falls on the party who gains least, at the moment they can least
> bear it, in a form serving a different party later (Grudin 1988).

> **Requirement 8.2 (Recording as byproduct).** Every act the protocol defines is an act a
> participant performs **for a reason of their own**, with the record falling out of its
> performance. An act existing so that a record should exist will not be performed; any element
> depending on such an act is moved to an optional tier or removed.

Excludes: general obligation to document reasoning; any separate structuring stage after the work.
Admits: an objection registered because the raiser wants a claim changed; a decision recorded because
a group must remember what it ruled out; a release declared because the author wants something citable.

### §9 Norms, ethics, law
Mertonian norms govern *results*, not process. Authorship criteria + CRediT attach credit to a
finished work — **this design moves the attachment point to a change within one**. Fricker 2007
(testimonial + hermeneutical injustice) names the diagnosis but supplies no infrastructure.
**Claim 9.1** — copyright (expression), patent (invention), trade secret (non-disclosure), moral
rights (attribution/integrity) all protect *finished products*. **None protects a party's position
in an ongoing process of generation.** Two consequences: the design offers **evidence, not a right**
(sealed registration); and attribution is modelled on **moral rights** — attribution *without any
power to exclude* — to avoid the anticommons (Heller & Eisenberg 1998; Boyle 2008).
Lex informatica (Reidenberg 1998; Lessig 2006) accepted: a data model *is* a normative fact — but
the response is to keep protocol rules few, explicit, inspectable, and push contested content to L1.

### §10 The limit of legal reconstruction
Evidence is discrete; generation is continuous. The design **improves the sampling without changing
its character** (Claim 10.1). Causal attribution under cumulative/nonlinear conditions strains the
counterfactual test (Wright's NESS; Halpern & Pearl).
> **Definition 10.2 / Proposition 10.3.** A **trajectory** is the recorded sequence. The
> **generativity of a relation** is its capacity to produce states its participants did not hold.
> Two trajectories may **coincide in recorded appearance while differing entirely in generativity**
> — the record holds what occurred, not what the relation was capable of.

This is the deeper ground of the no-scalar rule. **Open question the paper does not answer:** how
generativity is to be *represented*, *reasoned about*, *utilised*, and *protected*. GRA contributes
to the first only.

---

## 11–20. The derivation (Part II) — where the requirements come from

### §11 Displacement of evidential value
**Def. 11.1 (separating condition)** — after Spence 1973: an artefact carries evidence of capacity
only while producing it is *more costly for a lower-capacity producer*, by a margin making it
worthwhile for one and unattractive for the other. **The evidence was never in the object; it was in
the difference between what the object cost different producers.**
**Prop. 11.2** — a uniform fall in production cost weakens the evidential function while the
artefact, the practice, and the systems reading it all remain. **The failure is invisible from
inside the practice.** (Says nothing about quality of content.)
**Req. 11.3** — any replacement channel must satisfy the same separating condition. Since expense is
excluded by Req. 8.2, credibility must rest on **something the producing party does not control
alone** → §12.

### §12 Fabrication and distributed attestation
**Claim 12.1** — a record held and produced by a single party inherits the artefact's fabrication
cost. Length, detail, internal consistency, and the appearance of struggle are properties a
fabricated record has as readily as a true one.
Three sources of credibility: **cost** (excluded by 8.2) · **pre-commitment** (real but only covers
what lies in the future) · **distribution** (general).
> **Requirement 12.2 (Distributed attestation).** A transition is registered by a party distinct
> from the one proposing it, with that party's identifier recorded. Credibility follows from the
> **distribution of registrations across parties who did not coordinate**, and from **no property of
> the record's content, length or detail**.

Implications: registering must be **cheap** (Grudin applies to registrars too); entries must be
tamper-evident (content addressing + parent links — available from the substrate, no new crypto).
**Limits:** attestation establishes registration, not truth/improvement/understanding; requires ≥2
parties (personal tier has *zero* evidential weight and is justified by usefulness alone); collusion
is raised in cost, not eliminated; **counting attestations is forbidden** (a scalar; farmable by
reciprocal registration).
> **Claim 12.3 — why a protocol and not a platform.** A platform can host a record but cannot supply
> the independence its credibility depends on, since the operator is party to every entry.

### §13 The unit of record
Candidates rejected: **utterance** (unreadable volume; burden moves to interpretation), **output**
(Octopus-style — shows a second hypothesis exists, not that *this objection* converted the first
into it), **artefact version** (difference computed, reason absent by construction).
**Adopted: the transition.** Components + why each: prior state ref (a change naming no antecedent
degrades into commentary) · posterior state · typed act (searchability) · performing party
(attribution) · registering party (Req. 12.2) · disposition · absorption links.
> **Req. 13.1 (Granularity).** A transition references a **specific identified prior state**.
> A record attached to a project, repository or document as a whole is not a transition.

This *diagnoses* §6's observation: commentary systems never became epistemic infrastructure because
a comment attaches to an artefact — nothing transitions, no state is superseded.

**Worked case 13.2** (social theory, 3 steps): trust-between-individuals → [party B objects: omits
institutional power] → trust-as-process-shaped-by-power-asymmetry → [party C, entering from commons
governance, connects to monitoring/graduated sanction] → trust-generated-under-governance.
Exhibits: two transitions each referencing the state altered; an objection by a non-author with
acceptance as disposition; an **encounter** (entering party) at step 3; both attributable *without
either claiming to have authored the theory*.

**Three consequences:** *curation follows from the unit* (a two-hour meeting altering no state
produces no record — nobody decides what deserved keeping, so nobody holds a position over the
archive); *performativity resisted* (inflating the record requires recruiting a registrar);
*compression without a model* (typed transitions are readable by anyone — this is what independence
requires in practice).

> **Req. 13.3 (Factorisation of the type).** Type is factored into independent dimensions with small
> closed vocabularies, not one flat enumerated list. Flattening multiplies terms and inter-rater
> agreement declines as categories rise; deliberation over classification re-introduces capture cost.

| Dimension | Values |
|---|---|
| **act** (8) | question · claim · challenge · transformation · decision · connection · verification · release |
| **target** | question · assumption · hypothesis · concept · theory · method · path · artefact |
| **relation** | extends · modifies · replaces · refines · generalises · specialises · transfers → **binds to CiTO** |
| **trigger** | self · literature · experiment · simulation · discussion · objection · failure · model suggestion · entering party |
| **disposition** | accepted · contested · **unresolved** |

*Contribution is not an act* — it types a participant's part in an act and binds to CRediT.
**The `unresolved` disposition is essential:** most objections in theoretical work are never
resolved; a vocabulary with only accept/reject would produce a systematically false record and exert
pressure toward **fabricated closure**.

### §14 Divergence, and no merge
Identity of a state across transitions is **a matter of record, not adjudication** — a state is a
later version of another where a chain connects them; whether they are "the same theory" is a reader's
L3 judgement.
**Claim 14.1 — no merge operation.** Version control merges because (i) identity criteria exist at
byte/line level, (ii) changes to distinct regions compose, (iii) a test decides the result. **None
holds for a state of an understanding.** What is called integration is either a **synthesis** (a new
state referencing ≥2 parents) or an **absorption** (taking content from another trajectory *with
attribution to its originator*). **The word "merge" appears nowhere in the specification.**
A trajectory is a **directed graph, not a sequence**. Two states sharing a parent = divergence;
neither is designated the principal line. **Attribution crosses divergence.**
**Disanalogy with software forks:** in software a fork is a failure to be reunified; in inquiry a
fork is *frequently the correct outcome*. **Plurality is the normal shape of a healthy record.**
Forgone: canonical current version; automatic reconciliation; protection against the attention cost
of plurality.

### §15 Positions and functional authority
Four positions the design **generates** (not imports): **registrar** · **trajectory steward** ·
**holder of disclosure authority** · **custodian of the specification**.
Openness does **not** dissolve hierarchy — contradicted by Shaw & Hill 2014 (concentration of
decision rights in open peer-production communities) and Michels 1962. The design assumes it is false.
> **Def. 15.1.** A position is **functional** where constituted by acts the arrangement requires,
> recorded and attributable, with occupancy depending on continuing to perform them. It is
> **structural** where occupancy confers persistent standing, or where others' capacity to act
> depends on the holder's permission.
> **Req. 15.2 (Admissibility).** Two joint conditions: (i) constituting acts are recorded as
> transitions or administrative operations, attributable and visible; (ii) **participants retain the
> capacity to proceed without the holder's permission** (supplied by portability, §16).

Neither suffices alone: visibility without exit → documented autocracy; exit without visibility →
participants can't tell what a holder has done. *This is why administrative operations are recorded
distinctly from transitions.* Limits: a protocol cannot prevent positions forming; **recording is
not review** (a steward who always declines one participant's transitions leaves a complete record
and the protocol does nothing — L1 responds); the condition secures *capacity*, not practice.

### §16 Portability as the bound on authority
Hirschman 1970 (exit/voice): availability of exit conditions everything about how voice operates,
**whether or not exit is used**.
> **Claim 16.1.** In this design the bound on any position's authority **is the cost of exit**, not
> any rule addressed to the holder. (Rules require an enforcer; the enforcer occupies a position;
> the regress terminates only where a participant can act without anyone's permission.)
> **Req. 16.2 (Portability) — five joint properties.** The complete record (transitions,
> attestations, attribution, parent links) is (1) obtainable by any participant **without
> permission**; (2) in a **self-describing format readable without the producing software**;
> (3) carries **identifiers that stay resolvable when held elsewhere**; (4) **licensed** to permit
> continuation; (5) **continuable under the same protocol by an implementation the original operator
> does not control**.

**Property 5 is what distinguishes portability from export.** A data dump satisfies 1–4 and leaves
departing participants with an archive.
Evidence: open-source forks are rare *because the option exists*. Contrast: editorial secessions in
publishing are notable events — **Claim 16.3**: their rarity is evidence about **exit cost**, not
about the quality of what was departed from. A journal's standing lives in its title and indexing;
it does not leave with the people.
**Limits:** portability secures the record — **not the participants, not the resources, not the
standing**. Standing is positional and held by the arrangement. It converts a prohibitive exit cost
into a substantial one; expecting frequent secession is unwarranted.

### §17 Entry paths
Four candidate qualifications: demonstrated contribution · code of conduct · trust extended by
existing participants · verification of competence.
> **Claim 17.1 (bootstrap failure).** Qualification by demonstrated contribution *requires access in
> order to be satisfied and grants access in return for satisfaction* — closed against every party
> with no prior position. Trust-extension has the same form with an extra step.

(Same shape as Arrow 1962 on information as a commodity, and as §5's novelty penalty. Also the
empirical mechanism by which open communities concentrate decision rights.)
> **Req. 17.2 (Entry path).** At least one path exists by which a party with **no prior position**
> may perform an act **decided on the act itself**; cheap to attempt; its **material supplied by the
> arrangement**; outcome verifiable by others.

**The mechanism is already in the vocabulary:** a trajectory holds states whose disposition is
`unresolved` — standing objections, open questions, obstacles. A **register of unresolved states is
the entry path** (cf. `grrp open` in Paper IV). A stranger may `connect`, `challenge`, or `verify`
against an identified state; each is decided on content; none requires standing.
Untouched: volume/attention rationing; conduct+moderation (L1); competence for restricted classes;
and the fact that an arrangement whose participants decline every stranger still *conforms* — the
record of declining is what a reader has to go on.

### §18 Encounter and the participant set
A trajectory changes in **content** and in **who holds it** — both are transitions.
> **Def. 18.1 (Encounter).** A transition performed by a party who has performed **no prior act** in
> the trajectory, with a trigger identifying the occasion. No new primitive is added — the trigger
> dimension already covers it.
> **Claim 18.2.** The record holds **the generation of the arrangement that produced an
> understanding**, not the understanding alone. Where the unit is an output, an entering
> participant leaves no trace beyond a name on a later artefact.

Uses: attribution for parties who altered a trajectory **without producing an artefact of their own**;
conditions of productive encounter become inspectable (material for study, not a protocol function).
> **Claim 18.3 (matching, narrowed).** The discovery claim concerns **structural similarity between
> states in different fields** and **nothing within a field** (within a specialty everyone already
> knows each other). Cf. Swanson 1986 (disconnected literatures jointly entailing a conclusion
> neither states) — extended here from published claims to *recorded states, including unresolved
> ones*. It depends on a large corpus, so it is a **late property of an adopted arrangement and
> supplies no reason for anyone to adopt one**.

Two further boundaries: cross-vocabulary structural matching is an **unsolved L3 research problem**;
and **recording an encounter alters it** — the material most worth preserving is the least likely to
be produced under observation.

### §19 Priority and disclosure timing
The dilemma: circulation is where benefits arise; concealment is where a participant's protection
lies. **Asymmetric** — a well-positioned party risks little; a party without position bears the whole
risk, and that is the population the diagnosis concerns.
Priority answers it in the incumbent system but **attaches at publication**, i.e. after the work is
substantially complete — the generative phase is unprotected, and the only instrument is silence.
Deployed devices (preregistration, stage-wise publication, preprints) all **require disclosing the
thing registered**.
> **Def. 19.1 (Sealed registration).** Publication of a value derived from a state's content, from
> which the content cannot be recovered and against which it can later be checked, plus the
> registering party's identifier and a time. Disclosure is a **separate, subsequent** act.
> **Req. 19.2.** Registration is available at the moment the act is performed, at **every** disclosure
> class including disclosure-to-nobody. The record shows *that* registration occurred at its time
> **without showing what was registered**.

**Five limits.** Evidences possession, not understanding/capacity/priority. **Generates nothing while
sealed** — it buys the possibility of later opening, not the benefits of early opening. No protection
against independent arrival. Requires a trusted publisher of the value or a public medium (outside
the protocol). **A timestamp is not priority** — priority is a community's recognition, an L1 matter.

### §20 Transmissibility — *the strongest single result of Part II*
Collins 1974/2010 (TEA laser): labs failed to build the device from published papers; success
followed *contact with people who had built one*. MacKenzie & Spinardi 1995 (nuclear weapons design):
same structure where the incentive to record fully was extreme.
> **Def. 20.1 (The articulable fraction).** That part of what participants held which they were able
> to put into the record. Its complement transmits, if at all, by working alongside them, and **no
> property of the record's design recovers it.**

- **Reuse** survives in weakened form: what transfers is the *propositional content of a failure*
  (an approach was attempted, on what assumption, what obstruction was met) → **redirection of
  attention**, not transfer of capability. A reader cannot take up another's work where it stopped.
- **Evidence** is bounded to *the acts performed* — a record can be traversed by a modest party
  working slowly. Claim is that the record **discriminates better than an artefact under present
  conditions**, not that it measures capacity.
- **Hazard** is bounded by the same fraction: what a hostile reader gets is the propagable part.

> **Proposition 20.2.** The component the artefact omits is **simultaneously** the component
> carrying value in reuse, evidential force, and hazard. All three scale together with the
> articulable fraction, and **no design increases one without increasing the others.**

Kills a whole class of proposals: you cannot publish the trajectory *minus its dangerous parts* and
retain the benefit. Hence the answer to hazard is disclosure classes + stated grounds (→ Paper III),
never selective omission. Same component also carries the **reputational cost** of disclosing
failure → exploratory vulnerability (Paper III).

---

## 21. The gap, stated once (Claim 21.1)

> No arrangement in the surveyed literatures **(a)** takes the transition between two identified
> states as its unit of record, **(b)** registers that transition by a party distinct from the
> proposer, **(c)** attributes content absorbed from one line of work into another, **(d)** bounds
> the authority of positions by the portability of the record, and **(e)** restricts disclosure on a
> stated ground that determines what remains disclosable — **specified as an interaction protocol
> where the standards are description languages.**
> The elements are severally available; **the conjunction is unoccupied**.

Every element has an ancestor (attestation ← countersigned notebook; attribution ← CRediT + moral
rights; portability ← software forking; grounded restriction ← hazardous-research governance; typed
relations ← CiTO). Novelty is claimed **for the assembly and the requirements forcing it**, not the parts.

**Four findings that withdraw the claim** (stated so a reader can look for them):
1. A deployed system/spec whose unit is the transition between identified states, with distinct-party
   registration → defeats the claim entirely.
2. A spec defining admissible acts + effects on shared state for scholarly work, with conformance →
   defeats the description-language claim.
3. Evidence that rationale-capture systems failed for reasons **other than capture cost**, or were
   adopted more widely → removes Req. 8.2, the principal design constraint.
4. Evidence the separating condition has **not** weakened, or that evaluation has already replaced
   the artefact → removes the premise of the whole argument. *(Empirical; unsettled.)*

---

## 22. The sixteen requirements (the spec is judged against these)

| # | Requirement | Derived in |
|---|---|---|
| **R1** | Recording is a **byproduct** of acts performed for their own sake | §8 |
| **R2** | Deployed vocabularies are **bound, never redefined** | §7 |
| **R3** | A transition is **registered by a party other than its proposer** | §12 |
| **R4** | The unit of record is a **transition referencing an identified prior state** | §13 |
| **R5** | The log is **append-only**; current state is **derived**; edits are **detectable** | §13 |
| **R6** | **Divergence is recorded; no merge operation is defined** | §14 |
| **R7** | The complete record is **portable and continuable elsewhere** | §16 |
| **R8** | An **entry path** exists: cheap to attempt, externally verifiable | §17 |
| **R9** | **Absorbed content is attributed to its originator, without veto** | §9 |
| **R10** | **No scalar** quantity over participants or trajectories | §2 |
| **R11** | Disclosure is **monotone**: scheduled release, **no withdrawal** | §10 |
| **R12** | Personal content is **separable**, so redaction leaves the log intact | §9 |
| **R13** | Records are **durable**: plain formats, distributed custody, deposit | §25 |
| **R14** | The protocol is implementable with **no analytical capability present** | §2 |
| **R15** | The **core tier is worth adopting by a single participant** | §3 |
| **R16** | A **release can emit the artefact the incumbent reward system accepts** | §5 |

**The three that constrain most severely:** **R1** (eliminates the most otherwise-attractive designs
— no documentation obligation, no post-hoc structuring stage), **R10** (costs the ability to report
progress, rank contributors, or summarise standing), **R14** (costs the ability to require
model-assisted capture, matching, or summarisation).
Status: **not claimed complete**; **not independent** (R3+R7 both serve credibility; R1+R15 both
serve adoption); and this is the table Paper IV is assessed against.

---

## 23. The architecture in outline

```
   Edge applications      capture assistants · search · structural matching ·
   (L3, outside            summarisation · visualisation · assessment of content
    conformance)          — the protocol requires NONE of it
            ↑ (2) read/write records without being required by them
┌──────────────────────────────────────────────────────────────────────┐
│ PROTOCOL — the TRANSITION PLANE        ← the system of record        │
│ typed transitions · parent links · attestation + signature ·         │
│ attribution + absorption links · disposition · disclosure class      │
│ + declared ground.  APPEND-ONLY.                                     │
└──────────────────────────────────────────────────────────────────────┘
            ↑ (1) registration by a responsible party PROMOTES an event to a transition
┌──────────────────────────────────────────────────────────────────────┐
│ PROTOCOL — the EVENT PLANE                                           │
│ automatically generated records that something occurred: meetings,   │
│ comments, file changes, permission changes, model operations.        │
│ PRIVATE to participants by default. Carries no epistemic claim.      │
└──────────────────────────────────────────────────────────────────────┘
            ↓ (3) delegation: storage, identifiers, history, transport
   Substrates              version control (history, content addressing) ·
                           repositories (storage, PIDs, archival deposit) ·
                           notification/federation (exchange between implementations)
                          — existing, maintained by others, NOT reimplemented
```

The event plane is **where the surveillance hazard falls** — a complete log of who attended and whose
files changed is a monitoring record by construction. Hence: confined to participants, disclosed only
through registration.
**Claim 23.1** — the arrangement contributes **the transition plane and the rules governing promotion
into it**, and nothing else.

**Three tiers** (this stratification is what makes R15 achievable):
- **Personal** — one participant, transitions with parent links against identified states,
  append-only log, derived views, three acts. Gets: a searchable record of what was ruled out and
  why; a standing list of unanswered objections; a release emitting a citable document.
  Gets **no evidential weight whatever** (attestation impossible with one party).
- **Group** — attestation, contributor roles, absorption links, disclosure classes. **Credibility begins.**
- **Open** — propagation, distributed custody, deposit, charter reference. Exchangeable with
  implementations elsewhere.

Left to Paper IV: act vocabulary + factorisation; identifier and signature construction; disclosure
classes bound to grounds (→ Paper III); **conformance conditions** (without which the requirements
are aspirations).
**Claim 23.2** — this establishes the requirements are jointly satisfiable, and **nothing about
whether the arrangement works**. Adequacy is settled by use.

---

## 24. Two speculative formal models (envisagement — the protocol depends on neither)

The design is **event-based**: state persists until an act occurs; nothing updates on a schedule.
**Req. 24.1** — this is a reference to the *class of event-advanced systems* (DEVS, Zeigler et al.
2018; spiking networks, Maass 1997 are another instance). **No property of neural computation is
transferred.**

1. **Generalised heterogeneous dynamical network (Def. 24.2)** — nodes each carrying their own state
   space *and their own law of evolution* (discrete dynamics on a complex; spiking; continuous field;
   discrete-event automaton), coupled by **propagation operators** Πᵢⱼ mapping events emitted at vᵢ to
   admissible inputs at vⱼ. Motivation: a knowledge trajectory couples participants whose internal
   dynamics are not of one kind. Nearest prior art: DEVS multi-formalism coupling; multilayer network
   dynamics. **Three stated obstacles:** a shared time base + consistent event ordering across
   dynamics that individuate events differently; coupling semantics across differing state-space
   types; **closure under coupling**.
2. **Spin-foam-like representation** — a history as a **two-complex**: vertices = events, edges =
   couplings between elements of an event, faces = primitive elements; the §13 transitions are its
   one-dimensional shadow. Ancestry: Whitehead 1929 (events as primitive constituents); Kowalski &
   Sergot 1986 (event calculus). **Three objections recorded and unanswered:** no analogous algebraic
   structure on the informational side (so the borrowing is figurative); no counterpart to
   superposition, so the amplitude machinery may be inert; borrowed heavy formalism without its
   home-domain empirical constraints is a recognised failure mode.

**Four conditions for either to become formal:** explicit mapping with no ornamental elements; a
composition rule gluing histories along shared boundaries (natural candidate: a state of a shared
understanding); an interpretation of the weight assigned to a history; and a demonstration that some
question about trajectories is answerable in it **and not in the directed graph of §14** — which is
the representation the protocol actually uses and which is adequate to everything it requires.

---

## 25. Open problems, by what each awaits

- **Legal** — the unprotected position of a party in an ongoing generation; erasure rights vs
  integrity guarantees (answered by separating content from the attested skeleton, but not
  adjudicated); cross-border multiplicity of regimes; status of model-assisted contributions.
- **Normative** *(these bear directly on whether the claimed benefits appear)* — whether registration
  confers priority; **whether disclosed failure can be non-punitive** (the reuse argument depends on
  it); whether the **labour of registration** is recognised (unpaid work for someone else's benefit —
  precisely the disparity that killed the §8 systems; answered by making it cheap, not by rewarding
  it); whether an unresolved disagreement is publishable as a state.
- **Organisational/economic** — decades-long custody with succession; **assessment capacity is
  subtractable** and rationing without ranking is unsolved (→ Paper II); the **regressive
  distribution of overhead** (recording falls hardest on those with least time — exactly the
  population the diagnosis concerns).
- **Technical** — representing a state so structural similarity is computable across vocabularies
  (undemonstrated; retrieval by topic does not do it); trajectory-graph shape analysis (persistent
  homology, Carlsson 2009 — applicability unknown); quantum approaches (marked speculative; three
  obstacles: hardware, unproven advantage, and the representation problem is prior).

**None is required for conformance.** All sit at L3 so the protocol depends on none of them.

---

## 26. Conclusion — five results, three concessions

**Results:** (1) the evidential function rests on a separating condition and is weakening invisibly;
(2) a single-party record inherits the same weakness, so credibility must come from distributed
attestation — **hence a protocol, not a platform**; (3) the representational problem was solved
repeatedly and failed on **capture cost**, which excludes more designs than any other consideration;
(4) value-in-reuse, evidential force, and hazard are **the same component** and scale together;
(5) the layer is a **restoration**, not a novelty.

**Concessions:** the prior art in platforms/standards/representational systems; **no evidence for the
encounter motivation** (the best study points the other way); recognition is positional, so nothing
here increases the standing available — **attribution redistributes it, which predicts resistance
from parties who benefit from the present invisibility of others' contributions**.

> The account's contribution is to take capture cost as its **first constraint** rather than an
> obstacle to be regretted, and to see what a design looks like when **nothing may be required of a
> participant that the participant would not do anyway**. The result is smaller than the designs that
> failed, and whether smaller is enough is a question no argument settles.

---

## Implications for this repository

- README/plans must not promise **progress reports, trajectory health, similarity ranking,
  contribution scores** as protocol features. Every such thing is **L3** and most are forbidden as
  scalars (R10). *(The current `plans/implementation_plan.md` Stages 4–5 need this correction — see
  [gaps-and-repo-actions.md](gaps-and-repo-actions.md).)*
- The word **"commit"** should not name the epistemic unit — the paper deliberately says
  **transition** to avoid collision with git commits in the same repository. The README's
  "GRA Commit Concept" contradicts the papers.
- The word **"merge"** must appear nowhere in the UI or spec (Claim 14.1).
- Any claim about encounters/serendipity must be marked **envisagement** and carry the Irving et al.
  2020 counter-evidence (Req. 3.2).
- The personal tier must be **worth using alone on day one** (R15) — and must be described as
  carrying **no evidential weight** (§12.4), which is a distinction the README currently blurs.

Related: [paper-II-incentives-and-adoption.md](paper-II-incentives-and-adoption.md) ·
[paper-III-grounds-of-restriction.md](paper-III-grounds-of-restriction.md) ·
[paper-IV-grrp-specification.md](paper-IV-grrp-specification.md) ·
[glossary.md](glossary.md)
