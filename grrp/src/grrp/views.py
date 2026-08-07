"""Derived views.

Nothing here is stored.  The current state of a trajectory, the register of
open problems, and the chain leading to a release are all computed from the log
on demand.  A stored snapshot would become the thing people trust, the log
would drift from it or be edited to match it, and every claim the record makes
about its own integrity would fail at once.

The derivation rules are stated here rather than distributed through the code,
because they are choices a reader is entitled to disagree with.

    produces a state      every act writes a posterior state
    supersedes its prior  transformation only
    retires its prior     decision whose relation is cito:retracts
    a live position       posterior of claim or transformation, not superseded
                          and not retired

A trajectory's opening question is a state and is not a position: it is what
the work is about, and it does not stop being so when someone takes a view. It
stays in the register of open problems until something answers it. Objections,
decisions and releases produce states too, but those are annotations on a
position rather than positions themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

from .store import Repo

SUPERSEDING_ACTS = frozenset({"transformation"})
POSITION_ACTS = frozenset({"claim", "transformation"})
RETRACTS = "cito:retracts"


def opening_state(repo: Repo, traj_id: str) -> str | None:
    """The state holding the trajectory's question.

    The anchor a first claim attaches to, so that even the first transition in
    a trajectory references a specific identified prior state rather than the
    project as a whole.
    """
    for record in repo.transitions(traj_id):
        if record.get("act") == "question" and not record.get("prior_state"):
            return record.get("posterior_state")
    return None


def supersedes(record: dict) -> bool:
    return record.get("act") in SUPERSEDING_ACTS and bool(record.get("prior_state"))


def retires(record: dict) -> bool:
    return record.get("act") == "decision" and record.get("relation") == RETRACTS


def current_states(repo: Repo, traj_id: str) -> list[str]:
    """The live positions of a trajectory.

    There may be several.  Two states sharing a parent are a divergence, both
    are preserved, and neither is designated principal, default or canonical:
    in inquiry a fork is frequently the correct outcome, so plurality is the
    normal shape of a healthy record rather than an unfinished one.
    """
    records = repo.transitions(traj_id)
    live: list[str] = []
    closed: set[str] = set()
    for record in records:
        if supersedes(record) or retires(record):
            closed.add(record["prior_state"])
        if record.get("act") in POSITION_ACTS and record.get("posterior_state"):
            live.append(record["posterior_state"])
    seen: set[str] = set()
    ordered = [s for s in live if not (s in seen or seen.add(s))]
    return [s for s in ordered if s not in closed]


def answered(repo: Repo, traj_id: str) -> set[str]:
    """Transitions that a later transition has taken up as a parent.

    A challenge is answered when the work moves in response to it, and the
    graph already records that: the responding transformation or decision names
    the challenge among its parents.  Nothing is edited to mark it answered,
    which is what the append-only rule requires.
    """
    taken: set[str] = set()
    for record in repo.transitions(traj_id):
        if record.get("act") in {"transformation", "decision"}:
            taken.update(record.get("parents") or [])
    return taken


@dataclass
class OpenItem:
    trajectory: str
    transition: dict
    attaches_to: str | None
    text: str | None


def open_items(repo: Repo, traj_id: str) -> list[OpenItem]:
    """The register of unresolved states: the entry path.

    Every item is an identified state that a party holding no prior position in
    the trajectory could reference in a challenge, a connection or a
    verification.  Keeping the list to what is genuinely still open is the
    difference between a register of open problems and a list of everything
    nobody has closed.
    """
    resolved = answered(repo, traj_id)
    items: list[OpenItem] = []
    for record in repo.transitions(traj_id):
        if record.get("disposition") != "unresolved":
            continue
        if record["id"] in resolved:
            continue
        target_state = record.get("posterior_state") or record.get("prior_state")
        items.append(
            OpenItem(
                trajectory=traj_id,
                transition=record,
                attaches_to=record.get("prior_state"),
                text=repo.read_state(traj_id, target_state) if target_state else None,
            )
        )
    return items


def standing_objections(repo: Repo, traj_id: str, state_id: str) -> list[dict]:
    """Challenges against a state that no later transition has taken up.

    A release enumerates these.  It asserts that a state is published and that
    these objections stand; it asserts nothing about their merit.
    """
    resolved = answered(repo, traj_id)
    return [
        record
        for record in repo.transitions(traj_id)
        if record.get("act") == "challenge"
        and record.get("prior_state") == state_id
        and record.get("disposition") == "unresolved"
        and record["id"] not in resolved
    ]


def ancestry(repo: Repo, traj_id: str, tx_id: str) -> list[dict]:
    """Every transition the given one descends from, oldest first."""
    index = {record["id"]: record for record in repo.transitions(traj_id)}
    seen: set[str] = set()
    order: list[dict] = []

    def walk(identifier: str) -> None:
        if identifier in seen or identifier not in index:
            return
        seen.add(identifier)
        record = index[identifier]
        for parent in record.get("parents") or []:
            walk(parent)
        order.append(record)

    walk(tx_id)
    return order


def chain_to_state(repo: Repo, traj_id: str, state_id: str) -> list[dict]:
    """The transitions leading to a state, oldest first."""
    producers = [
        record
        for record in repo.transitions(traj_id)
        if record.get("posterior_state") == state_id
    ]
    if not producers:
        return []
    return ancestry(repo, traj_id, producers[-1]["id"])


def contributors(records: list[dict]) -> list[tuple[str, list[str]]]:
    """Parties and their CRediT roles across a set of transitions.

    Grouped, never counted: a tally of contributions would be a quantity over
    participants, and there is none of those anywhere in this tool.
    """
    roles: dict[str, list[str]] = {}
    for record in records:
        performer = record.get("performer")
        if performer:
            roles.setdefault(performer, [])
        for contribution in record.get("contributions") or []:
            party = contribution.get("party")
            role = contribution.get("role")
            if party and role and role not in roles.setdefault(party, []):
                roles[party].append(role)
    return sorted(roles.items())


def absorptions(records: list[dict]) -> list[dict]:
    """Absorption links across a set of transitions.

    Each names the state content was taken from and the party who produced it.
    Attribution, and no power to prevent, condition or reverse the use.
    """
    out: list[dict] = []
    for record in records:
        for link in record.get("absorption") or []:
            out.append({**link, "into": record["id"]})
    return out


def redactions(repo: Repo, traj_id: str) -> dict[str, dict]:
    """States whose content has been removed, by state identifier.

    A redacted record continues to assert that a transition occurred, by whom,
    of what type, and at what position in the graph.  It no longer supplies
    what was said.  The record of the removal is itself never removed: a system
    that erased the trace of an erasure would leave a record misdescribing its
    own history, in a way no later reader could detect.
    """
    return {
        record["prior_state"]: record
        for record in repo.transitions(traj_id)
        if record.get("kind") == "operation"
        and record.get("operation") == "redaction"
        and record.get("prior_state")
    }


def transitions_only(records: list[dict]) -> list[dict]:
    """Transitions, with administrative operations filtered out."""
    return [r for r in records if r.get("kind") != "operation"]


def has_attestation(repo: Repo, traj_id: str) -> bool:
    return any(
        (record.get("registration") or {}).get("attested")
        for record in repo.transitions(traj_id)
    )
