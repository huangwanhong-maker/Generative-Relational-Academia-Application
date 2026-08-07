"""The local page.

Level 3: an application over the record, outside conformance. It gets tests
anyway, and specifically for the things the design forbids — because a screen
is where the temptation to rank, count and summarise is strongest, and where a
reader would most readily believe a number if one appeared.
"""

from __future__ import annotations

import re
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from conftest import sid
from grrp import ui, views


def page(repo, traj_id, token="t", message=""):
    return ui.trajectory(repo, traj_id, token, message).decode("utf-8")


@pytest.fixture()
def served(workspace):
    """A running page on an ephemeral loopback port."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(workspace.repo, "secret"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield workspace, f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


# --- what it shows -----------------------------------------------------------

def test_the_index_lists_trajectories_without_counting_anything(workspace):
    workspace.run("new", "First question", "--title", "first")
    workspace.run("new", "Second question", "--title", "second")
    workspace.run("claim", "first", "-m", "A position.")

    # The stylesheet uses per-cent for widths, so the check is on the rendered
    # body rather than on the whole document.
    rendered = ui.index(workspace.repo).decode("utf-8").split("</style>")[1].lower()
    assert "first question" in rendered
    assert "second question" in rendered
    for forbidden in ("total", "score", "rank", "progress", "%"):
        assert forbidden not in rendered


def test_a_trajectory_shows_the_question_the_live_position_and_what_is_open(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust is shaped by asymmetry of power.")
    workspace.run("challenge", "-m", "This cannot distinguish trust from compliance.")

    body = page(workspace.repo, traj_id)
    assert "Is trust a property" in body
    assert "asymmetry of power" in body
    assert "compliance" in body
    assert "Unanswered" in body
    assert "entry path" in body


def test_divergence_is_shown_with_neither_branch_principal(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A shared position.")
    shared = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(shared), "-m", "Narrow it to institutions.")
    workspace.run("transform", sid(shared), "-m", "Keep the scope, weaken the claim.")

    body = page(workspace.repo, traj_id)
    assert "Narrow it to institutions." in body
    assert "Keep the scope, weaken the claim." in body
    assert "neither is marked principal" in body
    for forbidden in ("primary branch", "main branch", "default branch", "canonical branch"):
        assert forbidden not in body.lower()


def test_the_page_never_says_merge(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    assert "merge" not in page(workspace.repo, traj_id).lower()
    assert "merge" not in ui.index(workspace.repo).decode("utf-8").lower()
    assert "merge" not in ui.STYLE.lower()


def test_the_page_computes_no_quantity_over_participants_or_trajectories(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    workspace.run("challenge", "-m", "An objection.")
    body = page(workspace.repo, traj_id).lower()

    for forbidden in ("score", "ranking", "leaderboard", "activity", "health", "productivity"):
        assert forbidden not in body
    # No bare tallies of anything.
    assert not re.search(r"\b\d+\s+(transitions|objections|contributions|acts)\b", body)


def test_an_unattested_record_says_so_on_the_page(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    body = page(workspace.repo, traj_id)
    assert "Unattested throughout" in body
    assert "evidence to nobody" in body


def test_a_restriction_shows_its_ground_and_its_residue(trajectory):
    """The residue is the one question a reader can always ask, so the page
    puts it where the restriction is rather than somewhere else."""
    workspace, traj_id = trajectory
    workspace.run("charter", "adopt", "--classes", "private,public")
    workspace.run("claim", traj_id, "-m", "Content our funding depends on.")
    record = workspace.repo.transitions(traj_id)[-1]
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "appropriability")

    body = page(workspace.repo, traj_id)
    assert "appropriability" in body
    assert "negative results" in body, "the residue is shown beside the restriction"
    assert "was what the ground leaves disclosable in fact disclosed" in body
    assert "no control here that takes anything back" in body


def test_a_redacted_state_is_named_rather_than_blank(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Withdrawn material.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("redact", sid(state), "--ground", "erasure_request", "--yes")

    assert "redacted on the ground of erasure_request" in page(workspace.repo, traj_id)


def test_the_page_declares_itself_outside_conformance(trajectory):
    workspace, traj_id = trajectory
    body = page(workspace.repo, traj_id)
    assert "Level 3" in body
    assert "outside conformance" in body
    assert "does not depend on this page existing" in body


# --- what it lets you do -----------------------------------------------------

def test_recording_an_act_from_the_page_writes_the_same_record(trajectory):
    workspace, traj_id = trajectory
    said = ui._perform(
        workspace.repo, traj_id,
        {"act": ["claim"], "message": ["Trust obtains between individuals."], "state": [""]},
    )
    assert "Recorded" in said
    live = views.current_states(workspace.repo, traj_id)
    assert "individuals" in workspace.repo.read_state(traj_id, live[0])
    assert workspace.run("check").exit_code == 0


def test_a_challenge_from_the_page_stands_unresolved(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    ui._perform(
        workspace.repo, traj_id,
        {"act": ["challenge"], "message": ["An objection."], "state": [""]},
    )
    items = views.open_items(workspace.repo, traj_id)
    assert any("An objection." in (item.text or "") for item in items)


def test_abandoning_from_the_page_retires_the_direction(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Approach A.")
    doomed = views.current_states(workspace.repo, traj_id)[0]
    ui._perform(
        workspace.repo, traj_id,
        {"act": ["decide"], "message": ["The assumption failed."], "state": [sid(doomed)],
         "abandon": ["on"]},
    )
    assert doomed not in views.current_states(workspace.repo, traj_id)


def test_the_page_refuses_to_guess_at_a_divergence(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A shared position.")
    shared = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(shared), "-m", "One way.")
    workspace.run("transform", sid(shared), "-m", "Another way.")

    said = ui._perform(
        workspace.repo, traj_id, {"act": ["claim"], "message": ["A position."], "state": [""]}
    )
    assert "none is the canonical one" in said


def test_at_the_group_tier_the_page_proposes_rather_than_records(trajectory):
    from grrp import keys

    workspace, traj_id = trajectory
    other = keys.generate(workspace.repo.keys_dir, "colleague")
    workspace.run("key", "add", "colleague", other)

    said = ui._perform(
        workspace.repo, traj_id, {"act": ["claim"], "message": ["A position."], "state": [""]}
    )
    assert "Proposed" in said
    assert "not in the log until another party registers it" in said
    assert workspace.repo.proposals(traj_id)


def test_the_page_offers_no_way_to_narrow_disclosure_or_approve_an_absorption(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    body = page(workspace.repo, traj_id).lower()
    for forbidden in ("unpublish", "make private", "approve", "veto", "block", "reject"):
        assert forbidden not in body


# --- it is local, and it is not a service ------------------------------------

def test_it_binds_to_loopback_and_needs_a_token_to_write(served):
    workspace, base = served
    workspace.run("new", "A question", "--title", "q")

    assert "A question" in urllib.request.urlopen(f"{base}/").read().decode("utf-8")

    with pytest.raises(urllib.error.HTTPError) as raised:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/t/q/act",
                data=b"act=claim&message=from+another+page&token=wrong",
                method="POST",
            )
        )
    assert raised.value.code == 403
    assert not views.current_states(workspace.repo, "q")


def test_the_protocol_does_not_depend_on_the_page(workspace):
    """Deleting it would leave the record untouched: no module of the record
    imports it, and the command surface loads it only when asked."""
    from pathlib import Path

    source = Path(ui.__file__).parent
    for path in source.glob("*.py"):
        if path.name in {"ui.py", "cli.py"}:
            continue
        assert "import ui" not in path.read_text(encoding="utf-8")
        assert "from .ui" not in path.read_text(encoding="utf-8")
