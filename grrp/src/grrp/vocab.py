"""The typed vocabularies.

The type of a transition is factored into five independent dimensions with
small closed vocabularies, rather than one flat list of several dozen tags.
Agreement between two people classifying the same event declines as the number
of categories rises, and a vocabulary that requires deliberation reintroduces
the recording cost the whole design exists to avoid.

Relations bind to CiTO and contributor roles to CRediT.  Values that no
deployed vocabulary covers are marked ``local:`` and must be defined by a
community charter; they are accepted and flagged, never silently presented as
though they were bound.
"""

from __future__ import annotations

VOCABULARIES = {
    "relation": {"prefix": "cito", "namespace": "http://purl.org/spar/cito/"},
    "contributor": {
        "prefix": "credit",
        "namespace": "https://credit.niso.org/contributor-roles/",
    },
    "provenance": {"prefix": "prov", "namespace": "http://www.w3.org/ns/prov#"},
}

# --- act ---------------------------------------------------------------------
# Fixed by the protocol.  Not extensible: acts are what interoperability rests
# on, and a record whose act vocabulary varied by community could not travel.
ACTS = (
    "question",
    "claim",
    "challenge",
    "transformation",
    "decision",
    "connection",
    "verification",
    "release",
)

#: Acts implemented at the personal tier (M1).
ACTS_M1 = ("question", "claim", "challenge", "transformation", "decision", "release")

# --- target ------------------------------------------------------------------
# Extensible by charter: a mathematics community wants obstruction types, a
# laboratory wants deviation types.
TARGETS = (
    "question",
    "assumption",
    "hypothesis",
    "concept",
    "theory",
    "method",
    "path",
    "artefact",
)

# --- relation ----------------------------------------------------------------
# Bound to CiTO.  The friendly name on the left is a convenience for typing at
# a prompt; the CiTO identifier on the right is what is stored, because a
# record storing the word "extends" is uninterpretable once a second vocabulary
# uses the same word differently.
RELATIONS = {
    "extends": "cito:extends",
    "modifies": "cito:updates",
    "refines": "cito:qualifies",
    "replaces": "cito:corrects",
    "disagrees": "cito:disagreesWith",
    "agrees": "cito:agreesWith",
    "supports": "cito:supports",
    "refutes": "cito:refutes",
    "confirms": "cito:confirms",
    "retracts": "cito:retracts",
    "repliesTo": "cito:repliesTo",
    "usesMethodIn": "cito:usesMethodIn",
    "relates": "cito:citesAsRelated",
    "supportedBy": "cito:obtainsSupportFrom",
    "usesDataFrom": "cito:usesDataFrom",
    "disputes": "cito:disputes",
}

#: Relations named in the design for which CiTO has no counterpart.  They are
#: available as local values and require a charter to define them, which the
#: personal tier does not have.  Using one emits a warning.
LOCAL_RELATIONS = ("generalises", "specialises", "transfers")

# --- trigger -----------------------------------------------------------------
# Extensible by charter.  ``ai_suggestion`` exists so that a proposal
# originating in an automated analysis is marked as such: a model may occasion
# a transition and may not author or register one.
TRIGGERS = (
    "self",
    "literature",
    "experiment",
    "simulation",
    "observation",
    "discussion",
    "objection",
    "failure",
    "ai_suggestion",
    "entering_party",
)

# --- disposition -------------------------------------------------------------
# Exactly three values.  Fixed by the protocol and never extended or reduced.
#
# ``unresolved`` is why the vocabulary is closed.  Most objections in
# theoretical work are never resolved: they stand, and the work proceeds beside
# them.  A record admitting only acceptance and rejection would be
# systematically false about the fields this protocol most concerns, and would
# exert pressure toward fabricated closure.
DISPOSITIONS = ("accepted", "contested", "unresolved")

# --- contributor roles -------------------------------------------------------
# CRediT.  Contribution is not an act: it types a party's part *in* an act.
CREDIT_ROLES = (
    "Conceptualization",
    "DataCuration",
    "FormalAnalysis",
    "FundingAcquisition",
    "Investigation",
    "Methodology",
    "ProjectAdministration",
    "Resources",
    "Software",
    "Supervision",
    "Validation",
    "Visualization",
    "WritingOriginalDraft",
    "WritingReviewEditing",
)

# --- grounds of restriction --------------------------------------------------
# Closed.  A community may not declare a new one: grounds determine what may be
# withheld, so a community free to invent them is free to withhold anything by
# naming a reason, and the apparatus becomes decorative.
#
# Each states four things.  The fourth is what makes the instrument useful: a
# ground stated without its failure mode is a licence, since any party may
# assert the condition and no party can say what has gone wrong when the
# assertion is false.
GROUNDS = {
    "rivalry": {
        "condition": "a resource required for the work admits limited simultaneous use",
        "object": "access to the resource",
        "residue": "the trajectory in full - questions, methods, decisions, failures, "
                   "interpretations and results, none of which consumes the resource",
        "failure": "a restriction on access converted into a restriction on knowledge",
        "terminus": None,
    },
    "hazard": {
        "condition": "propagation of the content would create a risk of serious harm, "
                     "and the risk arises from the content being known",
        "object": "the propagable content of the method - the sequence by which a "
                  "capability is obtained, the constraints, the parameters that matter",
        "residue": "the existence of the work, the questions pursued, the decisions taken "
                   "and their reasons, the interpretations reached, and results that do "
                   "not convey the method",
        "failure": "the widest restriction obtained on the strongest justification, "
                   "unfalsifiable from outside the restricted class",
        "terminus": None,
    },
    "vulnerability": {
        "condition": "exposure of the work at its present stage would suppress or distort it",
        "object": "the timing of exposure",
        "residue": "everything, at the scheduled time",
        "failure": "postponement converted into permanent withholding",
        "terminus": "scheduled",
    },
    "appropriability": {
        "condition": "the work is funded by an arrangement that requires excludability",
        "object": "the content whose disclosure would destroy that excludability",
        "residue": "the existence of the work, the questions pursued, the decisions taken "
                   "and their reasons, and negative results",
        "failure": "rent-seeking secrecy - secrecy obtained on an economic justification "
                   "that does not apply",
        "terminus": None,
    },
}

# --- redaction grounds -------------------------------------------------------
# No deployed vocabulary covers why content was removed, so this is a local set
# and a community charter may replace it.  It is separate from the four grounds
# of *restriction*, which are closed and concern disclosure rather than removal.
REDACTION_GROUNDS = (
    "erasure_request",
    "consent_withdrawn",
    "personal_data",
    "hazard",
    "legal_order",
)

# --- administrative operations ----------------------------------------------
OPERATIONS = (
    "disclosure_changed",
    "redaction",
    "key_rotation",
    "fork_declared",
    "attribution_contested",
    "binding_recorded",
)


def resolve_relation(name: str | None) -> tuple[str | None, bool]:
    """Return (stored value, is_bound).

    ``is_bound`` is False for local values, which an implementation must never
    present as though they came from a deployed vocabulary.
    """
    if name is None:
        return None, True
    if name in RELATIONS:
        return RELATIONS[name], True
    if name.startswith("cito:") and name.split(":", 1)[1] in {
        v.split(":", 1)[1] for v in RELATIONS.values()
    }:
        return name, True
    if name in LOCAL_RELATIONS:
        return f"local:{name}", False
    if name.startswith("local:"):
        return name, False
    raise ValueError(
        f"unknown relation {name!r}. "
        f"Bound (CiTO): {', '.join(sorted(RELATIONS))}. "
        f"Local, needs a charter: {', '.join(LOCAL_RELATIONS)}."
    )


def resolve_role(name: str) -> str:
    """Return a CRediT identifier for a contributor role."""
    lowered = {role.lower(): role for role in CREDIT_ROLES}
    key = name.split(":")[-1].replace("-", "").replace("_", "").replace(" ", "").lower()
    if key in lowered:
        return f"credit:{lowered[key]}"
    raise ValueError(
        f"unknown contributor role {name!r}. CRediT roles: {', '.join(CREDIT_ROLES)}."
    )
