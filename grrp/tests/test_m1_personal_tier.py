"""M1. The personal tier, which has to be worth using by one person alone.

The trajectory worked here is the philosophy case: a claim about trust, an
objection that it omits institutional power, a transformation accepting the
objection, a second objection that is never resolved, a divergence, and a
release that enumerates the objection still standing.
"""

from __future__ import annotations

from conftest import sid
from grrp import views


def test_init_creates_a_profile_a_key_and_a_gitignored_event_plane(workspace):
    repo = workspace.repo
    profile = repo.profile()
    assert profile["protocol"] == "grrp/0.1"
    assert profile["tier"] == "personal"
    assert profile["party"].startswith("key:ed25519:")
    assert (repo.keys_dir / "self.pub").is_file()
    ignore = (repo.grrp_dir / ".gitignore").read_text(encoding="utf-8")
    assert "events/" in ignore
    assert "keys/*.key" in ignore


def test_new_opens_a_trajectory_whose_question_is_unresolved(trajectory):
    workspace, traj_id = trajectory
    repo = workspace.repo
    records = repo.transitions(traj_id)
    assert len(records) == 1
    assert records[0]["act"] == "question"
    assert records[0]["prior_state"] is None
    assert records[0]["disposition"] == "unresolved"
    assert repo.trajectory(traj_id)["question"].startswith("Is trust")


def test_a_claim_becomes_the_live_state(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    live = views.current_states(workspace.repo, traj_id)
    assert len(live) == 1
    assert "individuals" in workspace.repo.read_state(traj_id, live[0])


def test_a_challenge_does_not_alter_the_state_it_challenges(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    before = views.current_states(workspace.repo, traj_id)

    workspace.run(
        "challenge", sid(before[0]), "-m", "This omits institutional power.", "-t", traj_id
    )

    after = views.current_states(workspace.repo, traj_id)
    assert after == before, "a challenge must not supersede the state it challenges"
    assert len(views.standing_objections(workspace.repo, traj_id, before[0])) == 1


def test_a_transformation_supersedes_and_answers(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    claimed = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("challenge", sid(claimed), "-m", "This omits institutional power.")

    objection = views.standing_objections(workspace.repo, traj_id, claimed)[0]
    workspace.run(
        "transform",
        sid(claimed),
        "-m", "Trust is a process shaped by asymmetry of power.",
        "--relation", "modifies",
        "--answering", sid(objection["id"]),
    )

    live = views.current_states(workspace.repo, traj_id)
    assert len(live) == 1
    assert live[0] != claimed, "the prior state is superseded"
    assert "asymmetry" in workspace.repo.read_state(traj_id, live[0])
    assert views.standing_objections(workspace.repo, traj_id, claimed) == []


def test_an_unanswered_objection_keeps_standing(trajectory):
    """Most objections in theoretical work are never resolved. They stand, and
    the work proceeds beside them."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust is a process shaped by power.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run(
        "challenge", sid(state), "-m", "The revision cannot distinguish trust from compliance."
    )

    items = views.open_items(workspace.repo, traj_id)
    dispositions = {item.transition["disposition"] for item in items}
    assert "unresolved" in dispositions
    result = workspace.run("open")
    assert "compliance" in result.output


def test_divergence_is_preserved_with_no_principal_branch(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust is a process shaped by power.")
    shared = views.current_states(workspace.repo, traj_id)[0]

    workspace.run("transform", sid(shared), "-m", "Narrow the account to institutions.")
    workspace.run("transform", sid(shared), "-m", "Keep the scope and weaken the claim.")

    live = views.current_states(workspace.repo, traj_id)
    assert len(live) == 2, "both directions survive"
    output = workspace.run("state", traj_id).output
    assert "Neither is the canonical one" in output
    for word in ("principal", "canonical branch", "default branch"):
        assert f"marked {word}" not in output


def test_decide_abandon_retires_a_direction_and_keeps_the_reason(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Approach A: assume independence.")
    doomed = views.current_states(workspace.repo, traj_id)[0]

    workspace.run(
        "decide", sid(doomed), "--abandon",
        "-m", "The independence assumption does not hold for the observed data.",
    )

    assert doomed not in views.current_states(workspace.repo, traj_id)
    reasons = [
        workspace.repo.read_state(traj_id, r["posterior_state"])
        for r in workspace.repo.transitions(traj_id)
        if r["act"] == "decision"
    ]
    assert any("independence assumption" in (r or "") for r in reasons)


def test_release_enumerates_standing_objections_and_export_carries_them(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust is a process shaped by asymmetry of power.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run(
        "challenge", sid(state), "-m", "This cannot distinguish trust from compliance."
    )

    result = workspace.run("release", sid(state))
    assert "standing objections enumerated: 1" in result.output

    release = workspace.repo.releases(traj_id)[0]
    assert len(release["standing_objections"]) == 1

    document = workspace.run("export", sid(release["id"])).output
    assert "## Objections standing at release" in document
    assert "compliance" in document
    assert "## Lineage" in document
    assert "## Contributors" in document
    assert "Unattested" in document, "the personal tier carries no evidential weight"


def test_release_cannot_be_made_conditional_on_resolving_objections(trajectory):
    """There is deliberately no flag for it: a release asserts that a state is
    published and that these objections stand, and nothing about their merit."""
    help_text = trajectory[0].run("release", "--help").output
    for forbidden in ("--require-resolved", "--no-objections", "--certify", "--approve"):
        assert forbidden not in help_text


def test_check_passes_on_a_fresh_record(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    result = workspace.run("check")
    assert "ok -" in result.output
