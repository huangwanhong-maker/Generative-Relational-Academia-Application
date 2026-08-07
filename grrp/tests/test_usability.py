"""The usability pass.

None of this changes the record. It changes whether the record gets made at
all, which is the whole question the design turns on: the acts have to cost a
participant less than they are worth to that participant, on the first day,
alone.
"""

from __future__ import annotations

import os
import sys

import pytest

from conftest import sid
from grrp import editor, views


# --- the editor path ---------------------------------------------------------

def test_omitting_the_message_opens_the_editor(trajectory, monkeypatch):
    """Recording a decision with its reason means writing a paragraph. Doing
    that inside shell quotes is friction on the one act the reuse of abandoned
    work depends on."""
    workspace, traj_id = trajectory
    seen = {}

    def fake_edit(template: str, suffix: str = ".md") -> str:
        seen["template"] = template
        return "Trust obtains between individuals.\n" + template

    monkeypatch.setattr(editor, "edit", fake_edit)
    workspace.run("claim", traj_id)

    live = views.current_states(workspace.repo, traj_id)
    assert "individuals" in workspace.repo.read_state(traj_id, live[0])
    assert "What position are you taking?" in seen["template"]


def test_the_prompt_below_the_cut_is_not_recorded(trajectory, monkeypatch):
    workspace, traj_id = trajectory
    monkeypatch.setattr(
        editor, "edit", lambda t, suffix=".md": "The position.\n" + t
    )
    workspace.run("claim", traj_id)
    live = views.current_states(workspace.repo, traj_id)
    content = workspace.repo.read_state(traj_id, live[0])
    assert content.strip() == "The position."
    assert "ignored" not in content


def test_the_decision_prompt_asks_for_the_reason(trajectory, monkeypatch):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Approach A.")
    state = views.current_states(workspace.repo, traj_id)[0]
    seen = {}

    def fake_edit(template: str, suffix: str = ".md") -> str:
        seen["template"] = template
        return "The independence assumption failed.\n" + template

    monkeypatch.setattr(editor, "edit", fake_edit)
    workspace.run("decide", sid(state), "--abandon")
    assert "say what stopped it" in seen["template"]


def test_no_editor_available_says_what_to_do(trajectory, monkeypatch):
    workspace, traj_id = trajectory
    monkeypatch.setattr(editor, "edit", lambda t, suffix=".md": None)
    result = workspace.run("claim", traj_id, expect_ok=False)
    assert result.exit_code == 1
    assert "GRRP_EDITOR" in result.output and "-m" in result.output


def test_an_empty_message_records_nothing(trajectory, monkeypatch):
    workspace, traj_id = trajectory
    monkeypatch.setattr(editor, "edit", lambda t, suffix=".md": t)
    result = workspace.run("claim", traj_id, expect_ok=False)
    assert result.exit_code == 1
    assert "nothing recorded" in result.output
    assert not views.current_states(workspace.repo, traj_id)


def test_editor_discovery_prefers_grrp_editor(monkeypatch):
    monkeypatch.setenv("EDITOR", "vi")
    monkeypatch.setenv("GRRP_EDITOR", "code -w")
    assert editor.find() == ["code", "-w"]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX editor fallback")
def test_editor_discovery_falls_back(monkeypatch):
    for variable in ("GRRP_EDITOR", "VISUAL", "EDITOR"):
        monkeypatch.delenv(variable, raising=False)
    found = editor.find()
    assert found is None or isinstance(found, list)


# --- referring to a state without copying a hash -----------------------------

def test_acts_default_to_the_live_position(trajectory):
    """Copying a hash out of one command's output into the next is the friction
    that stops a tool being used on a Tuesday."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    before = views.current_states(workspace.repo, traj_id)[0]

    workspace.run("challenge", "-m", "This omits institutional power.")

    objections = views.standing_objections(workspace.repo, traj_id, before)
    assert len(objections) == 1


def test_transform_and_release_also_default(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "First position.")
    workspace.run("transform", "-m", "Second position.")
    live = views.current_states(workspace.repo, traj_id)
    assert len(live) == 1
    assert "Second" in workspace.repo.read_state(traj_id, live[0])

    workspace.run("release")
    assert workspace.repo.releases(traj_id)[0]["state"] == live[0]


def test_a_divergence_refuses_to_be_guessed_at(trajectory):
    """Where two positions are live, nothing in the design gives a basis for
    picking one, so the tool asks rather than choosing."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Shared position.")
    shared = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(shared), "-m", "Narrow it to institutions.")
    workspace.run("transform", sid(shared), "-m", "Keep the scope, weaken the claim.")

    result = workspace.run("challenge", "-m", "An objection.", expect_ok=False)
    assert result.exit_code == 1
    assert "several live positions" in result.output
    assert "canonical" in result.output
    assert "Narrow it to institutions." in result.output


# --- the overview ------------------------------------------------------------

def test_show_gives_the_state_of_one_trajectory(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust is shaped by asymmetry of power.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("challenge", sid(state), "-m", "Cannot distinguish trust from compliance.")
    workspace.run("release", sid(state))

    output = workspace.run("show", traj_id).output
    assert "Is trust a property" in output          # the question
    assert "asymmetry of power" in output           # the live position
    assert "compliance" in output                   # what is unanswered
    assert "released" in output
    assert "unattested throughout" in output


def test_show_reports_no_quantity_over_trajectories(workspace):
    workspace.run("new", "First question", "--title", "first")
    workspace.run("new", "Second question", "--title", "second")
    workspace.run("claim", "first", "-m", "A position.")

    output = workspace.run("show").output.lower()
    for forbidden in ("total", "score", "progress", "%", "rank"):
        assert forbidden not in output


def test_show_on_an_empty_record_says_where_to_start(workspace):
    output = workspace.run("show").output
    assert "nothing recorded yet" in output
    assert "grrp new" in output


def test_new_points_at_the_next_act(workspace):
    output = workspace.run("new", "A question", "--title", "q").output
    assert "grrp claim" in output
