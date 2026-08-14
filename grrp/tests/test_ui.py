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
from grrp import accounts, canonical, ui, views


def page(repo, traj_id, token="t", message=""):
    return ui.trajectory(repo, traj_id, token, message).decode("utf-8")


@pytest.fixture()
def served(workspace):
    """A running page on an ephemeral loopback port, with one signed-in account.

    Signed in as a fixture rather than per test, because every test below is
    about what the page does once you are past the door. What happens at the
    door has its own tests.
    """
    accounts.create(workspace.path, "tester", "a-good-enough-password")
    sessions = ui.Sessions()
    ticket = sessions.begin("tester")
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), ui.make_handler(workspace.repo, "secret", sessions)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield workspace, Client(f"http://127.0.0.1:{server.server_port}", ticket)
    server.shutdown()
    server.server_close()


class Client:
    """A browser that is signed in: it carries the session cookie."""

    def __init__(self, base: str, ticket: str) -> None:
        self.base = base
        self.cookie = f"{ui.COOKIE}={ticket}"

    def __str__(self) -> str:
        return self.base

    def request(self, path: str, data: bytes | None = None, method: str = "GET"):
        return urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={"Cookie": self.cookie},
        )

    def get(self, path: str = "/") -> str:
        return urllib.request.urlopen(self.request(path)).read().decode("utf-8")


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
    """The substrate uses the word for an operation this tool does not have,
    so borrowing it would make every reader expect behaviour the record has no
    way to provide."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")

    def rendered(payload: bytes) -> str:
        # The record's directory name is shown as its title, and under pytest
        # that is the name of this test.
        return payload.decode("utf-8").lower().replace(workspace.repo.root.name.lower(), "")

    assert "merge" not in rendered(ui.trajectory(workspace.repo, traj_id, "t"))
    assert "merge" not in rendered(ui.index(workspace.repo))
    assert "merge" not in ui.STYLE.lower()
    assert "merge" not in " ".join(ui.ACTS.values()).lower()


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
    # The rendered body, not the stylesheet: CSS says "display:block" about
    # boxes and means nothing about disclosure.
    body = page(workspace.repo, traj_id).split("</style>")[1].lower()
    for forbidden in ("unpublish", "make private", "approve", "veto", "block", "reject"):
        assert forbidden not in body


# --- it is local, and it is not a service ------------------------------------

def test_it_binds_to_loopback_and_needs_a_token_to_write(served):
    workspace, client = served
    workspace.run("new", "A question", "--title", "q")

    assert "A question" in client.get("/")

    with pytest.raises(urllib.error.HTTPError) as raised:
        urllib.request.urlopen(
            client.request(
                "/t/q/act",
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


# --- starting a record from the page -----------------------------------------

def test_the_page_runs_where_no_record_exists_and_offers_to_start_one(tmp_path):
    """It has to: otherwise the first thing anyone meets is a terminal."""
    space = ui.Workspace(tmp_path)
    assert space.records() == []

    body = ui.records_index(space, "tok").decode("utf-8")
    assert "Start a record" in body
    assert "question you are actually trying to answer" in body.lower()


def test_creating_a_record_makes_a_git_repository_and_opens_the_question(tmp_path):
    from grrp import actions, gitutil

    repo, traj_id = actions.create_record(
        tmp_path, "Trust and power", "Is trust a property between individuals?", use_git=True
    )

    assert repo.root.name == "trust-and-power"
    assert repo.profile_path.is_file()
    assert repo.trajectory(traj_id)["question"].startswith("Is trust")
    if gitutil.available():
        assert (repo.root / ".git").is_dir()
        assert gitutil.in_work_tree(repo.root)


def test_a_record_works_without_git(tmp_path):
    """Version control is a substrate, not a requirement."""
    from grrp import actions

    repo, traj_id = actions.create_record(tmp_path, "no vcs", "A question?", use_git=False)
    assert not (repo.root / ".git").exists()
    assert repo.transitions(traj_id)


def test_records_are_listed_without_being_ordered_or_counted(tmp_path):
    from grrp import actions

    actions.create_record(tmp_path, "first", "First question?", use_git=False)
    actions.create_record(tmp_path, "second", "Second question?", use_git=False)

    rendered = ui.records_index(ui.Workspace(tmp_path), "tok").decode("utf-8")
    rendered = rendered.split("</style>")[1].lower()
    assert "first question" in rendered and "second question" in rendered
    for forbidden in ("total", "score", "rank", "most", "least", "%"):
        assert forbidden not in rendered


# --- the drawing -------------------------------------------------------------

def test_the_trajectory_is_drawn(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    workspace.run("challenge", "-m", "This omits institutional power.")

    svg = ui.graph(workspace.repo, traj_id)
    assert svg.startswith("<div class='scroll'><svg")
    assert "Trust obtains between" in svg
    assert "question" in svg and "position" in svg and "objection" in svg
    assert "challenge" in svg, "edges are labelled by the act that made them"


def test_a_divergence_is_drawn_with_neither_branch_favoured(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A shared position.")
    shared = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(shared), "-m", "Narrow it to institutions.")
    workspace.run("transform", sid(shared), "-m", "Keep the scope, weaken the claim.")

    svg = ui.graph(workspace.repo, traj_id)
    assert "Narrow it to" in svg and "Keep the scope" in svg
    assert svg.count("n-box live") == 2, "both drawn identically; nothing marks one as the line"
    assert "merge" not in svg.lower()


def test_the_drawing_carries_no_quantity(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    workspace.run("challenge", "-m", "An objection.")
    svg = ui.graph(workspace.repo, traj_id).lower()
    for forbidden in ("score", "rank", "total", "count"):
        assert forbidden not in svg


def test_a_redacted_state_is_named_in_the_drawing(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Withdrawn material.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("redact", sid(state), "--ground", "erasure_request", "--yes")
    assert "redacted on the ground of" in ui.graph(workspace.repo, traj_id)


def test_an_empty_trajectory_draws_without_failing(workspace):
    workspace.run("new", "A question", "--title", "q")
    assert "<svg" in ui.graph(workspace.repo, "q")


# --- more acts from the page -------------------------------------------------

def test_releasing_from_the_page_enumerates_standing_objections(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    workspace.run("challenge", "-m", "An objection that stands.")

    said = ui._perform(workspace.repo, traj_id, {"act": ["release"], "state": [""]})
    assert "enumerating the objections that stand" in said
    assert "nothing about their merit" in said
    assert len(workspace.repo.releases(traj_id)[0]["standing_objections"]) == 1


def test_connecting_from_the_page_records_the_scheme_and_the_date(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    ui._perform(
        workspace.repo, traj_id,
        {"act": ["connect"], "message": ["Same obstruction."], "to": ["doi:10.1234/x"],
         "state": [""]},
    )
    connection = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "connection"][0]
    assert connection["artefacts"][0]["scheme"] == "doi"
    assert connection["artefacts"][0]["referenced_on"]


def test_a_connection_with_nothing_to_connect_to_is_refused(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    said = ui._perform(
        workspace.repo, traj_id,
        {"act": ["connect"], "message": ["Related."], "to": [""], "state": [""]},
    )
    assert "needs something to connect to" in said


def test_a_failed_check_from_the_page_stands_unresolved(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "The method transfers.")
    ui._perform(
        workspace.repo, traj_id,
        {"act": ["verify"], "message": ["It did not."], "failed": ["on"], "state": [""]},
    )
    verification = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "verification"][0]
    assert verification["disposition"] == "unresolved"
    assert verification["relation"] == "cito:refutes"


def test_registering_from_the_page_refuses_your_own_act(trajectory):
    from grrp import actions, keys

    workspace, traj_id = trajectory
    other = keys.generate(workspace.repo.keys_dir, "colleague")
    workspace.run("key", "add", "colleague", other)
    ui._perform(workspace.repo, traj_id,
                {"act": ["claim"], "message": ["A position."], "state": [""]})
    proposal = workspace.repo.proposals(traj_id)[0]

    with pytest.raises(Exception) as raised:
        actions.register_proposal(workspace.repo, traj_id, proposal)
    assert "C2" in str(raised.value)


def test_the_page_and_the_terminal_write_the_same_record(trajectory):
    """A record made from a page and one made from a terminal must be the same
    record, or the page is a second implementation rather than an application
    over the first."""
    workspace, traj_id = trajectory
    ui._perform(workspace.repo, traj_id,
                {"act": ["claim"], "message": ["From the page."], "state": [""]})
    from_page = workspace.repo.transitions(traj_id)[-1]

    assert from_page["protocol"] == "grrp/0.1"
    assert from_page["kind"] == "transition"
    assert from_page["id"] == canonical.transition_id(from_page)
    assert workspace.run("check").exit_code == 0


# --- the drawing as a file ---------------------------------------------------

def test_the_exported_drawing_is_well_formed_xml(trajectory):
    """An .svg file is parsed as XML, not HTML: unquoted attributes are legal
    in a page and are a parse error in a file."""
    import xml.etree.ElementTree as ET

    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    workspace.run("challenge", "-m", "An objection.")

    svg = ui.standalone_svg(workspace.repo, traj_id)
    root = ET.fromstring(svg.split("?>", 1)[1])
    assert root.tag.endswith("svg")


def test_the_exported_drawing_carries_its_own_colours_and_nothing_else(trajectory):
    """It will be looked at on a light background and a dark one, and there is
    no telling which. It must also reach for nothing: a drawing that phones
    somewhere is not a drawing of a record that needs no network."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")

    svg = ui.standalone_svg(workspace.repo, traj_id)
    assert "prefers-color-scheme: dark" in svg
    assert "<script" not in svg
    assert svg.count("http") == svg.count("http://www.w3.org"), "no external references"


def test_grrp_graph_writes_a_file(trajectory, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    out = tmp_path / "traj.svg"
    workspace.run("graph", traj_id, "-o", str(out))
    assert out.is_file()
    assert out.read_text(encoding="utf-8").startswith("<?xml")


def test_graphing_an_empty_trajectory_refuses_rather_than_writing_nothing(workspace):
    workspace.run("new", "A question", "--title", "q")
    # The opening question is a state, so there is something to draw.
    assert "<svg" in ui.standalone_svg(workspace.repo, "q")


# --- the cover ---------------------------------------------------------------

def cover(space, token="tok", message="", query=""):
    return ui.records_index(space, token, message, query).decode("utf-8")


def test_the_cover_shows_the_questions_not_just_the_directory_names(tmp_path):
    from grrp import actions

    repo, _ = actions.create_record(
        tmp_path, "trust", "Is trust a property between individuals?", use_git=False
    )
    from conftest import Workspace as W

    W(repo.root).run("claim", "-m", "Trust obtains between individuals.")

    body = cover(ui.Workspace(tmp_path))
    assert "Is trust a property between individuals?" in body
    assert "Trust obtains between individuals." in body, "the live position is on the cover"


def test_the_cover_marks_what_is_unanswered(tmp_path):
    from conftest import Workspace as W
    from grrp import actions

    repo, _ = actions.create_record(tmp_path, "q", "A question?", use_git=False)
    space = W(repo.root)
    space.run("claim", "-m", "A position.")
    space.run("challenge", "-m", "An objection nobody has answered.")

    body = cover(ui.Workspace(tmp_path))
    assert "unanswered" in body
    assert "An objection nobody has answered." in body


def test_the_cover_offers_both_ways_in(tmp_path):
    """Creating a record and continuing someone else's are the two doors, and a
    community reaches you through the second."""
    body = cover(ui.Workspace(tmp_path))
    assert "Start a record" in body
    assert "Continue someone's record" in body
    assert "path to a bundle they sent you" in body


def test_the_cover_says_there_is_no_directory_of_other_people(tmp_path):
    body = cover(ui.Workspace(tmp_path))
    assert "no directory of other" in body
    assert "party to every entry" in body


# --- search ------------------------------------------------------------------

def test_search_finds_a_question_a_title_and_a_position(tmp_path):
    from conftest import Workspace as W
    from grrp import actions

    repo, _ = actions.create_record(
        tmp_path, "trust", "Is trust a property between individuals?", use_git=False
    )
    W(repo.root).run("claim", "-m", "Trust is shaped by asymmetry of power.")
    actions.create_record(tmp_path, "transfer", "Does the method transfer?", use_git=False)

    space = ui.Workspace(tmp_path)
    assert [h.record for h in ui.search(space, "trust")] == ["trust"]
    assert [h.record for h in ui.search(space, "transfer")] == ["transfer"]

    deep = ui.search(space, "asymmetry")
    assert deep and deep[0].where == "claim", "it looks inside the states, not just the titles"
    assert "asymmetry" in deep[0].snippet


def test_search_is_case_insensitive_and_empty_finds_nothing(tmp_path):
    from grrp import actions

    actions.create_record(tmp_path, "trust", "Is TRUST a property?", use_git=False)
    space = ui.Workspace(tmp_path)
    assert ui.search(space, "trust")
    assert ui.search(space, "  ") == []


def test_search_filters_and_does_not_order_by_relevance(tmp_path):
    """An ordering by relevance is a measure over trajectories, and a measure
    adopted to direct attention becomes the thing people work towards."""
    from grrp import actions

    for name in ("aaa", "bbb", "ccc"):
        actions.create_record(tmp_path, name, f"A question about trust in {name}?", use_git=False)

    space = ui.Workspace(tmp_path)
    listed = [name for name, _ in space.records()]
    assert [h.record for h in ui.search(space, "trust")] == listed, (
        "matches come back in the order everything else is listed in"
    )

    body = cover(space, query="trust")
    assert "does not rank" in body
    assert "<mark>" in body, "the match is shown, not scored"

    # The page explains why it does not order by relevance, so the check is for
    # a measure being shown rather than for the word being mentioned.
    rendered = body.split("</style>")[1].lower()
    for forbidden in ("best match", "top result", "% match", "relevance:"):
        assert forbidden not in rendered
    assert not re.search(r"\d+(\.\d+)?\s*(%|points|pts)", rendered)


def test_a_search_that_finds_nothing_says_so(tmp_path):
    from grrp import actions

    actions.create_record(tmp_path, "trust", "A question?", use_git=False)
    assert "Nothing here mentions that" in cover(ui.Workspace(tmp_path), query="quarks")


# --- the acts are buttons now ------------------------------------------------

def test_every_act_is_a_button_that_says_what_it_does(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    body = page(workspace.repo, traj_id)

    for label in ("Take a position", "Object to this", "Record a decision",
                  "Abandon this direction", "Record a check", "Connect to it",
                  "Publish this state"):
        assert label in body, label
    assert "<select" not in body, "no assembling the act out of parts first"


def test_pressing_a_button_performs_that_act(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Approach A.")
    doomed = views.current_states(workspace.repo, traj_id)[0]

    ui._perform(
        workspace.repo, traj_id,
        {"act": ["abandon"], "message": ["The assumption failed."], "state": [sid(doomed)]},
    )
    assert doomed not in views.current_states(workspace.repo, traj_id)


def test_an_act_the_tool_does_not_have_is_refused(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    said = ui._perform(
        workspace.repo, traj_id,
        {"act": ["merge"], "message": ["Combine them."], "state": [""]},
    )
    assert "not an act" in said


# --- continuing someone's record from the page -------------------------------

def test_a_bundle_can_be_continued_from_the_cover(trajectory, tmp_path, served):
    import urllib.parse

    source, _ = trajectory
    source.run("claim", "-m", "A position from somewhere else.")
    archive = tmp_path / "traj.zip"
    source.run("bundle", "-o", str(archive))

    receiver, client = served
    data = urllib.parse.urlencode({"token": "secret", "bundle": str(archive)}).encode()

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(client.request("/continue", data=data, method="POST"))
    except urllib.error.HTTPError as redirect:
        assert redirect.code == 303
        assert "Continued" in urllib.parse.unquote(redirect.headers["Location"])

    assert receiver.repo.trajectory_ids(), "the record arrived"
    assert receiver.run("check").exit_code == 0
