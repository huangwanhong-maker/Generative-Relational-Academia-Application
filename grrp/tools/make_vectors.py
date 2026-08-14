"""Generate the cross-implementation vector file.

Two implementations of GRRP now exist: this one, and the TypeScript one under
``web/packages/protocol``. They must agree on every identifier for every input,
because an identifier is what a reader elsewhere checks. Agreement is not
something to assert in a README; it is something to fail a test over.

This writes the vectors from the Python side, which is the reference
implementation. The TypeScript suite reads the same file and must reproduce
every value. Where the two disagree the specification is underdetermined, and
the fix belongs in the specification -- not in whichever implementation is
easier to change.

Run:  python grrp/tools/make_vectors.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grrp import canonical, keys  # noqa: E402

OUT = ROOT.parent / "web" / "packages" / "protocol" / "test" / "vectors.json"

# Inputs chosen for the places two implementations drift, not for the places
# they obviously agree.
CANONICAL_CASES: list[tuple[str, object]] = [
    ("empty object", {}),
    ("empty array", []),
    ("null", None),
    ("booleans", [True, False]),
    ("integers", [0, -1, 1, 2**53 - 1]),
    ("nested", {"b": {"d": 1, "c": [1, {"f": None, "e": 2}]}, "a": "x"}),
    # Key order: Python sorts by code point, JavaScript's default sort compares
    # UTF-16 code units, and the two orderings differ once a key leaves the
    # basic plane.
    ("non-ascii keys", {"z": 1, "\u00e9": 2, "a": 3, "\u4e2d": 4, "\U0001f600": 5}),
    ("keys that are prefixes", {"a": 1, "ab": 2, "": 3, "aa": 4}),
    # String escaping: quotes, backslashes, the characters with short escapes,
    # the ones without, DEL, and characters outside the basic plane.
    ("escapes", {"s": 'a"b\\c\nd\te\rf\bg\fh'}),
    ("control characters", {"s": "\x00\x01\x1f\x7f"}),
    ("astral", {"s": "\U0001f600\U0001d11e"}),
    ("combining", {"s": "e\u0301clair"}),
    ("empty string", {"s": ""}),
    ("line separators", {"s": "a/b\u2028c\u2029d"}),
]

# Content normalisation: the boundary between what a person typed and what is
# hashed. Line endings, trailing whitespace, and the edges of the Unicode
# whitespace set, where Python's str.strip() and JavaScript's \s disagree --
# U+FEFF is whitespace to one and not the other, and so are U+001C..U+001F.
CONTENT_CASES: list[tuple[str, str]] = [
    ("plain", "A position.\n"),
    ("no trailing newline", "A position."),
    ("crlf", "One.\r\nTwo.\r\n"),
    ("cr only", "One.\rTwo.\r"),
    ("trailing spaces", "One.   \nTwo.\t\n"),
    ("leading and trailing blank lines", "\n\n  A position.  \n\n\n"),
    ("interior blank lines kept", "One.\n\nTwo.\n"),
    ("combining normalised to nfc", "e\u0301clair"),
    ("already nfc", "\u00e9clair"),
    ("non breaking space at line end", "One.\u00a0\nTwo.\n"),
    ("ideographic space at line end", "One.\u3000\nTwo.\n"),
    ("zero width no break space", "One.\ufeff\nTwo.\n"),
    ("file separator", "One.\x1c\nTwo.\n"),
    ("empty", ""),
    ("whitespace only", "   \n\t\n"),
    ("astral content", "\U0001f600 a claim\n"),
]


def transition_cases() -> list[dict]:
    """Whole skeletons, including the fields that must NOT affect the id."""
    base = {
        "protocol": "grrp/0.1",
        "kind": "transition",
        "trajectory": "traj:abc",
        "parents": [],
        "prior_state": None,
        "posterior_state": "state:sha256:" + "0" * 64,
        "act": "question",
        "target": "question",
        "relation": None,
        "trigger": "self",
        "disposition": "unresolved",
        "performer": "key:ed25519:AAAA",
        "performed": "2026-01-01T00:00:00Z",
    }
    with_parents = dict(base, parents=["sha256:aaa", "sha256:bbb"], act="claim")
    with_payload = dict(
        base,
        act="challenge",
        payload={"note": "an objection", "中": ["x", 1, None], "nested": {"b": 1, "a": 2}},
    )
    # The same covered payload, carrying excluded fields. Every one of these
    # must produce the identifier of `base`: registration is added after the
    # fact by a second party, and disclosure may widen at any time (C7).
    excluded = dict(
        base,
        id="sha256:whatever",
        registration={"registrar": "key:ed25519:BBBB", "time": "2026-01-02T00:00:00Z"},
        disclosure={"class": "open"},
    )
    # A field absent and a field explicitly null must be the same record: one
    # implementation omitting a key the other writes as null would otherwise
    # split the identifier.
    missing = {k: v for k, v in base.items() if v is not None}
    return [
        {"name": "minimal question", "record": base},
        {"name": "with parents", "record": with_parents},
        {"name": "with payload", "record": with_payload},
        {"name": "excluded fields ignored", "record": excluded, "same_as": "minimal question"},
        {"name": "absent equals null", "record": missing, "same_as": "minimal question"},
    ]


def main() -> None:
    vectors = {
        "note": (
            "Generated by grrp/tools/make_vectors.py from the Python reference "
            "implementation. The TypeScript implementation must reproduce every "
            "value here. Disagreement is a specification bug."
        ),
        "canonicalisation": canonical.CANONICALISATION,
        "hash": canonical.HASH,
        "covered_fields": list(canonical.COVERED_FIELDS),
        "excluded_fields": list(canonical.EXCLUDED_FIELDS),
        "canonical": [
            {
                "name": name,
                "value": value,
                "text": canonical.canonical_bytes(value).decode("utf-8"),
                "sha256": canonical.sha256_hex(canonical.canonical_bytes(value)),
            }
            for name, value in CANONICAL_CASES
        ],
        "content": [
            {
                "name": name,
                "input": raw,
                "normalised": canonical.normalise_content(raw),
                "state_id": canonical.state_id(canonical.normalise_content(raw)),
            }
            for name, raw in CONTENT_CASES
        ],
        "transitions": [
            dict(case, id=canonical.transition_id(case["record"])) for case in transition_cases()
        ],
        "signing": [
            {
                "id": "sha256:" + "a" * 64,
                "registrar": "key:ed25519:BBBB",
                "time": "2026-01-02T03:04:05Z",
                "text": canonical.signing_input(
                    "sha256:" + "a" * 64, "key:ed25519:BBBB", "2026-01-02T03:04:05Z"
                ).decode("utf-8"),
            }
        ],
        "keys": {"prefix": keys.PREFIX},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Bytes, not text mode: the same reason state files are written as bytes.
    OUT.write_bytes(
        (json.dumps(vectors, indent=2, ensure_ascii=False, sort_keys=False) + "\n").encode("utf-8")
    )
    counted = len(vectors["canonical"]) + len(vectors["content"]) + len(vectors["transitions"])
    print(f"{counted} vectors written to {OUT}")


if __name__ == "__main__":
    main()
