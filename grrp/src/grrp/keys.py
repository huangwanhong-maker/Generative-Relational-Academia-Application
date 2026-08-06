"""Party identity.

A party is identified by a public key.  Nothing requires that a party
correspond to a natural person, that a person hold one key, or that a key be
connected to a legal name.  What is required is *continuity*: the same
identifier across acts is what makes attribution meaningful and what makes
registration by a distinct party checkable.

Signing arrives at M3.  The key is generated at ``grrp init`` so that
identifiers recorded from the first day remain valid when it does.
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

PREFIX = "key:ed25519:"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def generate(keys_dir: Path, name: str = "self") -> str:
    """Create a keypair and return the party identifier."""
    keys_dir.mkdir(parents=True, exist_ok=True)
    private = ed25519.Ed25519PrivateKey.generate()
    public = private.public_key()

    # NOTE (M3): the private key is written unencrypted.  A passphrase belongs
    # with detached signatures, not before them.
    (keys_dir / f"{name}.key").write_bytes(
        private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    identifier = party_id(public)
    (keys_dir / f"{name}.pub").write_text(identifier + "\n", encoding="utf-8")
    return identifier


def party_id(public: ed25519.Ed25519PublicKey) -> str:
    raw = public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return PREFIX + _b64(raw)


def load_private(keys_dir: Path, name: str = "self") -> ed25519.Ed25519PrivateKey:
    data = (keys_dir / f"{name}.key").read_bytes()
    key = serialization.load_pem_private_key(data, password=None)
    assert isinstance(key, ed25519.Ed25519PrivateKey)
    return key


def read_public(keys_dir: Path, name: str = "self") -> str:
    return (keys_dir / f"{name}.pub").read_text(encoding="utf-8").strip()
