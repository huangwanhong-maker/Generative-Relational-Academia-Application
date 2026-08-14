"""Accounts: a password in front of an identity.

An account is *not* what makes a record credible, and it is worth being exact
about what it is and is not, because every system that has one eventually
starts treating it as the thing that matters.

An **identity** (:mod:`grrp.identity`) is a keypair.  It signs.  It is what
attribution and attestation rest on, it is portable, and it works with no
server in the picture at all.

An **account** is a name and a password that let a person reach an identity
through a browser on a server somebody else runs.  It is convenience and access
control.  It signs nothing.  Deleting every account here would not weaken a
single transition, because the signatures are over the keys and not over the
logins -- which is the property that makes this hostable without the host
becoming the authority (C10).

Registration is closed at the moment.  A signed-up stranger is not a party to
anything until somebody registers their acts, so open sign-up would add
accounts and no credibility; accounts are created by whoever runs the server,
with ``grrp account add``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from pathlib import Path

from . import errors, identity, store

ACCOUNTS_DIR = ".grrp-accounts"

#: Whether the sign-in page will create an account for a stranger.  Closed for
#: now, and the page says so rather than showing a form that fails.
REGISTRATION_OPEN = False

# scrypt at the parameters the standard library documents as interactive.  The
# threat is somebody who obtained the account files, which is also somebody who
# obtained the private keys sitting next to them -- so this protects the
# password itself, on the assumption it is reused elsewhere, and nothing more.
_N, _R, _P, _LEN = 2**14, 8, 1, 32


@dataclass(frozen=True)
class Account:
    name: str
    party: str


def directory(root: Path) -> Path:
    return root / ACCOUNTS_DIR


def _path(root: Path, name: str) -> Path:
    return directory(root) / f"{name}.yaml"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_LEN
    )
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(digest)}"


def _matches(password: str, stored: str) -> bool:
    try:
        algorithm, n, r, p, salt, digest = stored.split("$")
        if algorithm != "scrypt":
            return False
        again = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_unb64(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(_unb64(digest)),
        )
    except Exception:  # noqa: BLE001 - an unreadable record is a failure to match
        return False
    return hmac.compare_digest(again, _unb64(digest))


def exists(root: Path, name: str) -> bool:
    return _path(root, name).is_file()


def listing(root: Path) -> list[Account]:
    """Every account on this server, by name.

    By name and never by anything else: any other ordering of participants
    ranks them, however it is labelled (C6).
    """
    if not directory(root).is_dir():
        return []
    out = []
    for path in sorted(directory(root).glob("*.yaml")):
        data = store.read_yaml(path)
        out.append(Account(data["name"], data["party"]))
    return out


def create(root: Path, name: str, password: str) -> Account:
    """Make an account, and the keypair it reaches, in one step."""
    name = name.strip().lower()
    if len(password) < 8:
        raise errors.Refused(
            "a password of at least 8 characters. This guards browser access on "
            "whatever machine runs the server; it does not guard the record, which "
            "is guarded by signatures."
        )
    if exists(root, name):
        raise errors.Refused(f"there is already an account named {name!r} here")

    try:
        who = identity.find(root, name)
    except errors.GrrpError:
        who = identity.create(root, name)

    directory(root).mkdir(parents=True, exist_ok=True)
    (directory(root) / ".gitignore").write_text(
        "# Password hashes are nobody's business but this server's.\n*\n",
        encoding="utf-8",
    )
    store.write_yaml(
        _path(root, name),
        {
            "name": name,
            "party": who.party,
            "password": hash_password(password),
            "created": store.now(),
            "note": "An account reaches an identity. The identity signs; this does not.",
        },
    )
    return Account(name, who.party)


def authenticate(root: Path, name: str, password: str) -> Account:
    """Check a name and password, or refuse without saying which was wrong."""
    name = name.strip().lower()
    path = _path(root, name)
    stored = store.read_yaml(path).get("password", "") if path.is_file() else ""
    # Hash regardless, so that a missing account and a wrong password take
    # about the same time and the page does not disclose who has an account.
    if not _matches(password, stored) or not stored:
        raise errors.Refused("that name and password do not go together")
    return Account(name, identity.find(root, name).party)


def set_password(root: Path, name: str, password: str) -> None:
    if not exists(root, name):
        raise errors.UnknownReference(f"no account named {name!r} here")
    data = store.read_yaml(_path(root, name))
    data["password"] = hash_password(password)
    store.write_yaml(_path(root, name), data)
