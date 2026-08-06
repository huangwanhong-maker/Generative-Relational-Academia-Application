# Notes on the GRA papers

Working notes taken while reading the four papers in [papers/](../papers/). They are dense on purpose:
the intent is that these files can be used **instead of** re-reading 217 pages of PDF, and that any
claim made in this repository can be traced back to the paper and requirement that licenses it.

Quotation is used heavily where the papers' own wording is the point — several of the design rules are
stated as *"an error to be corrected"* or *"the single most likely implementation error"*, and
paraphrase loses their force.

## Files

| File | What it holds |
|---|---|
| [paper-I-design-and-requirements.md](paper-I-design-and-requirements.md) | The problem, the survey of prior art, the derivation, and **the sixteen requirements (R1–R16)**. Start here. |
| [paper-II-incentives-and-adoption.md](paper-II-incentives-and-adoption.md) | Why any of this might not happen. The commons dilemma, the positional bound, **the absorption test**, the dominance argument, **ten predictions with refuting observations**. Mostly a list of things the project may not claim. |
| [paper-III-grounds-of-restriction.md](paper-III-grounds-of-restriction.md) | Disclosure. **Four irreducible grounds, each with an object, a residue, and a named failure.** The residue rule. The shared component of value, evidence and hazard. |
| [paper-IV-grrp-specification.md](paper-IV-grrp-specification.md) | **GRRP v0.1 — the normative specification.** Record model, act vocabulary, attestation, absorption, graph, disclosure, redaction, identity, propagation, durability, charters, amendment, **conformance tiers and tests**, a git deployment, worked examples, failure modes. |
| [glossary.md](glossary.md) | Every fixed term with the definition and citation. Use this when writing anything user-facing. |
| [gaps-and-repo-actions.md](gaps-and-repo-actions.md) | Where this repository currently diverges from the papers, what to change, and what is still the user's decision. |

## The shortest possible summary

Scholarly communication transmits finished artefacts and discards **the trajectory** that produced them.
An artefact carried evidence about its producer only because producing it was costly *in a way that
discriminated between producers*; that discrimination is weakening. So attention moves to the trajectory
— but **a trajectory record is as cheaply fabricated as the artefact whose function it would inherit**.
Its credibility can therefore only come from **distribution across parties who did not coordinate**,
which is why this is a **protocol** and not a platform: a platform operator is party to every entry.

The representational problem was solved repeatedly between 1970 and now, and every such system failed on
**capture cost**. So the first constraint is: **nothing may be required of a participant that the
participant would not do anyway.**

Everything else follows from those four sentences.

## Reading order if you only have an hour

1. [glossary.md](glossary.md) — 10 min, gives you the vocabulary.
2. Paper I notes §11–§13 and §22 — the derivation and the sixteen requirements.
3. Paper IV notes §6, §8, §20 — the act vocabulary, attestation, and the conformance tests.
4. Paper II notes §12 and §16 — the dominance argument and the ten predictions.

## Provenance of these notes

Extracted from the PDFs and read in full on 2026-08-06. Section, definition, claim and requirement
numbers are the papers' own. Where a numbered cross-reference in a paper was broken in the source
(a few `??` and `refsec:` artefacts survive in the PDFs), the note resolves it from context and says so.
