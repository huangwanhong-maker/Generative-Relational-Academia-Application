# Notes — Paper IV: *Specifying the Generative Relational Research Protocol*

**Subtitle:** Architecture, Conformance, and Deployment over Existing Repositories
**Author:** Wanhong Huang · working draft, 2026 · CC BY-NC 4.0 · 63 pp, 24 sections
Source: [papers/GRA-paper-IV-...pdf](../papers/GRA-paper-IV-Specifying-the-GRRP.pdf)

**Role in the series:** the **normative specification**. Discharges Paper I's sixteen requirements and
fixes conformance. **Published as GRRP v0.1** — explicitly unfinished, with an amendment procedure,
*because a specification published as finished would contradict the account it specifies.*

> This is the paper the implementation is built against. [plans/implementation-plan.md](../plans/implementation-plan.md)
> is its builder-facing restatement — **the specification governs where the two differ.**

**Conformance vocabulary:** RFC 2119 `must / must not / should / may`. A `should` may be departed from
where the implementer **states a reason**.

---

## The four standing exclusions (§1)

Stated up front so absences are not read as omissions:
1. **No quantity over participants or trajectories, and no total order over either.** An implementation
   may compute one — outside conformance, on its own account.
2. **No analytical capability required.** Every conformant operation is performable **with a text
   editor and a version-control system**. Model-assisted capture is a convenience whose absence
   changes nothing about conformance.
3. **No merge operation.**
4. **No rules of conduct, membership criteria, retention periods or consent requirements.** These
   belong to a community's **operating charter**, which the protocol references and does not interpret.

> **Requirement 2.6 (Capacity and content).** The protocol fixes **the capacity and never the
> content.** A field whose values an implementation *enforces without interpreting* belongs to the
> protocol; the meaning assigned to those values belongs to the charter.

---

## §3 Architecture: three planes over delegated substrates

```
Edge applications  (outside conformance — the protocol requires none of it)
        ↑ (2) read and write records without being required by them
┌─ PROTOCOL ─ TRANSITION PLANE ── the system of record, APPEND-ONLY ────────┐
│ typed transitions · parent links · attestation + signature · attribution  │
│ + absorption links · disposition · disclosure class + declared ground     │
└───────────────────────────────────────────────────────────────────────────┘
        ↑ (1) registration by a responsible party PROMOTES an event to a transition
┌─ PROTOCOL ─ EVENT PLANE ──────────────────────────────────────────────────┐
│ auto-generated records that something occurred: meetings, comments, file  │
│ changes, permission changes, model operations. PRIVATE TO PARTICIPANTS.   │
└───────────────────────────────────────────────────────────────────────────┘
        ↓ (3) delegation
Substrates: version control (append-only history, content addressing, transport) ·
            repositories (storage, persistent identifiers, archival deposit) ·
            notification/federation (COAR Notify, ActivityPub)
```

> **Requirement 3.1 (Privacy of the event plane).** Event-plane records are disclosed **to
> participants of the trajectory by default and to no other party**. An event reaches wider disclosure
> **only through a transition that references it**, and an implementation **must not export, index or
> publish the event plane as such.**
> *(This is the plane where the surveillance hazard falls — a complete log of who attended, who
> commented and whose files changed is a monitoring record by construction.)*

**Claim 3.2.** The protocol contributes **the transition plane and the rules governing promotion into
it — and nothing else.** Reimplementing storage/identifiers/history/transport would inherit their
maintenance and compete with their installed base.

> **Requirement 3.3 (Substrate independence).** The specification **names capabilities, never
> products.** No conformance condition is expressed in terms of a particular VCS, repository service,
> identifier scheme or federation protocol; an implementation **must state which system supplies
> each**.
> *Cost, stated plainly:* no prescribed file layout or wire format — **interoperability rests on the
> record model and the bindings**, not on byte-level agreement (see the exchange minimum, §16).

> **Requirement 3.4 (Resolution and content addressing) — two properties commonly assumed and
> commonly absent, both load-bearing:**
> 1. **Every reference to a state or artefact must use an identifier that resolves independently of
>    the implementation that created it.** *An identifier resolving through the original operator's
>    service stops resolving when participants leave — and portability becomes nominal.*
> 2. **Every transition must carry an identifier derived from its content and from its parents'
>    identifiers**, so altering an early transition invalidates everything after it.

---

## §4 The event / transition / artefact model

**Definition 4.1.** An **event** records that something occurred and asserts nothing about an
understanding. A **transition** records that an identified state became another, through a typed act
performed by a party and registered by a party. An **artefact reference** records that a produced
object exists, with a resolving identifier.
*The division carries the economics of capture:* events are generated by systems participants already
use, so **near-zero cost, possibly large volume**; transitions require a human judgement **and a
registering party**, so **non-zero cost, small volume**; artefact references fall out of deposit.

> **Requirement 4.2 (Recording as byproduct).** Every act must be one a participant performs **for a
> reason of their own**. An implementation **must not require any act whose only purpose is that a
> record should exist**, and must not make conformance depend on such an act.
> *The requirement that determined the whole design.*

> **Requirement 4.3 (Promotion).** A transition enters the log **only by the act of a party who
> accepts responsibility for it.** An implementation may propose candidates by any means — **including
> analysis of the event plane by a model** — and a proposal becomes a transition only when a
> responsible party registers it. The record **must show which party registered**, and **must record
> that a proposal originated from an automated analysis where it did.**

Three consequences spelled out for implementers:
- **Cheap confirmation is permitted; reflexive confirmation is not.** One affirmative action is fine;
  **a default that registers unattended proposals violates the requirement**, because the record's
  credibility rests on registration meaning something.
- **Volume on the event plane is harmless.** A two-hour meeting altering no state produces events and
  no transitions — *nobody decides what deserved keeping, because the recording unit decides it.*
- **A model may occasion a transition and may not author or register one.** The origin is marked, which
  lets a later reader weigh it and keeps the arrangement compatible with authorship rules excluding
  non-human authors.

> **Requirement 4.4 (Append-only log and derived state).** The transition plane is append-only; a
> recorded transition **must not be altered or removed** — a correction is a further transition
> referencing the one corrected. **The current state must be derived from the log on demand and must
> not be stored as an authoritative object alongside it.**
> *The second sentence is the one most often violated, because a stored current state is convenient and
> fast. Where a stored snapshot is authoritative, the log becomes a secondary artefact that may drift
> from it or be edited to match it — and **every claim the protocol makes about credibility fails at
> once**. Caches are permitted if reconstructible from the log and marked as derived.*

**Requirement 4.5 (Granularity).** A transition **must** reference a **specific identified prior
state**. A record attached to a project, repository, document **or person** as a whole **is not a
transition, and an implementation must not admit one.**

**Requirement 4.6 (Separation of administrative operations).** Operations on the record itself
(class changed, permission altered, attribution recorded, fork declared) **must be recorded, must
carry the performing party, and must be distinguished from transitions by a mandatory `kind` field.**
*Two reasons:* administrative activity would otherwise **inflate the apparent generativity** of a
trajectory (the protocol computes no quantity, but **readers will nonetheless count**); and the
admissibility condition on positions requires the acts constituting a position to be recorded — *a
disclosure holder who could alter a class without leaving a record would occupy a position no
participant could inspect.*

---

## §5 States and identifiers

**Definition 5.1.** A **state** is an identified condition of a shared understanding — its recorded
content plus the identifier under which that content is addressed. **Created by a transition and never
modified**; a change is a further state produced by a further transition.
> The **content of a state is deliberately unspecified** — paragraph, formal statement, diagram, claim
> with qualifications, or a pointer to a section held elsewhere. **A specification prescribing the form
> of a scholarly claim would be prescribing research practice.**

**Requirement 5.2 (State identifiers).** Unique within the trajectory · resolves to content for a
party permitted to read it · **continues to resolve when the record is held by another
implementation**. **An implementation must not use an identifier whose resolution depends on a service
it alone operates.** Two satisfying constructions, named without preference: **content-derived**
identifiers, and **repository-issued persistent identifiers**. Where both are used, **record the
correspondence**.

**Requirement 5.3 (Derivation of views).** Any view — **including the current state** — must be
computable **from the log alone**. Caches permitted if reconstructible. *Consequence: a view whose
computation depends on information held only by the implementation (e.g. a proprietary ordering)
**cannot be presented as part of the record** — it is an application output.*

**Requirement 5.4 (Trajectory boundary).** A trajectory carries an identifier, **a statement of the
question or undertaking it concerns**, and the identifiers of parent trajectories where created by
divergence. **A state may belong to more than one trajectory** — the protocol records the sharing and
asserts nothing about which trajectory it principally belongs to (same reason it designates no
principal branch).

**Requirement 5.5 (External references).** Persistent identifier where one exists, **with the scheme
recorded**; otherwise enough descriptive information to identify the work, **plus the date the
reference was made**. *The date addresses a failure that accumulates silently: a reference to a
changed or vanished resource is uninterpretable without knowing when it was made — and a trajectory
whose value appears years later will contain many.*

---

## §6 The act vocabulary and the factorisation — *the part with no counterpart in any standard*

> **Requirement 6.1 (Factorisation).** A transition is typed along **five independent dimensions**,
> each with a **small closed vocabulary**: **act · target · relation · trigger · disposition**.
> **An implementation must not define a single enumerated type combining these dimensions.**
> *Ground: agreement between parties classifying the same occurrence declines as categories rise, and
> a vocabulary requiring deliberation re-introduces capture cost.*
>
> **Implementer's test when tempted to add a value:** *a distinction that two competent participants
> would classify differently more than occasionally belongs in a community's charter, not in the
> protocol.*

### Definition 6.2 — the eight acts

| Act | What it does |
|---|---|
| **question** | opens a line of inquiry, or introduces a new question within one |
| **claim** | states a position as the content of a state |
| **challenge** | raises an objection against an identified state |
| **transformation** | alters a state in response to something, producing its successor |
| **decision** | records that a direction was **taken or abandoned, with the reason** |
| **connection** | relates a state to another state or to an external work |
| **verification** | reports the outcome of a check performed on a state |
| **release** | declares a state published at a class, **with the objections standing against it** |

Three carry more weight than their brevity suggests:
- **decision** is what makes an abandoned line **interpretable later**. *A path recorded as abandoned
  without a reason cannot be revisited by anyone* — and reuse of abandoned work is one of the two
  concrete benefits claimed for the design.
- **release is a declaration and never a judgement.** It asserts a state is published and records which
  objections stand unresolved at that moment. **An implementation must not present a release as a
  certification of quality.**
- **challenge** produces a transition when registered, **and does not thereby alter the state it
  challenges**. Where accepted, a *subsequent transformation* produces the successor, and the two are
  linked by parent references.

**Contribution is not an act** — it types a party's *part in* an act, and binds to CRediT (§7).

### The other four dimensions

- **target** — question · assumption · hypothesis · concept · theory · method · path · artefact.
  *Community-extensible.*
- **relation** — extension · modification · replacement · refinement · generalisation · specialisation
  · transfer. **Bound to a citation-typing vocabulary (CiTO); not defined here.**
- **trigger** — reflection · literature · experiment · simulation · observation · discussion ·
  objection · prior failure · **automated suggestion** · **entry of a new party**. *Where the trigger
  refers to something recorded, the reference is included.* **Community-extensible.**
- **disposition** — **exactly three values: `accepted`, `contested`, `unresolved`.**
  > **Requirement 6.3.** The disposition vocabulary is **fixed by the protocol and must not be extended
  > or reduced.** `unresolved` is required: most objections in theoretical work are never resolved —
  > they stand, and the work proceeds beside them. **A record admitting only acceptance and rejection
  > would be systematically false about the fields this protocol most concerns, and would exert
  > pressure toward fabricated closure.**

**Requirement 6.4 (Extension per dimension).** Communities may extend **target** and **trigger** by
declaring values in a charter (identified in the record). **The act and disposition vocabularies must
not be extended.** An implementation meeting an unrecognised target/trigger **must retain the record
and must not reject it.**
*Asymmetry is deliberate: targets and triggers are domain-specific (a mathematics community wants
obstruction types; a laboratory wants deviation types). **Acts and dispositions are what
interoperability rests on.***

> **Requirement 6.5 (Availability of the open register) — the entry path.** An implementation **must
> make available, at each disclosure class, the set of states within that class whose disposition is
> `unresolved`**, and **must permit a party holding no prior position** to reference such a state in a
> **challenge, connection or verification**.
> *The protocol supplies the addressable problem and the admissible act — and **no obligation to accept
> anything**. Acceptance is decided by the parties holding the state, on the content of the act.*

### The transition record (Figure 6.1)

```
id                content-derived, over payload + parents
kind              transition | administrative operation      ← mandatory
parents           identifiers of prior transitions (≥1; none only for the opening transition)
prior_state       identifier of the state altered
posterior_state   identifier of the state produced
─── the factored type ──────────────────────────────────────
act               one of eight                        (fixed)
target            what the act operated on            (charter-extensible)
relation          posterior to prior                  (bound vocabulary)
trigger           occasion, + event/artefact ref      (charter-extensible)
disposition       accepted | contested | unresolved   (fixed)
────────────────────────────────────────────────────────────
performer         party identifier, with contributor role
registrar         party identifier + signature — DISTINCT (Req. 4.3 / 8.1)
absorption        links to states elsewhere, with attribution (no veto)
disclosure        class, declared ground, release schedule
artefacts         references to produced objects
```
An **administrative operation** uses **the same envelope** with `act`, `target`, `relation`,
`disposition` **absent** and an `operation` field in their place.

---

## §7 Bindings — four, and the protocol's own vocabulary is what remains

> **Requirement 7.1.** Where a deployed standard defines a needed vocabulary, **bind by identifier and
> do not restate its terms.** New terminology is defined **only** for the act vocabulary, the
> disposition vocabulary, and the record structure.
> *Three reasons, the third decisive:* restating acquires an obligation to track revisions; conformance
> becomes cheaper for existing users; and **a specification that reinvents a deployed vocabulary is
> dismissed by the community that maintains it — the ordinary fate of standards written in isolation.*

| Capability | Bound to |
|---|---|
| relations between states | **citation-typing vocabulary (CiTO)** — applied to relations between *states* rather than works |
| contributor roles | **contributor taxonomy (CRediT)** — *also serves the compatibility requirement* |
| agents, activities, derivation | **provenance model (PROV)** — export makes records readable by tooling that knows nothing of GRRP |
| anchored commentary | **annotation model (W3C Web Annotation)** — selectors carry the anchor; **the GRRP act type is carried in the annotation's `motivation`** |

**Claim 7.2.** Under these bindings **the protocol's own terminology reduces to: the eight acts, the
three dispositions, the record structure, and the disclosure + attestation fields.**

**Requirement 7.3 (Recording of bindings).** A record must identify, **for each bound vocabulary, the
vocabulary and the version**. **A value drawn from a bound vocabulary must be recorded as an
identifier in that vocabulary and not as a display label.** *Storing the word `extends` rather than
the vocabulary's identifier is uninterpretable once a second vocabulary uses the same word differently
— translation then depends on a guess.*

**Three failure cases:** a bound vocabulary is **revised** → the recorded version makes it detectable;
records referring to an earlier version **remain valid and must not be rewritten**. A vocabulary is
**withdrawn** → the identifiers in existing records **remain the authoritative statement of what was
meant**; a community may declare a replacement with a mapping, **and the mapping need not be
complete** — *a partial mapping preserving what can be preserved is better than a rewrite that
silently changes what records assert.* A vocabulary **lacks a needed value** → declare a charter
extension.
**Requirement 7.4.** **Local values must be marked as local** and identify the defining charter; an
implementation **must not present a local value as though it were bound.**

---

## §8 Registration, attestation, signature

> **Requirement 8.1 (Attestation).** A transition **must record the party who performed the act and
> the party who registered it.** Where distinct, the transition **is attested**. The registering
> party's identifier **and a signature over the transition's content and parents** must be recorded;
> **registration by an unidentified party is forbidden.**
> *Satisfied by an act that costs the registrar very little — reading a proposed transition and
> confirming it. **The cheapness is required, not convenient**, since the registrar performs work whose
> benefit accrues to someone else.*

> **Requirement 8.2 (Independence of the registrar).** **No automatic registration on behalf of a
> party**, and **no party may hold another's credentials for the purpose of registration.** Where a
> transition is registered under a standing arrangement with the performer, **the arrangement must be
> recorded.**
> *Addresses the ordinary case of a supervisor routinely registering a student's transitions: the
> arrangement is legitimate and its effect on independence is real, **so it is recorded rather than
> forbidden.***

> **Requirement 8.3 (Signature coverage) — the single most likely implementation error.** A signature
> **must cover** content, parent identifiers, prior and posterior state identifiers, and disclosure
> class. A signature **must not cover fields a later lawful operation may alter**, and the
> implementation **must state which fields those are.**
> *Otherwise ordinary operation — scheduled release widening disclosure, redaction removing content —
> invalidates signatures, and implementations then either forbid the operation or ignore the
> invalidation. Both defeat the purpose.*
>
> ⚠️ *Note the tension: `disclosure class` is listed as covered here, while §12/§21 require class to
> widen without invalidating signatures. §21.5 resolves it in the git deployment by holding the class
> **in a separate file the signature does not cover** — the implementer must notice this. The
> implementation plan's field note ("Signature coverage **excludes** `disclosure`") follows §21.5.*

**Claim 8.4.** **An attestation asserts that an identified party registered a transition at a time.**
It asserts **nothing** about whether the change was an improvement, whether the claim is true, or
whether the registering party understood it. *Stated in the specification because implementations will
be tempted to present an attested transition as a verified one, and readers will make the inference
unaided.*

Three limits, recorded here because implementers must know them: credibility needs **≥2 parties**;
**collusion is made costly, not impossible**; and **counting is forbidden**:
> **Requirement 8.5 (No aggregation over attestations).** No **counts, depths, ratios or derived
> scores** over attestations may be computed, stored or presented as part of a conformant record.
> **Attestation is a property of an individual transition with two values.**

> **Requirement 8.6 (Marking of unattested transitions).** A transition whose performer and registrar
> are the same **must be recorded as unattested** and **presented as unattested wherever attested
> transitions are presented.** An implementation **must not describe a wholly self-registered
> trajectory as verified, corroborated or independently recorded.**
> *Protects the mechanism's meaning exactly where it would be diluted — **the personal tier is the tier
> most people will use first.***

**Requirement 8.7 (Withdrawal of an attestation).** **An attestation must not be deleted.** A registrar
who wishes to withdraw records a further **challenge** referencing the attested transition and stating
the ground; **the original remains in the log with the withdrawal linked to it.** *A reader sees both
the original act and its withdrawal — more informative than a deletion or a silent correction, and it
places the dispute in the record where later readers can weigh it.*

---

## §9 Attribution and absorption — credit without exclusion

**Requirement 9.1.** A transition **must record the performing party**; where several parties
contributed, **each with a CRediT role**. No contribution without a party; no party without a role
where more than one is present.
> **Attribution attaches to an act, not to a finished work.** *A contributor statement says a person
> contributed to a paper. **This record says which change in the content of a claim a person
> produced.***

**Definition 9.2 / Requirement 9.3 (Absorption).** Taking content from a state in one trajectory into
a transition in another. The **absorption link records: the identifier of the state absorbed from, the
identifier of the party who produced it, and the transition into which content was taken.**
**Implementations must present absorption links alongside the transition wherever it is displayed.**
> *This is what makes the difference between arrangements **visible in the record**: in an open
> competition unselected proposals are discarded and their content, where used, is used without trace;
> here it appears as an absorption link naming the party who produced it. **Whether a given arrangement
> absorbs or discards is checkable from its record — and the check is performed by readers, not by the
> protocol.*** (= Paper II's absorption test.)

> **Requirement 9.4 (No veto).** An absorption link confers **attribution and no right to prevent,
> condition or reverse the use of the content.** An implementation **must not provide a mechanism by
> which the named party can block a transition, require approval before absorption, or withdraw content
> already absorbed.**
> *Model: the moral-rights side of IP. Ground: avoiding the anticommons.*
> **Consequence for implementers:** *a party who does not wish their state absorbed has **one
> instrument — the disclosure class of that state**. Absorption operates on what has been disclosed to
> the absorbing party, and a party who discloses to a class has accepted that members of the class may
> build on the content with attribution.*

**Requirement 9.5 (Contested attribution).** A party holding that an attribution is wrong, or that an
absorption occurred **without a link**, records a **challenge** stating the ground. The disputed record
**must not be deleted or altered**; the challenge must be **linked to it and presented wherever either
is presented.** **The protocol supplies no procedure and no party empowered to resolve it** — the
record's contribution is that **both positions are visible with their dates.**

**Three limits fixed as constraints on what an implementation may claim:** attribution records that a
party **performed an act — not that they originated the idea** (independent arrival is not
adjudicated); an absorption link records **that content was taken, not how much it mattered** —
**no measure of influence may be computed or displayed**; and **the presence of absorption links does
not establish that the arrangement was generative** (necessary, not sufficient).

---

## §10 The graph: parents, divergence, synthesis, no merge

**Requirement 10.1 (Parent links).** ≥1 parent, except the trajectory-creating transition. **The graph
must be acyclic**; a transition whose parents include a descendant of itself **must be rejected.**
*Not a formality — cycles admit a history in which a state precedes and follows itself, and every
derived view, including the current state, becomes ill-defined.*
> **Ordering follows from the graph and not from timestamps.** Two transitions with no path between
> them are **unordered, whatever their recorded times**, and an implementation **must not present
> unordered transitions as though one preceded the other.** *Recorded times are evidence about when
> parties acted; they are not the structure of the history.*

**Definition 10.2 / Requirement 10.3 (No principal branch).** An implementation **must not designate
any branch principal, default, canonical or current**, and **must not order branches by any property
of content, size or activity.** Where a reader needs a single view, **the implementation must require
the reader to select a branch.**
*It may of course display branches in some order on a screen. What it must not do is **record or export
an ordering**, or present one branch with the marks of authority.*

**Definition 10.4 (Synthesis).** A transition carrying **≥2 parents from distinct branches**, producing
a state whose content the performer **composed** from what those branches reached. An ordinary
**transformation** with several parents. **The branches it draws on continue to exist and are not
closed by it** — a synthesis is a further state, not a resolution of the divergence.

> **Requirement 10.5 (No merge operation).** The protocol defines **no operation combining two states
> automatically.** An implementation **must not compute a combined state, must not present such a
> computation as a transition, and must not use the term *merge* for synthesis or for absorption.**
> *Ground: version control merges because changes to distinct text regions compose, a conflict can be
> localised, and a test decides whether the result works. **Two revisions of a concept satisfy none of
> the three.*** The terminological clause is practical: the substrate uses *merge* for an operation
> that does exist, and borrowing the word would make every implementer expect behaviour the protocol
> does not have.

**Requirement 10.6 (Identity is recorded, not adjudicated).** An implementation **must not determine
whether the states reached by two branches are versions of the same object.** Asked whether a later
state is a version of an earlier one, **it must answer with the chain of transitions connecting them —
and must not answer with a judgement.**
*Two consequences: a trajectory may hold several live branches indefinitely, **a normal condition and
not an unfinished one**; and a reader must choose among branches with no basis supplied — **a cost
stated here and not concealed.***

---

## §11–12 Disclosure

**Definition 11.1.** Classes **must exist, must be ordered by inclusion, and must be enforced**; their
**identity and membership are declared in a charter**. Two protocol-fixed properties: **ordering by
inclusion** (without it scheduled release has no meaning) and **opacity** — the implementation enforces
class values **without interpreting them**. *A community with two classes and one with six are both
conformant.*

**Definition 11.2 / Table 11.1 — the four grounds** (fixed, not extensible; see
[paper-III](paper-III-grounds-of-restriction.md) for the full analysis):

| Ground | Object restricted | Residue remaining disclosable |
|---|---|---|
| **rivalry** | access to the instrument or resource | **the trajectory in full** |
| **hazard** | the propagable content of a method | questions, decisions, interpretations, negative results |
| **exploratory vulnerability** | the timing of exposure | **everything, at the scheduled time** |
| **appropriability** | content whose disclosure destroys excludability | existence, questions, decisions, negative results |

> *The **rivalry row is the one implementers most often get wrong**: an instrument admitting one user
> at a time supplies **no reason to restrict the record of what was done with it**.*
> *Conditional access (structured access) is the mechanism the hazard row assumes.*

**Requirement 11.3 (Declared ground).** Any record disclosed at less than the widest class available in
its trajectory **must carry a declared ground**; an implementation **must reject a restriction that
declares none**, and **must present the ground wherever it presents the restriction**.
**Requirement 11.4 (Residue).** The corresponding residue **must be disclosed at the widest class
available**; a ground **must not be used to withhold material it does not cover**.
> *This is what makes the grounds do work. **A design without the residue rule would permit any ground
> to justify total silence — which is the present arrangement with a label attached.*** Misapplication
> is named (rent-seeking secrecy; hazard-where-no-propagable-risk). **The protocol cannot detect
> either** — the requirement that the ground be declared and displayed is what lets a reader raise the
> question.

> **Requirement 11.5 (Per-record disclosure).** A class attaches to an **individual record**.
> **Disclosure must not be a property of a repository, project or trajectory as a whole**, and records
> within one trajectory **must be able to carry different classes.**
> *This is the second point at which the version-control analogy fails: in a VCS openness is a property
> of a repository chosen by its owner. Research requires that a single line of work carry states
> disclosed to everyone, to a group, and to nobody, with the differences declared and grounded.*
> **Consequence for views:** a view must be computed **over the records that reader may see**, and an
> implementation **must not disclose the existence of a record by omission, ambiguity, or a gap in
> numbering** where the charter requires existence to be concealed.

**Left to the charter:** which classes exist and who belongs · consent and retention · **who may change
a record's class** (the change is an administrative operation; *who may perform it is a charter
question, and the record makes the answer visible after the fact*).

### §12 Monotone disclosure and release

**Requirement 12.1 (Monotone disclosure).** **Disclosure may widen and must not narrow.** No operation
reducing the class of a disclosed record, **and no representation that such a reduction occurred.**
*Ground: a reduction **cannot be effected** — a party who has read a record retains what they read, so
an operation appearing to withdraw disclosure **conceals from the record's own participants a state of
affairs obtaining outside it**, and the implementation would then be trusted with material that should
never have been entered.*
Two operations that resemble narrowing and are distinguished: **redaction** (removal from the store,
not a change of class — §13) and **revocation of a party's class membership** (a charter matter about
*future* disclosures; it does not alter what was already disclosed).

**Requirement 12.2 (Restrictive default).** Records are created at **the most restrictive class
applicable under the declared ground** and widen **only by an explicit act**. **No widening as a side
effect of any other operation.** *Where disclosure cannot be undone, an error toward openness is
uncorrectable — and defaults are where such errors occur.*

**Definition 12.3 / Requirement 12.4 (Scheduled release).** A recorded commitment that a record will be
disclosed at a stated wider class at or after a stated time; **the schedule is part of the record and
is disclosed at the record's current class.** An implementation honouring it **widens the class at the
stated time without a further act by any party.** **A schedule may be shortened; it must not be
extended or cancelled**, and **any attempt must be recorded as an administrative operation with its
ground.**
*The asymmetry is the substance: vulnerability justifies delay and not permanent withholding, and a
schedule extendable indefinitely is a permanent withholding made to look temporary. The attempt is
recordable because a charter may sometimes allow it — and it must be visible.*

**Definition 12.5 / Requirement 12.6 (Release).** A release records the state identifier, the class,
the time, **and the identifiers of every transition referencing that state whose disposition is
`unresolved` at that moment.** It **must enumerate the standing objections**; an implementation **must
not omit them, must not permit a release conditional on their resolution, and must not present a
release as certifying, validating or approving the state.**
> *The point at which this specification differs most visibly from publication as practised. **A
> release asserts that a state is published and that these objections stand.** It asserts nothing about
> their merit — and a community treating an enumerated objection as a defect will produce releases with
> the objections suppressed, **which is a failure of the charter and not of the protocol.***
A release is also **what serves priority** (it carries a time and a registrant) — *the protocol
supplies the record and cannot supply the recognition.*

> **Requirement 12.7 (Emission on release) — discharges the compatibility condition.** An
> implementation **must be able to emit, from a release, a document containing: the released state,
> the chain of transitions leading to it, the parties with their contributor roles, the absorption
> links with their attributions, and the objections standing at release.** The emitted document
> **must carry the identifier of the release it was generated from.**
> *A participant obtains, **without additional work**, an object of the kind the incumbent reward system
> accepts, **carrying an appendix no other process can produce**. **Adoption does not require anyone to
> abandon publication.***

---

## §13 Separability, redaction, integrity

Resolves the conflict that defeated comparable systems: an append-only log with content-derived
identifiers cannot admit deletion, and a record holding personal data must.

**Definition 13.1.** **Skeleton** = identifier, kind, parent links, state references, typed fields,
parties, signature, disclosure class and ground. **Content** = the material referred to: the text of a
state, a recording, a transcript, an annotation body, a deposited file.
**Requirement 13.2 (Separability).** **Content stored separately, referenced from the skeleton by a
content-derived identifier. A skeleton must remain valid and verifiable when the content it references
has been removed.** *The signature covers the skeleton, which includes the content identifier; removing
content does not alter the skeleton, so the chain of identifiers and signatures stays intact and every
later record remains verifiable.*

**Definition 13.3 / Requirement 13.4 (Redaction).** Removal of content while the skeleton remains.
**A redacted record continues to assert that a transition occurred, by whom, of what type, at what
position in the graph — and no longer supplies what was said.** The redaction **must be recorded as an
administrative operation** carrying the redacted record's identifier, the time, the performing party,
and the ground. **A skeleton must not be removed. The record of a redaction must not be removed.
Redacted content must not be represented as never having existed.**
*The last clause is the substance: a system erasing the trace of an erasure would leave a record that
**misdescribed its own history**, making every later reader's inference unreliable in a way they could
not detect.*

**Three things survive and must all be presented:** the fact of the transition with its type, graph
position and date · **the parties**, unless the ground requires their removal — *in which case the
skeleton records that a party field was redacted, and the signature over the skeleton is preserved with
the party identifier replaced by its own content-derived identifier* · **the fact that a redaction
occurred, with its ground**, so a reader finding an unreadable antecedent knows why.
**Requirement 13.5 (Structural preservation).** **A redaction must not alter the graph.** Parent links,
state references and the induced ordering **survive unchanged**; a record **must not be removed because
its content was removed.**

**Requirement 13.6 (Propagation of redaction).** An implementation that received records **must accept
and act on a redaction notice** for them and **must forward such notices onward**, and **must record
notices received and forwarded.**
**Two honest limits:** *a copy held by a departed party cannot be reached, and no protocol reaches it*;
and derived objects (emitted documents, cached views) may embed content a later redaction removes — the
implementation **must reconstruct affected caches and must record which emitted documents referenced
redacted content**, so a party can pursue them outside the system.

**Three further limits.** **Possibility is not lawfulness.** **Content-derived identifiers of removed
content remain in the skeleton** — where content is short and its space small, the identifier may permit
**reconstruction by exhaustive search**, so an implementation handling such content **must apply a
per-record secret before computing the identifier.** And **a redaction is visible** — a participant who
removes their material leaves a record that they did so, with a ground. *This is the price of a
tamper-evident log; it cannot be avoided within one; **and participants should be told before they enter
rather than after they attempt a removal.***

---

## §14 Identity

**Definition 14.1.** A **party** is an entity capable of performing and registering acts, **identified
within the protocol by a public key.** Nothing requires that a party correspond to a natural person,
that a natural person hold one identifier, or that an identifier connect to a legal name.
**What is required is continuity.**
**Claim 14.2.** Attestation and attribution **require continuity of identity and do not require legal
identity.** A key pair establishes that the registering party is distinct from the performing party,
and that the same party acted last week — **which is the whole of what §8 and §9 depend on.**

> **Requirement 14.3 (Pseudonymous participation).** An implementation **must permit a party to
> participate under a key not bound to any external identifier, at every conformance tier**, and
> **must not require a legal name, telephone number, institutional affiliation or government
> identifier** as a condition of holding a party identifier.
> *Three reasons, the second the one the series cares about:* the mechanisms don't need it; **a
> universal identity requirement excludes exactly the population the companion papers concern** —
> unaffiliated scholars, parties in jurisdictions where a phone number is a state-linked identity
> document, parties whose participation carries risk — **and the entry path would be closed at the
> door**; and the empirical record for real-name policies is **exclusion without the improvement in
> conduct they were introduced to secure.**

**Definition 14.4 / Requirement 14.5 (Optional bindings).** A **binding** is a recorded, verifiable
association between a party identifier and an external identifier (researcher ID, institutional
account, domain, attested legal identity), recorded as an **administrative operation** carrying the
attesting party. Bindings **must be visible wherever the party identifier is presented, must record who
attested and when, and must be revocable by a further recorded operation.** An unbound identifier
**must not be presented as bound**; a revoked binding **must not be presented as current.**

> **Requirement 14.6 (Assurance by class and not by gate).** A charter may require a stated assurance
> level **for participation in a given disclosure class or for acts of a given kind**. An implementation
> **must enforce it at the point of the act** and **must not apply it as a condition of holding a party
> identifier or of reading records disclosed at the widest class.**
> *A community handling hazard-restricted material may reasonably require a verified institutional
> identity for that class. **The same community must not require it of a stranger who wishes to
> challenge a publicly disclosed claim** — that is the act by which parties without position enter, and
> gating it reproduces the bootstrap failure the design exists to avoid.*

**Requirement 14.7 (Key lifecycle).** **Rotation:** an administrative operation **signed by the old
key** nominating the new one; both identifiers then refer to the same party and **prior records remain
valid under the old identifier**. **Loss:** a new identifier plus a **charter-defined procedure**; the
implementation **must record which procedure was used and must not represent such an association as
equivalent to one signed by the old key** — *recovery procedures are necessary and weaker than a
signature, and a record presenting them identically would misdescribe the strength of its own
evidence.* **Compromise = revocation with a date**; registrations made before it **remain in the log,
marked with the compromise** — *removal would alter the graph and conceal the history the record exists
to hold.*

---

## §15 Sealed registration

**Definition 15.1.** A record carrying the **content-derived identifier of a state**, the registering
party identifier, a time, and a signature — **with the content disclosed to no party.** It asserts that
the registering party **held content with that identifier at that time.**
> *Requires nothing the specification does not already have: a sealed registration **is the skeleton of
> a record whose content has not been disclosed**, not a new kind of object.*

**Requirement 15.2.** Registration **must be available at every disclosure class, including the class
disclosing to no party beyond the performer.** A party **must be able to record a trajectory from its
first state without disclosing any content**, and **disclosure must not be a condition of
registration.**
**Definition 15.3 / Requirement 15.4 (Opening).** A transition disclosing previously sealed content,
recording the sealed registration's identifier and the content, so **any party may verify from the
record alone that the content yields the identifier registered earlier.** Verification failures **must
be recorded, and neither record removed.** *Opening is optional and may never occur — a party may seal a
trajectory and abandon it, and the sealed registrations remain as evidence of what was held and when,
unopened and unverifiable by anyone.*

**Claim 15.5.** It **converts the choice between disclosing early and recording nothing into a choice
about when to disclose.**

**Five limits.** Evidences **possession, not understanding** (a party may register a state they do not
comprehend). **Generates nothing** — a sealed state attracts no objection, no connection, no encounter;
*it protects a participant during precisely the phase in which the arrangement's benefits are
unavailable to them, and it purchases the possibility of opening later.* **Adjudicates nothing against
independent arrival.**
> **Requirement 15.6 (No inference from precedence).** An implementation **must not present an earlier
> sealed registration as establishing that a later party derived their work from it**, and **must not
> rank, order or annotate parties by the times of their sealed registrations.**
> **Requirement 15.7 (Statement of the limit).** An implementation **must not describe sealed
> registration as establishing priority**, and **must describe it as recording that a party held a
> content at a time.** *Where a community honours registration for priority, the honouring is recorded
> in the charter and not in the protocol.*

**Dependence outside the protocol (easy to overlook):** a sealed registration is evidence **only if its
time is credible to a party who does not trust the registrant.** An implementation **must anchor sealed
registrations in a manner a third party can check** — publishing identifiers at intervals in a medium
it does not control, or obtaining a timestamp from an independent party (Haber & Stornetta 1991) —
**and must record which method was used.**

---

## §16 Propagation

**Definition 16.1.** **Lateral propagation** = an objection raised against one trajectory entering
another, and absorbed content moving across a divergence with its attribution.
**Inter-implementation propagation** = exchange of records between implementations sharing no operator
(COAR Notify, ActivityPub). **Dissemination of finished artefacts is excluded from the term** —
repositories and indexes do it adequately and nothing here concerns it.

> **Requirement 16.2 (The exchange minimum).** Two implementations exchanging records **must agree on**:
> the **record structure** (§6) · the **act and disposition vocabularies** · the **identifiers of bound
> vocabularies in use and their versions** · **the construction of content-derived identifiers** ·
> **the signature scheme.**
> **They need agree on nothing else** — not storage, transport, interface, or serialisation.
> *The identifier-construction and signature-scheme clauses **cannot be relaxed**: two implementations
> computing identifiers differently produce records that cannot be verified across the boundary, and
> **the record's credibility does not survive the crossing.***

**Requirement 16.3 (Declaration of profile).** An implementation **must declare, machine-readably**:
protocol version, conformance tier, identifier construction, signature scheme, bound vocabularies with
versions. **A receiving implementation must record the declaration under which records were received.**

> **Requirement 16.4 (Continuation) — portability is not export.** A participant **must be able to
> obtain the complete record** (transitions, skeletons and signatures, attributions, absorption links,
> parent structure) **without the permission of any position holder**, and **must be able to continue it
> under an implementation the original operator does not control.** **Transitions appended after
> continuation must reference the obtained transitions as parents, so the continued trajectory is one
> graph and not two.**
> Two consequences: identifiers **must continue to resolve** (*a continuation whose references have
> become unresolvable is an archive, not a trajectory*); and **restricted content does not travel unless
> the receiving implementation can honour the class** — transfer the class and ground and honour them,
> **or transfer only the skeleton and record that content was withheld.**

**Requirement 16.5 (Received records).** **Verify what can be verified; retain what cannot, marked
unverified; never alter received records.** Unrecognised vocabulary values are **retained unchanged**.
> *The prohibition on alteration **extends to normalisation**. An implementation rewriting received
> records into its preferred form would invalidate their signatures and destroy the property that makes
> propagation worth having.* Redaction notices are the one exception (§13).

**Four failure cases.** **Version mismatch** — retain, do not process as own version; where versions
differ only in additions, process recognised fields **and record that it did so**. **Vocabulary drift**
— each record carries its own version; **no reconciliation by the protocol**. **Partial records** —
retain the subgraph, **mark missing parents as unresolved references**, **do not synthesise missing
transitions or present the subgraph as complete**. **Divergent continuation** — two parties continuing
the same obtained record independently is **a divergence and is treated as one**: both retained, neither
principal, shared ancestry visible in parent links. **No reconciliation is required and none is
provided.**

---

## §17 Durability

**Requirement 17.1 (Self-describing formats).** The **authoritative** form of a record **must be a
plain, self-describing serialisation readable without the software that produced it**, in a publicly
specified format. **It must not be held only in a database, index, or proprietary container.**
*Any internal representation is permitted for speed — what is forbidden is that the internal
representation **be** the record, since a record recoverable only through a running system is lost when
the system stops running, **and systems stop running.***
**Requirement 17.2 (Field documentation).** Publish, alongside the records, the **vocabularies and
versions used and the construction of identifiers and signatures**, in a document readable **without
access to the implementation.** *Addresses a failure visible only after it is irreparable: a
serialisation that is readable but uninterpretable, because the meaning of its fields lived in a
codebase, is **a durable record of nothing.***

**Definition 17.3.** **Custody is held by a party and not by a system.**
**Requirement 17.4 (Distributed custody).** At the **group and open tiers**, a record **must be held by
at least two parties who do not share an operator** (LOCKSS-style replicated independent custody); the
implementation **must record which parties hold copies** and make the record obtainable under Req. 16.4.
*What makes portability meaningful in practice — a right to obtain a record from a party who has ceased
to exist is a right without an object.*
**Requirement 17.5 (Archival deposit).** At the **open tier**, **released states and the transitions
leading to them** must be deposited with an **independent** archival service with stated preservation
commitments; **the deposit identifier is recorded in the trajectory.**
*Restricted to **released** material deliberately — **depositing sealed or restricted content with a
third party would place material outside the disclosure regime governing it.***
**Requirement 17.6 (Succession).** An organisation-operated implementation **must publish what becomes
of its records if it ceases to operate** — to whom custody passes, with which archival service material
is deposited, or how participants may obtain the records. **An implementation must not claim durability
without publishing such an arrangement.**

**Three limits:** a specification **cannot fund preservation**; **cannot compel a departed party** to
keep a copy; and format stability is a matter of degree — *what is secured is that the difficulty is one
of **interpretation** rather than of **recovery**.*

---

## §18 Operating charters — the Level-1 interface

**Definition 18.1.** An identified, **versioned** document adopted by a community, which **the protocol
references and interprets nothing in.**
> **The charter is where everything contested lives:** which classes exist and who belongs · consent
> before a record concerning a person is created · retention · conduct and consequences of breach ·
> identity assurance per act · **whether registration is honoured for priority** · review templates ·
> declared target/trigger extensions.

**Requirement 18.2 (Minimum charter content) — a condition of legibility, not a normative demand.** A
charter referenced by a conformant record **must state**: the disclosure classes and their ordering ·
the parties/roles belonging to each · the assurance level required per class and per act kind · any
extended target/trigger values with definitions · **the procedure by which the charter itself is
amended.** **An implementation must reject a record referencing a charter that does not state these.**
*It obliges a community to have decided its own questions and settles none of them.*

**Requirement 18.3 (Charter reference).** A trajectory **must record the charter identifier and
version**; any record whose class, assurance requirement or extended vocabulary value derives from a
charter **must record that charter's identifier and version.**
**Requirement 18.4 (Amendment is prospective).** An amendment **applies to records created after it and
must not alter the interpretation of earlier records.** Earlier versions must be retained or locatable.
> *One case implementations will handle badly:* **where an amendment removes a disclosure class,
> records already carrying it retain it, and the implementation must continue to enforce the class as
> the earlier charter defined it.** Reclassifying would either widen without an act (forbidden by 12.2)
> or narrow (forbidden by 12.1).

**Three refusals:** no model charter, no default charter, **no minimum standard of conduct** (*a
specification supplying one would be a specification of governance, and communities rejecting the model
could not conform*) · **no enforcement of charter provisions beyond the fields the protocol carries**
(classes are enforced because they are protocol fields; conduct rules are not) · **no adjudication
between a charter and law.**

---

## §19 Amendment and versioning — *the specification applied to itself*

**Definition 19.1.** A version is **compatible** with an earlier one where every record valid under the
earlier is valid under it **and carries the same meaning**; otherwise **incompatible**.
**Requirement 19.2.** Every record **must carry the protocol version under which it was created**. An
implementation **must not alter the version identifier of a record it did not create, and must not
upgrade records to a later version.** *A record created under one version asserts what that version's
fields meant; rewriting it would silently change what it asserts.*
**Protocol versions, implementation versions and charter versions are distinct** and must not share a
numbering.

> **Requirement 19.3 (Recorded amendment).** An amendment to the specification is **proposed, discussed
> and adopted through a record conforming to the specification**: *a proposal is a **state**; objections
> are **challenges**; revisions are **transformations**; adoption is a **release at the widest class**.*
> **The trajectory of the specification must be publicly readable and must remain so.**
> *Practical effect beyond the reflexive demonstration: a reader can see which objections were raised
> against a provision, which were answered, and **which stood unresolved at adoption** — Req. 12.6
> obliges the release to enumerate the last.*

**Requirement 19.4 (Custodial separation).** The party maintaining the specification **must not be the
operator of any implementation for which conformance confers advantage — or must record the conflict
and the arrangements limiting it.** The specification **must be licensed so any party may fork it, and
conformance to a fork must be expressible in the version identifier.**
**Requirement 19.5 (Declaration).** Declare the versions readable and the version records are created
under; on exchange, **each records the other's declared versions.**
> **Negotiation is minimal by design: no translation, no negotiation of a common subset, no downgrade**
> — each would produce records asserting something other than what their creators asserted.

**Three limits.** Procedure **does not confer quality**. **The procedure is itself capturable** — a
party controlling participation in the specification's trajectory controls the specification, and **no
clause within it prevents this**; the bound is **the licence to fork and the portability of the
specification's own record — the same partial bound placed on every other position.** And **an
amendment cannot repair a record** — for each incompatible change the specification **must state what a
reader should understand about records created earlier.**

---

## §20 Conformance tiers

**Cumulative**: conforming at a tier satisfies every requirement of the tiers below.

| Tier | Adds | Available to its adopter |
|---|---|---|
| **Personal** | transitions with parent links + identified prior states · append-only log with derived views · **three acts minimum: `claim`, `challenge`, `release`** · content separable from skeleton | a searchable record of what was ruled out and why · a list of objections not yet answered · **a citable release with its chain** |
| **Group** | attestation by a distinct party · contributor roles · absorption links · disclosure classes with declared grounds · administrative operations recorded | **evidence — credibility begins where a second party registers** · visible attribution of changes · onboarding a new participant from the record |
| **Open** | propagation with declaration of profile · distributed custody · archival deposit of released material · charter reference · identifier resolution independent of the operator | exchange with parties elsewhere · continuation beyond the operator · **entry of strangers through the open register** |

**Requirement 20.2 (Minimal implementation).** The personal tier **must not require** attestation,
contributor roles, disclosure classes, charters or propagation.
**Requirement 20.3 (Marking of the personal tier).** **Every transition marked unattested**, and the
absence of attestation **stated wherever a record is presented or exported.** **Must not describe a
personal-tier record as verified, corroborated or independently recorded.**
> *The honest position: **the personal tier delivers utility and no evidential weight**, and the two must
> not be confused at the point where most participants meet the protocol first.*

### The three conformance tests (for the exclusions most likely to be violated in good faith)

> **Requirement 20.4 — scalar test.** Fails where it **computes, stores, displays or exports any total
> order or numeric measure over participants or over trajectories**, including counts of transitions,
> counts of attestations, contribution shares, activity indices and derived scores.
> **Counts of records within a single trajectory, presented without comparison across participants or
> trajectories, do NOT violate this.**
>
> **Requirement 20.5 — independence test.** Fails where any conformant operation cannot be performed
> without an analytical capability. **The test: can the record be created, registered, read, verified,
> exported and continued using a text editor and a version-control system?**
>
> **Requirement 20.6 — byproduct test.** Fails where it requires an act whose only purpose is that a
> record should exist. **The test: does each required act have a purpose *for the party performing it*
> that is stated in the implementation's documentation?**

**Requirement 20.7 (Self-declaration).** Publish a declaration stating protocol version, tier,
identifier and signature constructions, bound vocabularies with versions, the substrates supplying
storage/identifiers/transport, and (at open tier) the succession arrangement. **Readable without access
to the implementation.**
> **Conformance is self-declared and checkable from the record. No certification body is established
> here and none is required** — a doubting party obtains a record under the continuation requirement and
> verifies signatures, identifier construction, and the presence of required fields.

**Three limits on a conformance claim:** it concerns **the implementation and not the records it holds**
(*a conformant implementation may hold a fabricated trajectory*) · it concerns **structure and not
quality** · at the open tier it establishes **capability, not that exchange has occurred.**

---

## §21 A deployment over version control (NON-NORMATIVE — Requirement 21.1)

*Included because a specification with no worked deployment invites the reply that it cannot be
implemented; excluded from the normative text because **a deployment ages faster than a specification
and should not date it.***

**The mapping.** A **trajectory is a repository**. A **transition is a commit**; its **skeleton is a
plain text file** added by that commit. **Content is in separate files**, referenced by the VCS's own
content identifiers — *so the separation required for redaction is the substrate's ordinary behaviour*.
**Parent links are the commit's parents; acyclicity is the substrate's.** A **synthesis is a commit with
several parents and is not a merge in the substrate's sense** — no automatic combination is performed.
**Signatures are commit signatures**; **attestation is expressed by a commit whose signer differs from
the skeleton's `performer` field**, and the implementation enforces the distinction by **refusing
commits where the two coincide at group tier and above.**
**Event plane:** held **outside** the trajectory repository, in the systems participants already use
(calendar, meeting recorder, message archive, working code repo). The implementation reads them,
proposes candidates, **and writes nothing to the trajectory until a party registers one**. *The privacy
requirement is satisfied by the arrangement rather than by a mechanism — the event plane is never copied
in, so publishing a trajectory discloses no event record.* What is disclosed is a **trigger reference**
in a registered transition.
**Disclosure:** **one repository per class**, with restricted records held in narrower-access
repositories and **referenced from the wider ones by identifier alone** — a reader at a wide class sees
*that* a record exists without seeing its content.
**Propagation** is clone and fetch; **the profile declaration is a file in the repository**.
**Deposit** is transferring an archive of the repository at a release to a service issuing a persistent
identifier, **recorded in a subsequent administrative operation**.

### The four weaknesses (stated because a reader will otherwise assume the mapping is clean)

1. **Disclosure is per repository; the spec requires per record.** One-repo-per-class **approximates and
   does not meet** Req. 11.5 — a record whose class changes under a scheduled release **must be moved
   rather than relabelled**, and the movement is visible in a way relabelling would not be. **The
   movement must be recorded as an administrative operation.**
2. **Identifier resolution depends on hosting.** The substrate's content identifiers are stable and
   **not resolvable by a party who does not hold a copy** — so **resolvable identifiers must be obtained
   from a repository service for every state referenced from outside**, with the correspondence recorded.
3. **Redaction is available and not simple.** Removing a content file from the working tree **leaves it
   in the history** — so redaction needs history-rewriting, **or** a design in which **content files are
   held outside the versioned tree and referenced by identifier. The second is preferable and is what
   the mapping above assumes.**
4. **Signature coverage is fixed by the substrate.** Commit signatures cover the commit content,
   **including the skeleton file with its disclosure class — so the class cannot be widened by a
   scheduled release without invalidating the signature.** The workable arrangement **records the class
   in a separate file the signature does not cover**, which satisfies Req. 8.3 **and requires the
   implementer to notice the problem.**

---

## §22 Three worked examples (constructed, not observed — they establish nothing empirical)

**Mathematics (Case 22.1) — an obstruction and an entering stranger.** question → claim → transformation
(trigger `reflection`) → verification recording the failure (an independence assumption does not hold) →
**decision abandoning the approach, with the reason** → a state recording the current obstruction,
disposition `unresolved`. Months later, **a party with no prior act finds it through the open register**
and records a **connection** to a construction in another field where the same obstruction was met; the
participants accept; a **transformation** follows, **registered by a party other than its performer**;
the entering party is recorded as performer of the connection with a contributor role.
*Exercises: the open register, the entry path, attestation, the decision act.* **Shows what the decision
act is for** — the abandoned approach is interpretable years later **only because the reason was recorded
with it**, and the connection was possible **only because the obstruction was addressable as a state**.
*At the personal tier the same trajectory is recordable, carries no attestation, **and the entering party
has nothing to find.***

**Machine learning (Case 22.2) — an evaluation failure and a restricted method.** Hypothesis + method
state → verifications (trigger `experiment`), one with an unpredicted outcome → **challenge registered by
a member who did not propose the hypothesis**, disposition `accepted` → transformation, relation
`modification`. **Part of the method is held at a restricted class on the appropriability ground**; the
**residue is disclosed at the widest class**: existence, question, decisions, **the evaluation outcomes
that failed**, and the revised hypothesis. A **scheduled release** is recorded for the restricted state.
**A second group absorbs the abandoned first hypothesis with its recorded failure, and the absorption
link credits the originating party.**
*Shows the residue rule doing the work it exists for: **the group withholds what excludability requires
and discloses everything the ground does not cover — which is what makes the abandoned hypothesis
available to the second group at all.***

**Philosophy (Case 22.3) — a divergence that is not resolved.** trust-between-individuals → challenge
(omits institutional power), accepted → transformation → **a third party challenges the revised state on
different grounds; neither accepted nor rejected — disposition `unresolved`, and work proceeds** → **two
transformations diverge**: one narrows to institutional settings, one keeps general scope and weakens the
claim; **neither designated principal** → a later **synthesis** references both as parents, **and the
branches continue** → a **release on the narrowed branch enumerating the unresolved challenge as
standing**, with an emitted document carrying state, chain, contributors and the standing objection.
> *The case where the specification differs most sharply from publication as practised: **the released
> document declares an objection its author has not answered.***

**Three findings common to all three:** every act has a purpose for its performer — *nobody documents in
order to document* · **the requirements exercised differ by field and the tiers accommodate the
difference** (philosophy needs no classes; ML needs classes and the residue rule; mathematics needs the
open register and entry path) · **the demanding part is the same in all three: recording a decision with
its reason at the moment of abandoning a direction.** *It is work with no present incentive, on which the
reuse of abandoned material nevertheless depends. **The specification makes the act cheap and cannot make
it attractive** — a limit of a protocol.*

---

## §23 Failure modes and attacks

**Of the record.** **Collusive fabrication** — cost rises with the number of independent registrars and
the visibility of their other work; **not eliminated; an implementation must not describe an attested
record as proof of authenticity.** **Retroactive alteration** — content-derived identifiers over payload
and parents invalidate every descendant, **so detectable by any holder of a copy**; where a party holds
the only copy, detection requires a second custodian (Req. 17.4, group tier and above). **Backdating** —
**signatures do not establish time**; the §15 anchoring moves the question to a party the registrant does
not control; **without anchoring, recorded times are assertions.** **Flooding** — no rate limit and no
quality condition; the bearing mechanisms are indirect (attestation requires recruiting a registrar; the
scalar exclusion removes the reward for volume); **rationing of attention is a charter matter.**

**Of position.** **Registrar gatekeeping** — the protocol records the declining party's other
registrations and **supplies no remedy**; the charter responds, and **portability bounds the position**.
**Custodial capture** — **the continuation requirement is the test**, and an operator refusing it is
non-conformant; **the protocol cannot compel compliance**, and recourse is the copies under distributed
custody. **Capture of the specification** — **no clause prevents it**; bounds are the licence to fork and
the portability of the specification's record, **which are partial.**

**Of disclosure.** **Misapplied grounds** — declared and displayed, **not assessable by the protocol**;
detectable by readers, corrected (where it is) by the community. **Disclosure by inference** — *a
record's existence revealed by a gap, an identifier sequence or the shape of a derived view.*
**Implementations must compute views over the records a reader may see and must not disclose existence by
omission where a charter requires concealment. A genuine implementation hazard, easy to introduce
accidentally.** **Redaction that cannot reach** a departed copy. **Reconstruction from an identifier** —
answered by the **per-record secret**, applied before the identifier is computed, **which an implementer
must decide in advance.**

**Of the arrangement.**
> **Surveillance through the event plane.** *The plane that makes capture cheap is a monitoring log.*
> The privacy requirement confines it to participants and forbids export and indexing, and an
> implementation violating it **would produce exactly the instrument the design exists to avoid.**
> **This is the failure with the largest consequence for participants and the one an implementer is most
> likely to introduce while improving a feature.**

**Scores at the edge** — the protocol **forbids the implementation from computing one and cannot forbid
third parties**; a widely adopted external score would reintroduce the dynamic the exclusion prevents.
*The protocol's only contribution is that **it supplies no such quantity itself and no privileged basis
for one**.* **Reflexive confirmation** — registration becomes a habitual click; **the affirmative-act
requirement is the answer and is weak**; what strengthens it is a charter under which registering
carelessly is a recognisable failure, **and the record shows who registered what.**

**Three failures with no technical answer** (*stated so that no reader mistakes the specification's
silence for a solution*):
1. **A community that punishes disclosed failure will produce records with the failures removed** — and
   the reuse of abandoned material, one of the two concrete benefits claimed, **will not occur.**
2. **A community that does not honour registration** leaves sealed registration supplying evidence to
   parties with no forum in which it counts.
3. **A community in which nobody registers another party's transitions will operate at the personal tier
   under a group-tier declaration** — records whose marking is correct and **whose evidential value is
   absent.** *The protocol makes the condition visible and does nothing further.*

---

## §24 Boundaries and open issues

**Five refusals.** It does not **assess content** · does not **measure capacity** (a trajectory records
what occurred, not what the relation could have produced, and what it records is the articulable fraction
alone) · does not **resolve disputes** (contested attribution, withdrawn attestation, disputed grounds are
all recorded, and **no party is empowered by the specification to decide any of them**) · does not
**guarantee lawfulness** (it makes lawful operation *possible* where an unredactable record would
foreclose it) · **does not produce encounters** — *it records them and makes states addressable so a party
elsewhere may find one; **whether such finding occurs is a matter of adoption, scale and community
behaviour, on which the available evidence is discouraging.***

**Four open engineering questions:** per-record disclosure over per-repository substrates (*a substrate
supporting per-object access with cryptographic enforcement would settle it*) · **resolvable identifiers
at state granularity, cheaply** (presently expensive) · redaction across implementations that no longer
communicate · **representation of a state for structural matching across vocabularies** (*the capability
the cross-field claim depends on; the specification supplies a substrate and claims nothing about it*).

**Three open normative questions no specification can settle:** whether **registration is honoured for
priority** · whether **disclosed failure can be non-punitive** — *on which the reuse argument depends
entirely* · whether **the labour of registering another party's transitions is recognised** — *unpaid work
for another's benefit, the disparity that defeated every comparable system.*

> **Four findings that would show the specification inadequate:**
> 1. **Personal-tier adoption without progression to the group tier**, over a substantial population and
>    period → the arrangement supplies private utility and **does not produce the attested records on
>    which every evidential claim rests.**
> 2. **Records in which the `decision` act is rare while transformations are common** → the act on which
>    reuse depends is not being performed, and **making it cheap was insufficient.**
> 3. **Group-tier declarations alongside registration patterns of pairs who register only each other** →
>    **attestation operating as a formality.**
> 4. **A widely used external score computed over conformant records** → **the exclusion of scalar
>    measures displaces the dynamic rather than preventing it.**

**Status:** version 0.1. **No implementation, no deployment history, no evidence of use, and every
requirement in it is a proposal about what such use would need.**

---

## Implications for this repository

- **The tool's UI vocabulary must follow the eight acts, not invented ones** — and must never say
  "commit" for a transition or "merge" for a synthesis/absorption (Req. 10.5).
- **Every command's `--help` must state the purpose it serves *for the person running it*** — this is
  literally the byproduct conformance test (Req. 20.6), and the implementation plan already encodes it as
  an acceptance test.
- **`grrp check` should implement Req. 20.4/20.5/20.6 directly** as the three conformance tests, plus the
  append-only, signature-coverage, redaction, attestation and portability tests already in the plan.
- **Signature coverage is the named "single most likely implementation error"** — spec §8.3 vs. deployment
  §21.5. Follow §21.5: hold the disclosure class in a separate, uncovered file.
- **The personal tier must mark everything unattested and say so on every export** (Req. 20.3) — a plain
  requirement the current README does not reflect.
- **Emission on release (Req. 12.7) is not a "later stage" nicety** — it is the compatibility mechanism
  that makes adoption possible at all. It belongs in M1.
- **`grrp open` implements Req. 6.5** (the open register). It is the entry path, and Paper I §17 makes it
  the answer to the bootstrap failure.
- **The four "findings that would show the specification inadequate" are this project's evaluation plan.**
  In particular: *watch the ratio of `decision` acts to transformations*, and *watch for
  register-only-each-other pairs*.

Related: [paper-I-design-and-requirements.md](paper-I-design-and-requirements.md) ·
[paper-II-incentives-and-adoption.md](paper-II-incentives-and-adoption.md) ·
[paper-III-grounds-of-restriction.md](paper-III-grounds-of-restriction.md) · [glossary.md](glossary.md)
