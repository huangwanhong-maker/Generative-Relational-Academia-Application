"""M3a. Keys, signatures and attestation.

The group tier is where credibility begins, and where it comes from is the
whole point: not from the content of a record, its length or its detail, but
from being registered by a party who did not coordinate with the performer.
"""

from __future__ import annotations

import re

import pytest

from conftest import sid
from grrp import canonical, keys, store, views


@pytest.fixture()
def pair(workspace):
    """A record with two parties, acting as the second via GRRP_KEY."""
    repo = workspace.repo
    other = keys.generate(repo.keys_dir, "colleague")
    workspace.run("key", "add", "colleague", other)
    workspace.run("new", "Is trust a property between individuals?", "--title", "trust")
    return workspace, "trust", other


def as_colleague(monkeypatch):
    monkeypatch.setenv("GRRP_KEY", "colleague")


# --- knowing a party ---------------------------------------------------------

def test_adding_a_key_moves_the_record_to_the_group_tier(workspace):
    repo = workspace.repo
    other = keys.generate(repo.keys_dir, "colleague")
    assert repo.tier() == "personal"

    output = workspace.run("key", "add", "colleague", other).output

    assert repo.tier() == "group"
    assert "cannot register your own acts" in output


def test_a_bad_key_is_refused_with_a_useful_message(workspace):
    result = workspace.run("key", "add", "colleague", "not-a-key", expect_ok=False)
    assert result.exit_code == 1
    assert "key:ed25519:" in result.output


def test_key_mine_prints_what_to_hand_to_a_colleague(workspace):
    output = workspace.run("key", "mine").output
    assert workspace.repo.party() in output
    assert "grrp key add" in output


# --- proposal and registration -----------------------------------------------

def test_at_group_tier_an_act_is_a_proposal_and_not_in_the_log(pair):
    workspace, traj_id, _ = pair
    output = workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.").output

    assert "(proposed)" in output
    assert "grrp register" in output
    assert workspace.repo.proposals(traj_id), "the proposal is recorded"
    assert not any(
        r["act"] == "claim" for r in workspace.repo.transitions(traj_id)
    ), "and is not in the log"


def test_registering_by_a_distinct_party_attests_and_signs(pair, monkeypatch):
    workspace, traj_id, colleague = pair
    workspace.run("claim", traj_id, "-m", "Trust obtains between individuals.")
    proposal = workspace.repo.proposals(traj_id)[0]

    as_colleague(monkeypatch)
    output = workspace.run("register", sid(proposal["id"])).output
    assert "attested" in output

    record = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "claim"][0]
    registration = record["registration"]
    assert registration["attested"] is True
    assert registration["registrar"] == colleague
    assert registration["registrar"] != record["performer"]
    assert keys.verify(
        colleague,
        canonical.signing_input(record["id"], colleague, registration["time"]),
        registration["signature"],
    )
    assert not workspace.repo.proposals(traj_id), "the proposal is consumed"


# --- acceptance test 7 -------------------------------------------------------

def test_register_refuses_when_performer_and_registrar_are_identical(pair):
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]

    result = workspace.run("register", sid(proposal["id"]), expect_ok=False)

    assert result.exit_code == 1
    assert "C2" in result.output
    assert "cannot register your own act" in result.output
    assert "did not coordinate" in result.output
    assert workspace.repo.proposals(traj_id), "the proposal is untouched"


def test_registration_does_not_change_the_identifier(pair, monkeypatch):
    """Registration is added after the fact, so it must sit outside the
    identifier: otherwise registering a proposal would change the thing its
    children point at."""
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposed_id = workspace.repo.proposals(traj_id)[0]["id"]

    as_colleague(monkeypatch)
    workspace.run("register", sid(proposed_id))

    record = [r for r in workspace.repo.transitions(traj_id) if r["act"] == "claim"][0]
    assert record["id"] == proposed_id
    assert canonical.transition_id(record) == proposed_id


def test_check_verifies_the_registration_signature(pair, monkeypatch):
    workspace, traj_id, colleague = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]
    as_colleague(monkeypatch)
    workspace.run("register", sid(proposal["id"]))

    assert workspace.run("check").exit_code == 0

    path = workspace.repo.transition_path(traj_id, proposal["id"])
    record = store.read_yaml(path)
    record["registration"]["registrar"] = workspace.repo.profile()["party"]
    store.write_yaml(path, record)

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "signature does not verify" in result.output


def test_a_forged_attestation_flag_is_caught(pair):
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]

    # Write it straight into the log, claiming attestation without a second party.
    forged = dict(proposal)
    forged["registration"] = {
        "registrar": forged["performer"],
        "time": store.now(),
        "attested": True,
        "signature": None,
    }
    store.write_yaml(workspace.repo.transition_path(traj_id, forged["id"]), forged)

    result = workspace.run("check", expect_ok=False)
    assert result.exit_code == 1
    assert "registered by the party who performed it, but marked" in result.output


# --- pending -----------------------------------------------------------------

def test_pending_says_who_each_proposal_waits_on(pair, monkeypatch):
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")

    mine = workspace.run("pending").output
    assert "yours, waiting on another party" in mine

    as_colleague(monkeypatch)
    theirs = workspace.run("pending").output
    assert "waiting on you" in theirs


def test_check_reports_what_is_proposed_but_not_registered(pair):
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    output = workspace.run("check").output
    assert "not yet registered" in output
    assert "Nothing proposed is in the log" in output


# --- withdrawal --------------------------------------------------------------

def test_a_registrar_may_withdraw_and_nothing_is_deleted(pair, monkeypatch):
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]
    as_colleague(monkeypatch)
    workspace.run("register", sid(proposal["id"]))

    workspace.run("withdraw", sid(proposal["id"]), "-m", "This misdescribes what occurred.")

    # A withdrawal is itself an act, so at the group tier it too is a proposal
    # until another party takes responsibility for it. The rule does not bend
    # for the party who happens to be undoing something.
    withdrawal = workspace.repo.proposals(traj_id)[0]
    monkeypatch.delenv("GRRP_KEY")
    workspace.run("register", sid(withdrawal["id"]))

    records = workspace.repo.transitions(traj_id)
    original = [r for r in records if r["id"] == proposal["id"]][0]
    assert original["registration"]["attested"] is True, "the registration stands"
    assert proposal["id"] in views.withdrawn_attestations(workspace.repo, traj_id)
    assert "has withdrawn the attestation" in workspace.run("check").output


def test_only_the_registrar_may_withdraw(pair, monkeypatch):
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]
    as_colleague(monkeypatch)
    workspace.run("register", sid(proposal["id"]))

    monkeypatch.delenv("GRRP_KEY")
    result = workspace.run(
        "withdraw", sid(proposal["id"]), "-m", "Not mine to withdraw.", expect_ok=False
    )
    assert result.exit_code == 1
    assert "withdrawn by the party who made it" in result.output


# --- what attestation does not assert ----------------------------------------

def test_no_aggregate_over_attestations_is_computed(pair, monkeypatch):
    """The natural response to collusion is to measure attestation depth. That
    is a quantity over trajectories, and it would be farmed within a season by
    reciprocal registration."""
    workspace, traj_id, _ = pair
    workspace.run("claim", traj_id, "-m", "A position.")
    proposal = workspace.repo.proposals(traj_id)[0]
    as_colleague(monkeypatch)
    workspace.run("register", sid(proposal["id"]))

    for command in (["log"], ["show"], ["check"], ["state"]):
        output = workspace.run(*command).output.lower()
        assert "attestation depth" not in output
        for forbidden in ("score", "ratio", "count", "index", "depth"):
            assert not re.search(rf"{forbidden}", output), (command, forbidden)
