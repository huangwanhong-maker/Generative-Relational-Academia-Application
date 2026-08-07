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


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def load_private(keys_dir: Path, name: str = "self") -> ed25519.Ed25519PrivateKey:
    path = keys_dir / f"{name}.key"
    if not path.is_file():
        raise FileNotFoundError(f"no private key named {name!r} in {keys_dir}")
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    assert isinstance(key, ed25519.Ed25519PrivateKey)
    return key


def read_public(keys_dir: Path, name: str = "self") -> str:
    return (keys_dir / f"{name}.pub").read_text(encoding="utf-8").strip()


def known(keys_dir: Path) -> dict[str, str]:
    """Every party this record knows a public key for, by local name.

    Names are a convenience for typing at a prompt.  The identifier is the key,
    and nothing anywhere requires that it correspond to a legal name.
    """
    if not keys_dir.is_dir():
        return {}
    return {
        path.stem: path.read_text(encoding="utf-8").strip()
        for path in sorted(keys_dir.glob("*.pub"))
    }


def add(keys_dir: Path, name: str, party: str) -> None:
    """Record another party's public key."""
    if not party.startswith(PREFIX):
        raise ValueError(f"a party identifier looks like {PREFIX}<key>, not {party!r}")
    try:
        raw = _unb64(party.removeprefix(PREFIX))
        ed25519.Ed25519PublicKey.from_public_bytes(raw)
    except Exception as error:  # noqa: BLE001 - the message is what matters here
        raise ValueError(f"{party!r} is not a usable ed25519 public key: {error}") from None
    keys_dir.mkdir(parents=True, exist_ok=True)
    (keys_dir / f"{name}.pub").write_text(party + "\n", encoding="utf-8")


def sign(keys_dir: Path, data: bytes, name: str = "self") -> str:
    return _b64(load_private(keys_dir, name).sign(data))


def verify(party: str, data: bytes, signature: str) -> bool:
    """Whether ``signature`` over ``data`` was made by the holder of ``party``.

    A false result means the record does not say what it appears to say.  It
    does not mean the content is wrong, and it does not mean the party who
    signed understood what they were registering: an attestation asserts that
    an identified party registered a transition at a time, and nothing more.
    """
    try:
        public = ed25519.Ed25519PublicKey.from_public_bytes(
            _unb64(party.removeprefix(PREFIX))
        )
        public.verify(_unb64(signature), data)
        return True
    except Exception:  # noqa: BLE001 - any failure is a failure to verify
        return False
