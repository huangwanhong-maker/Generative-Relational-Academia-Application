"""M4. The open tier: portability, deposit, sealed registration, custody.

Portability is not export. A system offering a data dump leaves departing
participants with an archive. What makes the difference is that the record can
be continued under an implementation the original operator does not control,
with appended transitions referencing the obtained ones as parents, so the
result is one graph and not two.
"""

from __future__ import annotations

import json
import zipfile

import pytest

from conftest import Workspace, sid
from grrp import canonical, store, views


@pytest.fixture()
def elsewhere(tmp_path_factory) -> Workspace:
    """A second machine: a different repository, a different party."""
    space = Workspace(tmp_path_factory.mktemp("elsewhere"))
    space.run("init")
    return space


# --- acceptance test 8 -------------------------------------------------------

def test_bundle_here_continue_there_is_one_graph_not_two(trajectory, elsewhere, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    workspace.run("challenge", "-m", "This omits institutional power.")
    obtained = [r["id"] for r in workspace.repo.transitions(traj_id)]

    archive = tmp_path / "traj.zip"
    workspace.run("bundle", traj_id, "-o", str(archive))
    assert archive.is_file()

    # No shared service: a file, carried across.
    elsewhere.run("continue", str(archive))

    there = elsewhere.repo.transitions(traj_id)
    assert [r["id"] for r in there] == obtained, "every transition arrived, unaltered"

    # Appended transitions reference the obtained ones as parents.
    elsewhere.run("transform", "-m", "Trust is a process shaped by asymmetry of power.")
    appended = elsewhere.repo.transitions(traj_id)[-1]
    assert appended["parents"], "the continuation attaches to what was obtained"
    assert appended["parents"][0] in obtained

    # One graph: every parent resolves, and check passes.
    known = {r["id"] for r in elsewhere.repo.transitions(traj_id)}
    for record in elsewhere.repo.transitions(traj_id):
        for parent in record.get("parents") or []:
            assert parent in known
    assert elsewhere.run("check").exit_code == 0


def test_a_bundle_needs_nobody_s_permission_and_no_service(trajectory, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    workspace.run("bundle", "-o", str(tmp_path / "b.zip"))

    with zipfile.ZipFile(tmp_path / "b.zip") as archive:
        names = archive.namelist()
    assert "manifest.yaml" in names
    assert "profile.yaml" in names
    assert any(n.startswith(f"trajectories/{traj_id}/transitions/") for n in names)
    assert any(n.startswith(f"trajectories/{traj_id}/states/") for n in names)
    assert not any(n.startswith("keys/") and n.endswith(".key") for n in names)


# --- received records are never altered --------------------------------------

def test_received_records_are_copied_byte_for_byte(trajectory, elsewhere, tmp_path):
    """The prohibition on alteration extends to normalisation: rewriting a
    received record into this tool's preferred form would invalidate its
    signature."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))
    elsewhere.run("continue", str(archive))

    for path in workspace.repo.transitions_dir(traj_id).glob("*.yaml"):
        mirrored = elsewhere.repo.transitions_dir(traj_id) / path.name
        assert mirrored.read_bytes() == path.read_bytes()


def test_continuing_twice_leaves_what_is_already_held_untouched(trajectory, elsewhere, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))
    elsewhere.run("continue", str(archive))

    output = elsewhere.run("continue", str(archive)).output
    assert "already held, untouched" in output
    assert elsewhere.run("check").exit_code == 0


def test_a_version_it_cannot_read_is_retained_unprocessed(trajectory, elsewhere, tmp_path):
    """A record created under one version asserts what that version's fields
    meant, so it is not read as though it were of another."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))

    with zipfile.ZipFile(archive) as source:
        contents = {name: source.read(name) for name in source.namelist()}
    contents["manifest.yaml"] = contents["manifest.yaml"].replace(b"grrp/0.1", b"grrp/9.9")
    with zipfile.ZipFile(archive, "w") as target:
        for name, data in contents.items():
            target.writestr(name, data)

    result = elsewhere.run("continue", str(archive), expect_ok=False)
    assert result.exit_code == 1
    assert "Kept unprocessed" in result.output
    assert not elsewhere.repo.trajectory_ids(), "nothing was processed"


def test_an_unverifiable_signature_is_retained_and_marked(trajectory, elsewhere, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    record = workspace.repo.transitions(traj_id)[-1]

    path = workspace.repo.transition_path(traj_id, record["id"])
    forged = store.read_yaml(path)
    forged["registration"] = {
        "registrar": "key:ed25519:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "time": store.now(),
        "attested": True,
        "signature": "bm90LWEtc2lnbmF0dXJl",
    }
    store.write_yaml(path, forged)

    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))
    output = elsewhere.run("continue", str(archive)).output

    assert "unverified" in output
    assert "retained and marked, not discarded" in output
    assert elsewhere.repo.transition_path(traj_id, record["id"]).is_file()


def test_a_partial_record_is_not_filled_in(trajectory, elsewhere, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "First.")
    workspace.run("transform", "-m", "Second.")
    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))

    # Drop the opening transition from the bundle.
    with zipfile.ZipFile(archive) as source:
        contents = {n: source.read(n) for n in source.namelist()}
    opening = [
        r for r in workspace.repo.transitions(traj_id) if r["act"] == "question"
    ][0]
    name = f"trajectories/{traj_id}/transitions/{opening['id'].split(':')[-1]}.yaml"
    contents.pop(name)
    with zipfile.ZipFile(archive, "w") as target:
        for key, data in contents.items():
            target.writestr(key, data)

    output = elsewhere.run("continue", str(archive)).output
    assert "parents not present" in output
    assert "nothing has been synthesised" in output
    assert opening["id"] not in {r["id"] for r in elsewhere.repo.transitions(traj_id)}


def test_divergent_continuation_is_a_divergence(trajectory, elsewhere, tmp_path):
    """Two parties continuing the same obtained record independently produce two
    graphs sharing a common ancestry. Both are retained, neither is principal,
    and no reconciliation is required or provided."""
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A shared position.")
    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))
    elsewhere.run("continue", str(archive))

    workspace.run("transform", "-m", "One way onward.")
    elsewhere.run("transform", "-m", "Another way onward.")

    back = tmp_path / "back.zip"
    elsewhere.run("bundle", "-o", str(back))
    workspace.run("continue", str(back))

    live = views.current_states(workspace.repo, traj_id)
    assert len(live) == 2, "both directions are retained"
    assert "Neither is the canonical one" in workspace.run("state", traj_id).output
    assert workspace.run("check").exit_code == 0


# --- restricted content does not travel by default ---------------------------

def test_restricted_content_is_withheld_and_the_withholding_is_named(trajectory, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("charter", "adopt", "--classes", "private,public")
    workspace.run("claim", traj_id, "-m", "Content our funding depends on.")
    record = workspace.repo.transitions(traj_id)[-1]
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "appropriability")

    output = workspace.run("bundle", "-o", str(tmp_path / "b.zip")).output
    assert "content withheld" in output
    assert "skeletons travelling without it" in output

    with zipfile.ZipFile(tmp_path / "b.zip") as archive:
        names = archive.namelist()
    withheld = record["posterior_state"].split(":")[-1]
    assert f"trajectories/{traj_id}/states/{withheld}.md" not in names
    assert any(n.endswith(f"{record['id'].split(':')[-1]}.yaml") for n in names), "the skeleton travels"


def test_withheld_content_is_accounted_for_rather_than_treated_as_tampering(
    trajectory, elsewhere, tmp_path
):
    workspace, traj_id = trajectory
    workspace.run("charter", "adopt", "--classes", "private,public")
    workspace.run("claim", traj_id, "-m", "Restricted content.")
    record = workspace.repo.transitions(traj_id)[-1]
    workspace.run("disclose", sid(record["id"]), "--class", "private", "--ground", "hazard")

    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))
    elsewhere.run("continue", str(archive))

    result = elsewhere.run("check")
    assert result.exit_code == 0, "a gap the record explains is not tampering"
    assert "withheld when this record was obtained" in result.output


# --- the declaration ---------------------------------------------------------

def test_the_profile_declaration_is_machine_readable(workspace):
    output = workspace.run("profile", "--json").output
    data = json.loads(output)
    for key in ("protocol", "hash", "canonicalisation", "covered_fields", "signing_input"):
        assert key in data
    assert "registration" in data["excluded_fields"]
    assert "disclosure" in data["excluded_fields"]


def test_the_declaration_under_which_records_arrived_is_recorded(trajectory, elsewhere, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    archive = tmp_path / "b.zip"
    workspace.run("bundle", "-o", str(archive))
    elsewhere.run("continue", str(archive))

    receipts = list((elsewhere.repo.grrp_dir / "received").glob("*.yaml"))
    assert receipts
    receipt = store.read_yaml(receipts[0])
    assert receipt["manifest"]["declaration"]["canonicalisation"] == canonical.CANONICALISATION


# --- deposit -----------------------------------------------------------------

def test_deposit_packages_released_material_only(trajectory, tmp_path):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("release", sid(state))
    release = workspace.repo.releases(traj_id)[0]

    directory = tmp_path / "deposit"
    workspace.run("deposit", sid(release["id"]), "-o", str(directory))

    assert (directory / "release.md").is_file()
    assert (directory / "declaration.yaml").is_file()
    assert (directory / "record.zip").is_file()
    assert "lineage" in (directory / "release.md").read_text(encoding="utf-8").lower()


def test_a_deposit_identifier_is_recorded_in_the_trajectory(trajectory):
    workspace, traj_id = trajectory
    workspace.run("claim", traj_id, "-m", "A position.")
    state = views.current_states(workspace.repo, traj_id)[0]
    workspace.run("release", sid(state))
    release = workspace.repo.releases(traj_id)[0]

    workspace.run("deposit", sid(release["id"]), "--identifier", "doi:10.5281/zenodo.1")

    deposits = [
        r for r in workspace.repo.transitions(traj_id)
        if r.get("operation") == "deposit_recorded"
    ]
    assert deposits[0]["payload"]["identifier"] == "doi:10.5281/zenodo.1"
    assert deposits[0]["payload"]["scheme"] == "doi"
    assert workspace.run("check").exit_code == 0


# --- sealed registration -----------------------------------------------------

def test_sealing_records_that_something_was_held_without_saying_what(trajectory):
    workspace, traj_id = trajectory
    workspace.run("seal", traj_id, "-m", "An idea I am not ready to show anyone.")

    record = workspace.repo.transitions(traj_id)[-1]
    state_id = record["posterior_state"]
    assert not workspace.repo.state_path(traj_id, state_id).is_file(), "nothing is disclosed"
    assert (workspace.repo.grrp_dir / "sealed" / f"{state_id.split(':')[-1]}.md").is_file()

    ignore = (workspace.repo.grrp_dir / ".gitignore").read_text(encoding="utf-8")
    assert "sealed/" in ignore

    result = workspace.run("check")
    assert result.exit_code == 0
    assert "sealed" in result.output
    assert "generates nothing while sealed" in result.output


def test_opening_a_seal_lets_anyone_check_it_against_the_identifier(trajectory):
    workspace, traj_id = trajectory
    workspace.run("seal", traj_id, "-m", "Held on the first day.")
    record = workspace.repo.transitions(traj_id)[-1]
    state_id = record["posterior_state"]

    workspace.run("openseal", sid(state_id))

    content = workspace.repo.read_state(traj_id, state_id)
    assert content is not None
    assert canonical.state_id(content) == state_id, "it yields the identifier registered earlier"


def test_sealing_says_a_timestamp_is_not_evidence_unless_anchored(trajectory):
    workspace, traj_id = trajectory
    output = workspace.run("seal", traj_id, "-m", "Something.").output
    assert "your own assertion" in output
    assert "a medium you do not control" in output


def test_sealing_never_claims_priority(workspace):
    # Rich wraps help across lines, so compare on normalised whitespace.
    help_text = " ".join(workspace.run("seal", "--help").output.split())
    assert "does not establish priority" in help_text
    assert "priority is a community's recognition of a claim" in help_text
    assert "generates nothing" in help_text


# --- custody and succession --------------------------------------------------

def test_custody_of_one_party_is_named_as_insufficient(workspace):
    output = workspace.run("custody", "show").output
    assert "does not survive that party" in output


def test_custody_and_succession_are_recorded_in_the_profile(workspace):
    workspace.run("custody", "add", "the departmental archive")
    workspace.run("custody", "succession", "passes to the Serendip Commons Society")

    profile = workspace.repo.profile()
    assert "the departmental archive" in profile["custody"]
    assert "Serendip" in profile["succession"]
    assert "Serendip" in workspace.run("custody", "show").output
