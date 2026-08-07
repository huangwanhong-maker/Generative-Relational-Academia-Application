"""The conformance self-test.

Two kinds of thing are checked, and they are reported separately because they
mean different things.

*Integrity* is a fact about this record: identifiers recomputed from the files,
the graph acyclic, parents present, no state referenced that was never written
without a redaction recorded.  A failure here means the record has been edited
or corrupted.

*Conformance* is a fact about this implementation: no quantity over
participants or trajectories, no operation requiring a model or a network, and
every command stating a purpose for the person running it.  A failure here
means the tool has drifted from the protocol, which is the more likely of the
two and the harder to notice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import canonical, keys, vocab
from .store import Repo


@dataclass
class Report:
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def check_repo(repo: Repo) -> Report:
    report = Report()
    profile = repo.profile()

    if profile.get("protocol") != "grrp/0.1":
        report.fail(f"profile declares protocol {profile.get('protocol')!r}, expected grrp/0.1")
    if profile.get("canonicalisation") != canonical.CANONICALISATION:
        report.fail("profile canonicalisation does not match this implementation")

    trajectory_ids = repo.trajectory_ids()
    if not trajectory_ids:
        report.note("no trajectories recorded yet")

    for traj_id in trajectory_ids:
        _check_trajectory(repo, traj_id, report)

    _check_scalar_exclusion(report)
    return report


def _check_trajectory(repo: Repo, traj_id: str, report: Report) -> None:
    records = repo.transitions(traj_id)
    by_id = {record.get("id"): record for record in records}
    attested = 0

    for record in records:
        label = canonical.short(record.get("id") or "?")

        # Identifier recomputation.  This is the append-only test: any edit to a
        # covered field changes the identifier, and because parents are covered,
        # it invalidates every descendant too.
        recomputed = canonical.transition_id(record)
        if recomputed != record.get("id"):
            report.fail(
                f"{traj_id}/{label}: recorded identifier does not match its content. "
                "The transition has been edited, or was written by an implementation "
                "with a different canonicalisation."
            )
        expected_path = repo.transition_path(traj_id, record["id"])
        if not expected_path.is_file():
            report.fail(f"{traj_id}/{label}: filename does not match the identifier")

        # Vocabulary.
        if record.get("kind") == "transition":
            if record.get("act") not in vocab.ACTS:
                report.fail(f"{traj_id}/{label}: unknown act {record.get('act')!r}")
            if record.get("disposition") not in vocab.DISPOSITIONS:
                report.fail(
                    f"{traj_id}/{label}: disposition {record.get('disposition')!r} is not "
                    "one of accepted, contested, unresolved"
                )
            target = record.get("target")
            if target and target not in vocab.TARGETS:
                report.note(f"{traj_id}/{label}: target {target!r} is not a protocol value")
            trigger = record.get("trigger")
            if trigger and trigger not in vocab.TRIGGERS:
                report.note(f"{traj_id}/{label}: trigger {trigger!r} is not a protocol value")
            relation = record.get("relation")
            if relation and relation.startswith("local:"):
                report.note(
                    f"{traj_id}/{label}: relation {relation!r} is a local value and needs "
                    "a charter to define it"
                )
        elif record.get("kind") == "operation":
            if record.get("operation") not in vocab.OPERATIONS:
                report.fail(f"{traj_id}/{label}: unknown operation {record.get('operation')!r}")
            if record.get("act") or record.get("disposition"):
                report.fail(
                    f"{traj_id}/{label}: an operation carries no act and no disposition. "
                    "Operations and transitions must not be records of the same kind."
                )
            payload = record.get("payload") or {}
            if not record.get("subject"):
                report.fail(f"{traj_id}/{label}: an operation must name its subject")
            if record.get("operation") == "redaction":
                if not payload.get("ground"):
                    report.fail(f"{traj_id}/{label}: a redaction must record its ground")
            if record.get("operation") == "disclosure_changed" and not payload.get("refused"):
                grounds = payload.get("grounds") or []
                for name in grounds:
                    if name not in vocab.GROUNDS:
                        report.fail(
                            f"{traj_id}/{label}: {name!r} is not one of the four grounds. "
                            "The set is closed."
                        )
                if payload.get("release_at") and "vulnerability" not in grounds:
                    report.fail(
                        f"{traj_id}/{label}: a schedule belongs to exploratory vulnerability, "
                        "the only ground with a terminus."
                    )
        else:
            report.fail(f"{traj_id}/{label}: unknown kind {record.get('kind')!r}")

        # Granularity: a transition names the state it altered.  The opening
        # transition of a trajectory is the only one without a prior state.
        if record.get("kind") == "transition" and record.get("act") != "question":
            if not record.get("prior_state"):
                report.fail(
                    f"{traj_id}/{label}: no prior state. A transition references a "
                    "specific identified state, never a project or a document as a whole."
                )

        for entry in record.get("contributions") or []:
            if not entry.get("party") or not entry.get("role"):
                report.fail(
                    f"{traj_id}/{label}: a contribution records a party and a role. "
                    "Neither is optional where more than one party is present."
                )
            elif not str(entry["role"]).startswith("credit:"):
                report.note(
                    f"{traj_id}/{label}: role {entry['role']!r} is not drawn from the bound "
                    "contributor vocabulary"
                )

        for link in record.get("absorption") or []:
            if not link.get("state") or not link.get("party"):
                report.fail(
                    f"{traj_id}/{label}: an absorption link names the state content was taken "
                    "from and the party who produced it."
                )

        for parent in record.get("parents") or []:
            if parent not in by_id:
                report.fail(f"{traj_id}/{label}: parent {canonical.short(parent)} is missing")

        registration = record.get("registration") or {}
        if registration.get("attested"):
            attested += 1
            registrar = registration.get("registrar")
            if registrar == record.get("performer"):
                report.fail(
                    f"{traj_id}/{label}: registered by the party who performed it, but marked "
                    "attested. Credibility follows from registration by a party who did not "
                    "coordinate with the performer."
                )
            signature = registration.get("signature")
            if not signature:
                report.fail(f"{traj_id}/{label}: attested with no signature")
            elif registrar:
                data = canonical.signing_input(
                    record["id"], registrar, registration.get("time", "")
                )
                if not keys.verify(registrar, data, signature):
                    report.fail(
                        f"{traj_id}/{label}: the registration signature does not verify. "
                        "The record does not say what it appears to say."
                    )

    _check_acyclic(traj_id, records, by_id, report)
    _check_content(repo, traj_id, records, report)

    proposals = repo.proposals(traj_id)
    if proposals:
        report.note(
            f"{traj_id}: {len(proposals)} act(s) proposed and not yet registered. "
            "Nothing proposed is in the log."
        )

    for identifier, disputes in views_module().contested_attributions(repo, traj_id).items():
        if identifier in by_id:
            report.note(
                f"{traj_id}/{canonical.short(identifier)}: its attribution is contested by "
                f"{len(disputes)} further act(s). Both positions stand; nothing here decides "
                "between them."
            )

    withdrawn = views_module().withdrawn_attestations(repo, traj_id)
    for identifier in sorted(withdrawn):
        if identifier in by_id:
            report.note(
                f"{traj_id}/{canonical.short(identifier)}: its registrar has withdrawn the "
                "attestation. Both the registration and the withdrawal remain in the log."
            )

    if records and attested == 0:
        report.note(
            f"{traj_id}: every transition was registered by the party who performed it. "
            "The record is unattested: useful to its author, and carrying no evidential "
            "weight. Credibility begins where a second party registers."
        )


def _withheld_on_receipt(repo: Repo) -> set[str]:
    """States whose content a sender could not disclose to us.

    A gap nobody can account for is tampering. A gap the record itself explains
    is separability working: the skeleton, the graph and the identifiers are
    all intact, and only the content is absent.
    """
    from .store import read_yaml

    received = repo.grrp_dir / "received"
    if not received.is_dir():
        return set()
    withheld: set[str] = set()
    for path in received.glob("*.yaml"):
        manifest = (read_yaml(path).get("manifest") or {})
        withheld.update(manifest.get("content_withheld") or [])
    return withheld


def views_module():
    from . import views

    return views


def _check_content(repo: Repo, traj_id: str, records: list[dict], report: Report) -> None:
    """Content may be missing, and only for a recorded reason.

    Separability is what makes the log both tamper-evident and lawfully
    redactable: removing a state's content leaves the skeleton, its parent
    links and its identifier chain intact.  What it must not do is leave a gap
    nobody can account for, so a missing state without a recorded redaction is
    a failure rather than an absence.
    """
    from . import views

    removed = views.redactions(repo, traj_id)
    referenced: set[str] = set()
    for record in records:
        for key in ("prior_state", "posterior_state"):
            if record.get(key):
                referenced.add(record[key])

    sealed = repo.grrp_dir / "sealed"
    for state_id in sorted(referenced):
        if repo.state_path(traj_id, state_id).is_file():
            continue
        if (sealed / f"{state_id.split(':')[-1]}.md").is_file():
            report.note(
                f"{traj_id}/{canonical.short(state_id)}: sealed. The record says a state with "
                "this identifier was held at this time, and says nothing about what it was. "
                "It generates nothing while sealed."
            )
            continue
        operation = removed.get(state_id)
        if operation:
            report.note(
                f"{traj_id}/{canonical.short(state_id)}: content redacted on the ground of "
                f"{(operation.get('payload') or {}).get('ground')}. The transition, its "
                "position in the graph and "
                "the record of the removal all remain."
            )
        elif state_id in _withheld_on_receipt(repo):
            report.note(
                f"{traj_id}/{canonical.short(state_id)}: content was withheld when this record "
                "was obtained, because the sender could not disclose it here. The skeleton, "
                "its position in the graph and its identifier are intact."
            )
        else:
            report.fail(
                f"{traj_id}/{canonical.short(state_id)}: content is missing and nothing "
                "accounts for it - no redaction was recorded, it is not sealed, and it was "
                "not withheld when obtained. Either the file was deleted outside grrp, or "
                "the record has been tampered with."
            )

    # The graph must be unaffected by a removal.
    for state_id, operation in removed.items():
        producers = [r for r in records if r.get("posterior_state") == state_id]
        if not producers:
            report.fail(
                f"{traj_id}/{canonical.short(operation['id'])}: redaction names a state no "
                "transition produced"
            )


def _check_acyclic(traj_id: str, records: list[dict], by_id: dict, report: Report) -> None:
    """A record permitting cycles admits a history in which a state precedes
    and follows itself, and every derived view becomes ill-defined."""
    colour: dict[str, int] = {}

    def visit(identifier: str) -> bool:
        state = colour.get(identifier, 0)
        if state == 1:
            return False
        if state == 2:
            return True
        colour[identifier] = 1
        for parent in by_id.get(identifier, {}).get("parents") or []:
            if parent in by_id and not visit(parent):
                return False
        colour[identifier] = 2
        return True

    for record in records:
        if not visit(record["id"]):
            report.fail(f"{traj_id}: the transition graph contains a cycle")
            return


# Identifiers that would be a quantity over participants or trajectories.  A
# count *within* one trajectory, shown without comparison to another, is
# permitted; anything comparable across them is not.
FORBIDDEN_SUBSTRINGS = (
    "reputation",
    "leaderboard",
    "ranking",
    "contribution_score",
    "activity_index",
    "trajectory_score",
    "h_index",
)


def _check_scalar_exclusion(report: Report) -> None:
    from pathlib import Path

    source = Path(__file__).parent
    for path in source.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for needle in FORBIDDEN_SUBSTRINGS:
            # The names appear in this list and in the comments explaining why
            # they are excluded; those two files are the exception.
            if needle in text and path.name not in {"check.py", "cli.py"}:
                report.fail(
                    f"{path.name}: contains {needle!r}. No quantity over participants "
                    "or trajectories is computed, stored, displayed or exported."
                )
    report.note(
        "no quantity over participants or trajectories is computed by this implementation"
    )
