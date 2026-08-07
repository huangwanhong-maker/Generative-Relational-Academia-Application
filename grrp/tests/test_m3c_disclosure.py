"""M3c. Disclosure classes, grounds, and monotone release.

An arrangement that records how understanding changes must be able to withhold.
The question is never whether but on what ground -- and what follows from the
ground. A ground determines an object and leaves a residue, and the residue
requirement is what stops a ground operating as a licence. Without it every
ground collapses into the same thing, which is silence with a justification
attached.
"""

from __future__ import annotations

import pytest

from conftest import sid
from grrp import canonical, store, views, vocab


@pytest.fixture()
def chartered(trajectory):
    workspace, traj_id = trajectory
    workspace.run("charter", "adopt", "--classes", "private,group,public")
    workspace.run("claim", traj_id, "-m", "A method that took some funding to develop.")
    return workspace, traj_id, workspace.repo.transitions(traj_id)[-1]


# --- the charter -------------------------------------------------------------

def test_without_a_charter_there_is_nothing_to_disclose_at(trajectory):
    """A record referring to a class nobody has defined is uninterpretable."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    record = workspace.repo.transitions(traj_id)[-1]

    result = workspace.run(
        "disclose", sid(record["id"]), "--class", "private", expect_ok=False
    )
    assert result.exit_code == 1
    assert "grrp charter adopt" in result.output


def test_the_protocol_supplies_no_default_set_of_classes(workspace):
    """A specification supplying a model charter would be a specification of
    governance, and communities that reject the model could not conform."""
    assert workspace.repo.classes() == []
    result = workspace.run("charter", "adopt", expect_ok=False)
    assert result.exit_code == 1
    assert "yours to decide" in result.output


def test_classes_are_ordered_by_inclusion_narrowest_first(workspace):
    output = workspace.run("charter", "adopt", "--classes", "private,group,public").output
    assert "private < group < public" in output
    assert workspace.repo.classes() == ["private", "group", "public"]


def test_a_charter_amendment_is_prospective_and_versioned(workspace):
    workspace.run("charter", "adopt", "--classes", "private,public")
    assert workspace.repo.charter()["version"] == 1
    output = workspace.run("charter", "adopt", "--classes", "private,group,public").output
    assert "charter version 2" in output
    assert "applies to records made after it" in output
    assert "interpretation of records made before it" in output


# --- grounds are closed, and each leaves a residue ---------------------------

def test_the_four_grounds_are_closed(chartered):
    workspace, _, record = chartered
    result = workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "commercially_sensitive", expect_ok=False,
    )
    assert result.exit_code == 1
    assert "The set is closed" in result.output
    for name in ("rivalry", "hazard", "vulnerability", "appropriability"):
        assert name in result.output


def test_restricting_without_a_ground_is_refused(chartered):
    """Under ordinary practice a restriction is a default that asserts nothing.
    Here it is an assertion, dated and attributable."""
    workspace, _, record = chartered
    result = workspace.run(
        "disclose", sid(record["id"]), "--class", "private", expect_ok=False
    )
    assert result.exit_code == 1
    assert "C7" in result.output
    assert "must declare a ground" in result.output


def test_disclosing_at_the_widest_class_needs_no_ground(chartered):
    workspace, _, record = chartered
    assert workspace.run("disclose", sid(record["id"]), "--class", "public").exit_code == 0


def test_declaring_a_ground_surfaces_the_residue(chartered):
    """The one part of the design that gains something without giving something
    up: the residue lies outside the omitted component, so disclosing it costs
    nothing under any ground."""
    workspace, _, record = chartered
    output = workspace.run(
        "disclose", sid(record["id"]), "--class", "private", "--ground", "appropriability"
    ).output

    assert "What this ground leaves disclosable" in output
    assert "negative results" in output
    assert "rent-seeking secrecy" in output


def test_every_ground_states_a_condition_object_residue_and_failure():
    """A ground stated without its failure mode is a licence: any party may
    assert the condition and no party can say what has gone wrong when the
    assertion is false."""
    for name, ground in vocab.GROUNDS.items():
        for field in ("condition", "object", "residue", "failure"):
            assert ground[field], (name, field)


def test_grounds_command_prints_the_typology(workspace):
    output = workspace.run("grounds").output
    assert "the trajectory in full" in output          # rivalry's residue
    assert "do not convey the method" in output       # hazard's
    assert "everything, at the scheduled time" in output
    assert "The set is closed" in output


def test_composing_grounds_intersects_their_residues(chartered):
    workspace, _, record = chartered
    output = workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "hazard", "--ground", "appropriability",
    ).output
    assert "the residue is the intersection" in output
    assert "declaring more is not free" in output


# --- monotone disclosure -----------------------------------------------------

def test_disclosure_may_widen(chartered):
    workspace, traj_id, record = chartered
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "vulnerability")
    workspace.run("disclose", sid(record["id"]), "--class", "public")

    current = views.disclosure_of(workspace.repo, traj_id, record["id"])
    assert current["effective_class"] == "public"


def test_disclosure_may_never_narrow(chartered):
    """A party who has read a record retains what they read, so an operation
    offering the appearance of withdrawal would misdescribe the world to the
    people relying on it."""
    workspace, traj_id, record = chartered
    workspace.run("disclose", sid(record["id"]), "--class", "public")

    result = workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "hazard", expect_ok=False,
    )
    assert result.exit_code == 1
    assert "C7" in result.output
    assert "widen and never narrow" in result.output

    current = views.disclosure_of(workspace.repo, traj_id, record["id"])
    assert current["effective_class"] == "public"


def test_no_command_offers_to_unpublish(workspace):
    from grrp.cli import app

    names = [c.name or c.callback.__name__ for c in app.registered_commands]
    for forbidden in ("unpublish", "unrelease", "hide", "conceal", "restrict"):
        assert forbidden not in names


# --- scheduled release -------------------------------------------------------

def test_a_schedule_belongs_only_to_vulnerability(chartered):
    """Rivalry ends when the resource is uncontended and appropriability when
    the funding purpose is served, neither observable from here. Hazard does
    not end at all."""
    workspace, _, record = chartered
    result = workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "hazard", "--release-at", "2027-01-01", expect_ok=False,
    )
    assert result.exit_code == 1
    assert "the only ground with a terminus" in result.output
    assert "Hazard does not end" in result.output


def test_a_schedule_widens_by_itself_at_the_stated_time(chartered):
    """Honouring a scheduled release widens the class without a further act by
    any party, so it is derived from the log and the clock: there is nothing to
    fire and nothing that can be forgotten."""
    workspace, traj_id, record = chartered
    workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "vulnerability", "--release-at", "2026-01-01",
    )

    before = views.disclosure_of(workspace.repo, traj_id, record["id"], at="2025-06-01T00:00:00Z")
    assert before["effective_class"] == "private"
    assert before["schedule_fired"] is False

    after = views.disclosure_of(workspace.repo, traj_id, record["id"], at="2026-06-01T00:00:00Z")
    assert after["effective_class"] == "public"
    assert after["schedule_fired"] is True


def test_a_schedule_may_be_shortened(chartered):
    workspace, traj_id, record = chartered
    workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "vulnerability", "--release-at", "2030-01-01",
    )
    assert workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "vulnerability", "--release-at", "2027-01-01",
    ).exit_code == 0
    current = views.disclosure_of(workspace.repo, traj_id, record["id"], at="2025-01-01T00:00:00Z")
    assert current["release_at"] == "2027-01-01"


def test_extending_a_schedule_is_refused_and_the_attempt_recorded(chartered):
    """A delay that can be extended indefinitely is a permanent withholding
    made to look temporary. The attempt is recorded, because a charter may in
    some circumstances allow it and it should be visible that it was made."""
    workspace, traj_id, record = chartered
    workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "vulnerability", "--release-at", "2027-01-01",
    )

    result = workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "vulnerability", "--release-at", "2030-01-01", expect_ok=False,
    )
    assert result.exit_code == 1
    assert "shortened, never extended" in result.output

    attempts = [
        r for r in workspace.repo.transitions(traj_id)
        if (r.get("payload") or {}).get("attempted") == "extend_schedule"
    ]
    assert attempts, "the attempt is in the record"
    assert attempts[0]["payload"]["refused"] is True

    current = views.disclosure_of(workspace.repo, traj_id, record["id"], at="2025-01-01T00:00:00Z")
    assert current["release_at"] == "2027-01-01", "the schedule is unchanged"


# --- per record, derived, and covered ----------------------------------------

def test_disclosure_is_per_record_not_per_repository(chartered):
    """In a version-control system openness is a property of a repository. A
    single line of work needs states disclosed to everyone, to a group, and to
    nobody, with the differences declared and grounded."""
    workspace, traj_id, first = chartered
    workspace.run("claim", traj_id, "-m", "A second position, freely shown.")
    second = workspace.repo.transitions(traj_id)[-1]

    workspace.run("disclose", sid(first["id"]), "--class", "private", "--ground", "appropriability")
    workspace.run("disclose", sid(second["id"]), "--class", "public")

    assert views.disclosure_of(workspace.repo, traj_id, first["id"])["effective_class"] == "private"
    assert views.disclosure_of(workspace.repo, traj_id, second["id"])["effective_class"] == "public"


def test_an_undisclosed_record_is_not_a_restriction_without_a_ground(chartered):
    """Not yet published is a different thing from withheld."""
    workspace, traj_id, record = chartered
    assert views.disclosure_of(workspace.repo, traj_id, record["id"]) is None


def test_disclosure_is_derived_from_the_log(chartered):
    workspace, traj_id, record = chartered
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "hazard")
    workspace.run("disclose", sid(record["id"]), "--class", "public")

    operations = views.disclosure_operations(workspace.repo, traj_id, record["id"])
    assert len(operations) == 2, "both changes are in the log; neither overwrote the other"
    assert workspace.run("check").exit_code == 0


# --- acceptance test 5 -------------------------------------------------------

def test_a_disclosure_change_invalidates_nothing(chartered):
    """Widening a class is a lawful operation. If it invalidated identifiers or
    signatures, an implementation would either forbid the operation or ignore
    the failure, and both defeat the purpose."""
    workspace, traj_id, record = chartered
    before = record["id"]

    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "vulnerability")
    workspace.run("disclose", sid(record["id"]), "--class", "public")

    after = [r for r in workspace.repo.transitions(traj_id) if r["id"] == before][0]
    assert after["id"] == before
    assert canonical.transition_id(after) == before
    assert workspace.run("check").exit_code == 0


def test_the_declared_ground_is_covered_by_the_identifier(chartered):
    """A ground that could be altered afterwards would be no ground at all."""
    workspace, traj_id, record = chartered
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "appropriability")

    path = next(
        p for p in workspace.repo.transitions_dir(traj_id).glob("*.yaml")
        if store.read_yaml(p).get("operation") == "disclosure_changed"
    )
    tampered = store.read_yaml(path)
    tampered["payload"]["grounds"] = ["hazard"]
    store.write_yaml(path, tampered)

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "does not match its content" in result.output


def test_check_rejects_a_ground_outside_the_closed_set(chartered):
    workspace, traj_id, record = chartered
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "hazard")

    path = next(
        p for p in workspace.repo.transitions_dir(traj_id).glob("*.yaml")
        if store.read_yaml(p).get("operation") == "disclosure_changed"
    )
    tampered = store.read_yaml(path)
    tampered["payload"]["grounds"] = ["because_i_said_so"]
    tampered["id"] = canonical.transition_id(tampered)
    path.unlink()
    store.write_yaml(workspace.repo.transition_path(traj_id, tampered["id"]), tampered)

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "not one of the four grounds" in result.output


def test_show_surfaces_what_is_restricted_and_on_what_ground(chartered):
    workspace, _, record = chartered
    workspace.run(
        "disclose", sid(record["id"]), "--class", "private",
        "--ground", "vulnerability", "--release-at", "2027-01-01",
    )
    output = workspace.run("show").output
    assert "restricted" in output
    assert "vulnerability" in output
    assert "widens to public on 2027-01-01" in output
    assert "residue that must still be disclosed" in output
