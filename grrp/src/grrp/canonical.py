"""Canonical serialisation, hashing, and identifier construction.

Two independent things are hashed, and they are kept separate on purpose.

*State content* is hashed over the exact bytes written to disk, so that a state
file can be verified by anyone holding it, with no knowledge of this tool.

*Transition skeletons* are hashed over a canonical form of the **covered
payload** only.  The covered payload deliberately excludes every field that a
later lawful operation may change:

    registration   added when a transition is registered (M3: proposal then
                   registration by a distinct party would otherwise alter the id)
    disclosure     held in a sidecar file; widening a class or a scheduled
                   release firing must not invalidate anything

Getting that exclusion wrong is the single most likely serious bug in this
project: ordinary operation would start invalidating signatures, and an
implementation would then either forbid the operation or ignore the failure.
Both defeat the purpose.

The canonical form is JSON with sorted keys and no insignificant whitespace.
YAML is the human-readable record on disk; JSON is used only as the hashing
input, so reformatting a YAML file never changes an identifier.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any

CANONICALISATION = "json-sorted/1"
HASH = "sha256"

#: Fields of a transition covered by its identifier.  Everything not listed
#: here is excluded by construction.  Adding a field to this list changes every
#: identifier, which is why the protocol version pins it.
COVERED_FIELDS = (
    "protocol",
    "kind",
    "trajectory",
    "parents",
    "prior_state",
    "posterior_state",
    "act",
    "target",
    "relation",
    "trigger",
    "disposition",
    "operation",
    "ground",
    "performer",
    "performed",
    "contributions",
    "absorption",
    "artefacts",
)

#: Fields explicitly excluded from the identifier and from any signature.
EXCLUDED_FIELDS = ("id", "registration", "disclosure")


def canonical_bytes(obj: Any) -> bytes:
    """Deterministic byte encoding of a JSON-compatible object."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalise_content(text: str) -> str:
    """Normalise state content before it is hashed and written.

    Applied once, at creation.  The bytes written to disk are the bytes hashed,
    so a holder of the file can verify the identifier without this function.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip()
    return text + "\n"


def state_id(content: str) -> str:
    """Identifier of a state, over the exact bytes of its content file."""
    return f"state:{HASH}:{sha256_hex(content.encode('utf-8'))}"


def covered_payload(record: dict) -> dict:
    """The part of a transition record that its identifier commits to."""
    return {key: record.get(key) for key in COVERED_FIELDS}


def transition_id(record: dict) -> str:
    """Identifier of a transition, over its covered payload and parent ids.

    ``parents`` is inside the covered payload, so the identifier chains: any
    alteration of an earlier transition invalidates every descendant.
    """
    return f"{HASH}:{sha256_hex(canonical_bytes(covered_payload(record)))}"


def signing_input(transition_id_value: str, registrar: str, time: str) -> bytes:
    """The bytes a registrar signs.

    Covers the transition identifier (and therefore its whole covered payload
    and its parents), the registrar, and the time of registration.  It does not
    cover disclosure, redaction marks, or the signature itself.

    Signatures are produced from M3.  The construction is fixed here so that
    identifiers recorded now remain valid when signing arrives.
    """
    return canonical_bytes(
        {"id": transition_id_value, "registrar": registrar, "time": time}
    )


def short(identifier: str, length: int = 12) -> str:
    """Abbreviate an identifier for display.  Never used for storage."""
    return identifier.split(":")[-1][:length]
