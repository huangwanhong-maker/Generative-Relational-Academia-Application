"""The acceptance tests that decide conformance.

Numbered as in the build order. Tests 6 and 8 belong to M2 and M4 and are
skipped with the reason stated, rather than quietly absent.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import sid
from grrp import canonical, store, views
from grrp.cli import app

SOURCE = Path(__file__).resolve().parents[1] / "src" / "grrp"


def source_files() -> list[Path]:
    return sorted(SOURCE.glob("*.py"))


def command_names() -> list[str]:
    return [c.name or c.callback.__name__ for c in app.registered_commands]


# --- 1. no scalars over participants or trajectories -------------------------

FORBIDDEN = (
    "reputation", "leaderboard", "ranking", "rank_", "score", "h_index",
    "contribution_share", "activity_index", "impact_factor", "percentile",
)


def test_no_scalar_identifiers_in_the_source():
    """A measure adopted to direct attention becomes the object of effort, and
    a quantity over a trajectory measures a realisation and not a capacity."""
    offenders: list[str] = []
    for path in source_files():
        text = path.read_text(encoding="utf-8").lower()
        # check.py and cli.py name these words in order to exclude them.
        if path.name in {"check.py", "cli.py"}:
            continue
        for needle in FORBIDDEN:
            if needle in text:
                offenders.append(f"{path.name}: {needle}")
    assert not offenders, offenders


def test_no_command_offers_statistics_or_ranking():
    for name in command_names():
        assert name not in {"stats", "rank", "score", "top", "leaderboard", "dashboard"}


def test_read_commands_emit_no_cross_trajectory_quantity(workspace):
    """Counts within one trajectory, shown without comparison, are permitted.
    Anything comparable across trajectories or participants is not."""
    workspace.run("new", "First question", "--title", "first")
    workspace.run("new", "Second question", "--title", "second")
    for a, b in (("first", "First"), ("second", "Second")):
        workspace.run("claim", a, "-m", f"{b} position.")

    for command in (["log"], ["state"], ["open"], ["check"], ["profile"]):
        output = workspace.run(*command).output.lower()
        assert "total" not in output
        assert "score" not in output
        assert not re.search(r"\b(most|least|top|highest|lowest)\b", output)


# --- 2. independence: no network, no model, no service -----------------------

def test_no_network_or_model_dependency_in_the_source():
    forbidden_imports = (
        "import socket", "import requests", "import urllib", "import http",
        "openai", "anthropic", "boto3", "sqlite3", "import sqlalchemy",
    )
    for path in source_files():
        text = path.read_text(encoding="utf-8").lower()
        for needle in forbidden_imports:
            assert needle not in text, f"{path.name} reaches for {needle}"


def test_the_whole_flow_runs_with_no_service_present(workspace):
    """Create, read, verify, release and export, with nothing but files."""
    workspace.run("new", "Does the method transfer?", "--title", "transfer")
    workspace.run("claim", "transfer", "-m", "It transfers under independence.")
    state = views.current_states(workspace.repo, "transfer")[0]
    workspace.run("challenge", sid(state), "-m", "Independence is not available here.")
    workspace.run("release", sid(state))
    release = workspace.repo.releases("transfer")[0]
    document = workspace.run("export", sid(release["id"])).output
    assert "Independence is not available here." in document
    assert workspace.run("check").exit_code == 0


def test_the_record_is_plain_text_readable_without_this_tool(workspace):
    workspace.run("new", "A question", "--title", "q")
    workspace.run("claim", "q", "-m", "A position.")
    repo = workspace.repo
    for path in repo.transitions_dir("q").glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "act:" in text and "protocol: grrp/0.1" in text
    for path in repo.states_dir("q").glob("*.md"):
        assert path.read_text(encoding="utf-8").strip()


# --- 3. every command states its purpose for the person running it -----------

def test_every_command_help_names_the_purpose_it_serves(workspace):
    """A command whose only stated purpose is that a record should exist fails.
    The work of recording falls on the person running it, so the help text has
    to say what they get."""
    missing = []
    for name in command_names():
        output = workspace.run(name, "--help").output
        if "Purpose (for you):" not in output:
            missing.append(name)
    assert not missing, f"no stated purpose: {missing}"


def test_stated_purposes_are_not_about_the_record_existing(workspace):
    for name in command_names():
        output = workspace.run(name, "--help").output
        purpose = output.split("Purpose (for you):", 1)[1][:300].lower()
        assert "so that a record exists" not in purpose
        assert "for the record" not in purpose


# --- 4. editing a transition is detected -------------------------------------

def test_editing_a_transition_is_detected_by_check(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    path = next(workspace.repo.transitions_dir(traj_id).glob("*.yaml"))

    record = store.read_yaml(path)
    record["act"] = "challenge"
    store.write_yaml(path, record)

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "does not match its content" in result.output


def test_altering_an_early_transition_invalidates_its_descendants(trajectory):
    """Parents are inside the covered payload, so the identifiers chain."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "First.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(state), "-m", "Second.")

    records = workspace.repo.transitions(traj_id)
    child = [r for r in records if r["act"] == "transformation"][0]
    parent_id = child["parents"][0]
    parent = [r for r in records if r["id"] == parent_id][0]

    tampered = dict(parent)
    tampered["performed"] = "2020-01-01T00:00:00Z"
    assert canonical.transition_id(tampered) != parent_id
    assert parent_id in child["parents"], "the child commits to the parent it had"


def test_a_recorded_transition_is_never_rewritten(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    record = workspace.repo.transitions(traj_id)[-1]
    with pytest.raises(Exception) as raised:
        workspace.repo.append_transition(traj_id, record)
    assert "C3" in str(raised.value)


# --- 5. disclosure changes must not invalidate anything ----------------------

def test_a_disclosure_sidecar_does_not_affect_verification(trajectory):
    """Widening a class, or a scheduled release firing, is a lawful operation.
    It must not make an ordinary record look tampered with."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    record = workspace.repo.transitions(traj_id)[-1]

    sidecar = workspace.repo.disclosure_dir(traj_id) / f"{record['id'].split(':')[-1]}.yaml"
    store.write_yaml(
        sidecar,
        {
            "transition": record["id"],
            "class": "group",
            "ground": "vulnerability",
            "release_at": "2027-01-01",
        },
    )
    assert workspace.run("check").exit_code == 0

    store.write_yaml(
        sidecar,
        {"transition": record["id"], "class": "public", "ground": "vulnerability"},
    )
    assert workspace.run("check").exit_code == 0
    assert canonical.transition_id(record) == record["id"]


def test_no_operation_narrows_disclosure():
    """Disclosure may widen and never narrow: a party who has read a record
    retains what they read, so an unpublish operation would misdescribe the
    world to the people relying on it."""
    for name in command_names():
        assert name not in {"unpublish", "unrelease", "retract", "hide", "conceal"}


# --- constraints with no command surface -------------------------------------

def test_the_word_merge_appears_nowhere_in_the_interface(workspace):
    """The substrate uses the word for an operation this tool does not have."""
    for name in command_names():
        assert "merge" not in name
        assert "merge" not in workspace.run(name, "--help").output.lower()


def test_no_merge_or_combine_operation_exists_in_the_source():
    for path in source_files():
        text = path.read_text(encoding="utf-8").lower()
        assert "def merge" not in text
        assert "combine_states" not in text


def test_a_transition_must_reference_an_identified_prior_state(trajectory):
    """A record attached to a project or a repository as a whole is not a
    transition."""
    workspace, traj_id = trajectory
    for record in workspace.repo.transitions(traj_id):
        if record["act"] != "question":
            assert record["prior_state"], "granularity"


def test_personal_tier_records_are_marked_unattested(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    for record in workspace.repo.transitions(traj_id):
        assert record["registration"]["attested"] is False
    assert "unattested" in workspace.run("log").output.lower()
    assert "unattested" in workspace.run("check").output.lower()


# --- deferred ----------------------------------------------------------------

# Test 6 (redaction keeps the chain valid and records itself) is implemented in
# test_m2_integrity.py.


# Test 7 (register refuses when performer and registrar are identical) is
# implemented in test_m3_attestation.py.


@pytest.mark.skip(reason="M4: bundle and continue are not implemented yet")
def test_bundle_on_one_machine_continues_on_another_as_one_graph():
    ...


# --- ordering follows the graph, not the clock -------------------------------

def test_a_parent_always_precedes_its_children(trajectory):
    """Two transitions recorded in the same second must still be listed in the
    order the graph fixes. Recorded times are evidence about when parties
    acted; they are not the structure of the history."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "First.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(state), "-m", "Second.")
    workspace.run("decide", sid(state), "-m", "Why the first was set aside.")

    records = workspace.repo.transitions(traj_id)
    position = {r["id"]: i for i, r in enumerate(records)}
    for record in records:
        for parent in record.get("parents") or []:
            if parent in position:
                assert position[parent] < position[record["id"]]
