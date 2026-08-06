"""M0. Identifiers are deterministic, chain over parents, and exclude the
fields that later lawful operations change."""

from __future__ import annotations

import copy

from grrp import canonical, store


def payload() -> dict:
    return store.new_transition(
        trajectory="trust",
        act="claim",
        performer="key:ed25519:AAAA",
        prior_state="state:sha256:aa",
        posterior_state="state:sha256:bb",
        target="hypothesis",
        performed="2026-08-06T12:00:00Z",
    )


def test_same_payload_yields_the_same_identifier():
    assert payload()["id"] == payload()["id"]


def test_state_identifier_is_over_the_bytes_written():
    content = canonical.normalise_content("  trust is a property  \r\n")
    assert content == "trust is a property\n"
    assert canonical.state_id(content) == (
        "state:sha256:" + canonical.sha256_hex(content.encode("utf-8"))
    )


def test_identifier_changes_when_a_covered_field_changes():
    original = payload()
    altered = copy.deepcopy(original)
    altered["act"] = "challenge"
    assert canonical.transition_id(altered) != original["id"]


def test_identifier_chains_over_parents():
    original = payload()
    altered = copy.deepcopy(original)
    altered["parents"] = ["sha256:deadbeef"]
    assert canonical.transition_id(altered) != original["id"]


def test_identifier_excludes_registration_and_disclosure():
    """Registration is added after the fact at the group tier, and disclosure
    may widen at any time. Either changing the identifier would make ordinary
    operation look like tampering."""
    original = payload()
    altered = copy.deepcopy(original)
    altered["registration"] = {"registrar": "key:ed25519:ZZZZ", "time": "2027-01-01T00:00:00Z"}
    altered["disclosure"] = {"class": "public", "ground": "vulnerability"}
    assert canonical.transition_id(altered) == original["id"]


def test_signing_input_is_stable_under_disclosure_change():
    original = payload()
    first = canonical.signing_input(original["id"], "key:ed25519:B", "2026-08-06T12:00:00Z")
    original["disclosure"] = {"class": "public"}
    second = canonical.signing_input(original["id"], "key:ed25519:B", "2026-08-06T12:00:00Z")
    assert first == second


def test_canonical_form_is_insensitive_to_key_order():
    a = canonical.canonical_bytes({"b": 1, "a": 2})
    b = canonical.canonical_bytes({"a": 2, "b": 1})
    assert a == b
