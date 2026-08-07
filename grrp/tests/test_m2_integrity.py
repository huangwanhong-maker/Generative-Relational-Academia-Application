"""M2. Integrity: the full act vocabulary, and redaction that leaves the record
truthful about its own history."""

from __future__ import annotations

from conftest import sid
from grrp import store, views


# --- completing the act vocabulary -------------------------------------------

def test_connect_to_an_external_work_records_scheme_and_date(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust is shaped by asymmetry of power.")

    workspace.run("connect", "--to", "doi:10.1234/example", "-m", "Same obstruction, other field.")

    connection = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "connection"][0]
    artefact = connection["artefacts"][0]
    assert artefact["ref"] == "doi:10.1234/example"
    assert artefact["scheme"] == "doi"
    assert artefact["referenced_on"], "a reference is uninterpretable without its date"
    assert connection["relation"] == "cito:citesAsRelated"


def test_connect_recognises_identifier_schemes(trajectory):
    for ref, scheme in [
        ("doi:10.1/x", "doi"),
        ("arxiv:2401.00001", "arxiv"),
        ("https://example.org/paper", "url"),
        ("isbn:9780000000000", "isbn"),
        ("Smith 1970, working paper", "other"),
    ]:
        assert store.external_reference(ref)["scheme"] == scheme


def test_connect_to_another_state_is_recorded_in_the_graph(workspace):
    """A link between two states needs no new field: the transition that
    produced the other state becomes a parent, so the link travels with the
    record."""
    workspace.run("new", "First question", "--title", "first")
    workspace.run("claim", "first", "-m", "A position in the first line of work.")
    workspace.run("new", "Second question", "--title", "second")
    workspace.run("claim", "second", "-m", "A position in the second line of work.")

    other = views.current_states(workspace.repo, "first")[0]
    workspace.run("connect", "--to", sid(other), "-t", "second", "-m", "These meet here.")

    connection = [r for r in workspace.repo.transitions("second") if r["act"] == "connection"][0]
    producer = [
        r["id"] for r in workspace.repo.transitions("first")
        if r.get("posterior_state") == other
    ][0]
    assert producer in connection["parents"]


def test_a_failed_verification_stands_on_the_open_register(trajectory):
    """A check that did not come out as predicted is something you owe an
    answer to, and it is also where a stranger could take the work up."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "The method transfers under independence.")

    workspace.run("verify", "--failed", "-m", "Ran it on the target domain; independence fails.")

    verification = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "verification"][0]
    assert verification["disposition"] == "unresolved"
    assert verification["relation"] == "cito:refutes"
    assert any(i.transition["id"] == verification["id"] for i in views.open_items(workspace.repo, traj_id))


def test_a_successful_verification_does_not(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "The method transfers.")
    workspace.run("verify", "-m", "Replicated on three datasets.")

    verification = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "verification"][0]
    assert verification["disposition"] == "accepted"
    assert verification["relation"] == "cito:confirms"


def test_neither_connection_nor_verification_supersedes_the_state(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    before = views.current_states(workspace.repo, traj_id)

    workspace.run("connect", "--to", "doi:10.1/x", "-m", "Related.")
    workspace.run("verify", "-m", "Checked.")

    assert views.current_states(workspace.repo, traj_id) == before


# --- administrative operations ----------------------------------------------

def test_an_operation_is_not_a_transition(trajectory):
    """Administrative activity would otherwise inflate the apparent
    generativity of a trajectory, and readers will count whatever is shown."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("redact", sid(state), "--ground", "personal_data", "--yes")

    operations = [r for r in workspace.repo.transitions(traj_id) if r["kind"] == "operation"]
    assert len(operations) == 1
    # The same envelope, with act, target, relation and disposition absent and
    # an operation field in their place.
    for field in ("act", "target", "relation", "disposition"):
        assert field not in operations[0]
    assert operations[0]["operation"] == "redaction"
    assert operations[0]["ground"] == "personal_data"

    output = workspace.run("log", traj_id).output
    assert "[redaction]" in output
    assert "an operation on the record, not a transition" in output


def test_the_redaction_ground_is_covered_by_the_identifier(trajectory):
    """A ground that could be altered afterwards would be no ground at all."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("redact", sid(state), "--ground", "personal_data", "--yes")

    path = next(
        p for p in workspace.repo.transitions_dir(traj_id).glob("*.yaml")
        if store.read_yaml(p).get("kind") == "operation"
    )
    record = store.read_yaml(path)
    record["ground"] = "legal_order"
    store.write_yaml(path, record)

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "does not match its content" in result.output


# --- acceptance test 6 -------------------------------------------------------

def test_after_redaction_the_chain_verifies_and_the_graph_is_unchanged(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Something a participant later withdraws.")
    doomed = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("transform", sid(doomed), "-m", "A successor built on it.")
    successor = views.current_states(workspace.repo, traj_id)[0]

    graph_before = [
        (r["id"], tuple(r.get("parents") or []), r.get("prior_state"), r.get("posterior_state"))
        for r in workspace.repo.transitions(traj_id)
    ]

    workspace.run("redact", sid(doomed), "--ground", "consent_withdrawn", "--yes")

    # the chain still verifies
    result = workspace.run("check")
    assert result.exit_code == 0
    assert "redacted on the ground of consent_withdrawn" in result.output

    # the graph is unchanged
    graph_after = [
        (r["id"], tuple(r.get("parents") or []), r.get("prior_state"), r.get("posterior_state"))
        for r in workspace.repo.transitions(traj_id)
        if r.get("kind") != "operation"
    ]
    assert graph_after == graph_before

    # the content is gone, the successor survives, and the removal is recorded
    assert workspace.repo.read_state(traj_id, doomed) is None
    assert workspace.repo.read_state(traj_id, successor) is not None
    assert doomed in views.redactions(workspace.repo, traj_id)


def test_a_redacted_state_says_so_rather_than_going_blank(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Withdrawn material.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("release", sid(state))
    workspace.run("redact", sid(state), "--ground", "erasure_request", "--yes")

    assert "redacted on the ground of erasure_request" in workspace.run("show", traj_id).output

    release = workspace.repo.releases(traj_id)[0]
    document = workspace.run("export", sid(release["id"])).output
    assert "content redacted on the ground of erasure_request" in document
    assert "the record of the removal remain" in document


def test_content_missing_without_a_recorded_redaction_fails(trajectory):
    """A gap nobody can account for is tampering, not separability."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]

    workspace.repo.state_path(traj_id, state).unlink()

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "no redaction was recorded" in result.output


def test_redaction_refuses_an_unknown_ground(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]
    result = workspace.run("redact", sid(state), "--ground", "because", "--yes", expect_ok=False)
    assert result.exit_code == 1
    assert "erasure_request" in result.output


def test_redaction_warns_that_git_history_still_holds_the_content(trajectory):
    """Possibility is not lawfulness, and the tool should not imply otherwise."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]
    output = workspace.run("redact", sid(state), "--ground", "personal_data", "--yes").output
    assert "earlier git commits still contain the removed text" in output
    assert "beyond reach" in output
