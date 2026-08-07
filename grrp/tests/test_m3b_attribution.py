"""M3b. Attribution and absorption.

This is where the difference between a generative arrangement and a competitive
one becomes visible in the record. An arrangement is competitive where the work
of entrants who were not selected leaves no trace in the work that proceeds, and
generative where content originating in unselected work enters what proceeds and
is attributed to the party who produced it. The distinction turns on what
becomes of unselected work, not on openness of entry.
"""

from __future__ import annotations

import re

import pytest

from conftest import sid
from grrp import keys, views


@pytest.fixture()
def pair(workspace):
    repo = workspace.repo
    other = keys.generate(repo.keys_dir, "colleague")
    workspace.run("key", "add", "colleague", other)
    workspace.run("new", "Is trust a property between individuals?", "--title", "trust")
    return workspace, "trust", other


# --- attribution attaches to an act ------------------------------------------

def test_a_contributor_is_recorded_with_a_credit_role(trajectory, workspace_key):
    workspace, traj_id = trajectory
    workspace.run(
        "claim", traj_id, "-m", "Trust is shaped by asymmetry of power.",
        "--contributor", f"{workspace_key}=Conceptualization",
    )
    record = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "claim"][0]
    assert record["contributions"] == [
        {"party": workspace.repo.party(), "role": "credit:Conceptualization"}
    ]


def test_roles_are_bound_to_credit_not_invented(trajectory, workspace_key):
    workspace, traj_id = trajectory
    result = workspace.run(
        "claim", traj_id, "-m", "A position.",
        "--contributor", f"{workspace_key}=ChiefThinker", expect_ok=False,
    )
    assert result.exit_code == 1
    assert "Conceptualization" in result.output


def test_a_contributor_must_be_a_party_the_record_knows(trajectory):
    workspace, traj_id = trajectory
    result = workspace.run(
        "claim", traj_id, "-m", "A position.",
        "--contributor", "stranger=Methodology", expect_ok=False,
    )
    assert result.exit_code == 1
    assert "grrp key add" in result.output


def test_attribution_is_stored_as_an_identifier_not_a_label(trajectory, workspace_key):
    """A record holding the word 'Methodology' is uninterpretable once a second
    vocabulary uses the same word differently."""
    workspace, traj_id = trajectory
    workspace.run(
        "claim", traj_id, "-m", "A position.",
        "--contributor", f"{workspace_key}=methodology",
    )
    record = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "claim"][0]
    assert record["contributions"][0]["role"] == "credit:Methodology"


# --- absorption --------------------------------------------------------------

def test_absorption_credits_whoever_produced_the_state(workspace):
    """The party credited is looked up from the record, so nobody has to find a
    key and type it."""
    workspace.run("new", "First question", "--title", "first")
    workspace.run("claim", "first", "-m", "An approach that was not selected.")
    unselected = views.current_states(workspace.repo, "first")[0]

    workspace.run("new", "Second question", "--title", "second")
    workspace.run(
        "claim", "second", "-m", "The line of work that proceeded.",
        "--from", sid(unselected),
    )

    record = [r for r in workspace.repo.transitions("second") if r["act"] == "claim"][0]
    link = record["absorption"][0]
    assert link["state"] == unselected
    assert link["party"] == workspace.repo.party()


def test_the_absorption_test_is_answerable_from_the_record(workspace):
    """Whether an arrangement absorbs or discards is checkable by a reader, and
    the check is performed by them rather than by the protocol."""
    workspace.run("new", "Question", "--title", "q")
    workspace.run("claim", "q", "-m", "A declined proposal's method.")
    declined = views.current_states(workspace.repo, "q")[0]
    workspace.run("transform", sid(declined), "-m", "The selected line, taking that method.",
                  "--from", sid(declined))

    absorbed = views.absorptions(workspace.repo.transitions("q"))
    assert absorbed, "content from unselected work entered what proceeded, with attribution"
    assert absorbed[0]["state"] == declined
    assert absorbed[0]["party"]


def test_absorbing_from_a_state_nobody_produced_is_refused(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    result = workspace.run(
        "transform", "-m", "A successor.", "--from", "deadbeef", expect_ok=False
    )
    assert result.exit_code == 1


# --- no veto -----------------------------------------------------------------

def test_there_is_no_mechanism_to_block_or_approve_an_absorption(workspace):
    """Rights to exclude, multiplied across many small contributions, produce
    the fragmentation in which downstream work needs so many permissions that it
    does not occur. The originator's one instrument is the disclosure class."""
    from grrp.cli import app

    names = [c.name or c.callback.__name__ for c in app.registered_commands]
    for forbidden in ("approve", "deny", "block", "veto", "permit", "consent"):
        assert forbidden not in names

    for name in names:
        help_text = workspace.run(name, "--help").output.lower()
        for forbidden in ("--approve", "--deny", "--block", "--veto", "--require-approval"):
            assert forbidden not in help_text


def test_no_measure_of_how_much_an_absorption_mattered(workspace):
    workspace.run("new", "Question", "--title", "q")
    workspace.run("claim", "q", "-m", "A position.")
    state = views.current_states(workspace.repo, "q")[0]
    workspace.run("transform", "-m", "A successor.", "--from", sid(state))

    for command in (["show"], ["log"], ["check"]):
        output = workspace.run(*command).output.lower()
        # "evidential weight" is the account's own phrase for what a record
        # lacks, not a measure, so the check is for measure-shaped language.
        for forbidden in ("influence", "contribution score", "absorption score", "share of"):
            assert forbidden not in output, (command, forbidden)
        assert not re.search(r"\b\d+\s*%", output), command


# --- contested attribution ---------------------------------------------------

def test_contesting_leaves_both_positions_standing(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position someone else shaped.")
    target = workspace.repo.transitions(traj_id)[-1]

    workspace.run("contest", sid(target["id"]), "-m", "My objection produced this, unnamed.")

    records = workspace.repo.transitions(traj_id)
    original = [r for r in records if r["id"] == target["id"]][0]
    assert original == target, "the disputed record is untouched"

    disputes = views.contested_attributions(workspace.repo, traj_id)
    assert target["id"] in disputes
    assert "attribution is contested" in workspace.run("check").output


def test_nothing_adjudicates_a_contested_attribution(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    target = workspace.repo.transitions(traj_id)[-1]
    output = workspace.run("contest", sid(target["id"]), "-m", "Wrong.").output
    assert "Nobody here decides between them" in output

    from grrp.cli import app
    names = [c.name or c.callback.__name__ for c in app.registered_commands]
    for forbidden in ("resolve", "settle", "adjudicate", "rule"):
        assert forbidden not in names


# --- attribution on a proposal, never on a recorded transition ---------------

def test_attribute_works_on_a_proposal(pair, monkeypatch):
    workspace, traj_id, colleague = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]

    workspace.run("attribute", sid(proposal["id"]), "--contributor", "colleague=Methodology")

    updated = workspace.repo.proposals(traj_id)[0]
    assert updated["contributions"] == [{"party": colleague, "role": "credit:Methodology"}]

    monkeypatch.setenv("GRRP_KEY", "colleague")
    workspace.run("register", sid(updated["id"]))
    record = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "claim"][0]
    assert record["contributions"][0]["party"] == colleague


def test_attributing_a_recorded_transition_is_refused(trajectory):
    """A recorded transition is never edited. If an attribution in the log is
    wrong, that is contested by a further act."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    record = workspace.repo.transitions(traj_id)[-1]

    result = workspace.run(
        "attribute", sid(record["id"]), "--contributor", "self=Methodology", expect_ok=False
    )
    assert result.exit_code == 1
    assert "C3" in result.output
    assert "grrp contest" in result.output


def test_attributing_a_proposal_changes_its_identifier_and_says_so(pair):
    """Contributions and absorption are part of what a transition asserts, so
    they are covered by its identifier."""
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    before = workspace.repo.proposals(traj_id)[0]["id"]

    output = workspace.run(
        "attribute", sid(before), "--contributor", "colleague=Validation"
    ).output

    after = workspace.repo.proposals(traj_id)[0]["id"]
    assert after != before
    assert "identifier changed" in output


# --- synthesis ---------------------------------------------------------------

def test_a_transformation_may_draw_on_several_branches(trajectory):
    """A synthesis is a state its performer composed from what those branches
    reached. It does not close them, and nothing is combined by rule."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A shared position.")
    shared = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(shared), "-m", "Narrow it to institutions.")
    workspace.run("transform", sid(shared), "-m", "Keep the scope, weaken the claim.")
    branches = views.current_states(workspace.repo, traj_id)
    assert len(branches) == 2

    output = workspace.run(
        "transform", sid(branches[0]), "--with", sid(branches[1]),
        "-m", "An account holding both.",
    ).output
    assert "synthesis" in output
    assert "branches it draws on continue" in output

    synthesis = workspace.repo.transitions(traj_id)[-1]
    assert len(synthesis["parents"]) >= 2

    live = views.current_states(workspace.repo, traj_id)
    assert branches[1] in live, "a synthesis does not close the branch it drew on"


def test_synthesis_is_not_called_merge(workspace):
    from grrp.cli import app

    help_text = workspace.run("transform", "--help").output.lower()
    assert "merge" not in help_text
    assert "synthesis" in help_text
    assert "merge" not in [c.name or c.callback.__name__ for c in app.registered_commands]


# --- the release banner is derived, not stored -------------------------------

def test_the_attestation_banner_is_derived_at_export_time(pair, monkeypatch):
    """A flag written when the release was proposed would still say
    "unattested" after the release itself had been registered. Views are
    computed from the log, and this is one of them."""
    workspace, traj_id, _ = pair

    def register_latest():
        proposal = workspace.repo.proposals(traj_id)[0]
        monkeypatch.setenv("GRRP_KEY", "colleague")
        workspace.run("register", sid(proposal["id"]))
        monkeypatch.delenv("GRRP_KEY")

    workspace.run("claim", traj_id, "-m", "A position.")
    register_latest()
    workspace.run("release")
    register_latest()

    release = workspace.repo.releases(traj_id)[0]
    assert "attested" not in release, "nothing derivable is stored"

    document = workspace.run("export", sid(release["id"])).output
    assert "**Unattested.**" not in document
    # The opening question was recorded before the second party existed.
    assert "Partly unattested" in document
