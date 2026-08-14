"""Who you are signing as, across every record on this machine.

There is no account, because there is no server to hold one.  A party is a
keypair (see :mod:`grrp.keys`), and signing in is choosing which key signs --
nothing is checked against a directory, because a directory of participants is
exactly what the design refuses to build.

Two consequences follow, and both are stated on the page rather than left for
someone to discover:

*It authenticates you to nobody.*  Anyone who can read this filesystem can act
as any identity on it.  The page binds to loopback and the private keys are
gitignored; that is the whole of the protection, and it is protection against
the network, not against whoever is sitting here.

*What it does buy is continuity, which is the thing attribution rests on.*  The
keyring lives beside the records rather than inside one, so the same identity
carries across all of them.  A key generated separately in each record would
make one person look like several parties, and would make attested
registration -- which turns on the registrar being a *different* party from the
performer -- unfalsifiable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import errors, keys
from .store import Repo

RING_DIR = ".grrp-identities"
NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")


@dataclass(frozen=True)
class Identity:
    name: str
    party: str

    @property
    def short(self) -> str:
        """Enough of the key to tell two identities apart by eye."""
        return self.party.removeprefix(keys.PREFIX)[:12]


def ring(root: Path) -> Path:
    return root / RING_DIR


def _guard(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".gitignore").write_text(
        "# Private keys never leave this machine, and are never committed.\n"
        "*.key\n",
        encoding="utf-8",
    )


def available(root: Path) -> list[Identity]:
    """Identities you can sign as here: a public key with its private half.

    A public key on its own is somebody else, whom you can verify and cannot
    act as.
    """
    directory = ring(root)
    if not directory.is_dir():
        return []
    return [
        Identity(path.stem, path.read_text(encoding="utf-8").strip())
        for path in sorted(directory.glob("*.pub"))
        if (directory / f"{path.stem}.key").is_file()
    ]


def find(root: Path, name: str) -> Identity:
    for identity in available(root):
        if identity.name == name:
            return identity
    raise errors.UnknownReference(f"no identity named {name!r} on this machine")


def create(root: Path, name: str) -> Identity:
    """Generate a keypair and make it available to every record here."""
    name = name.strip().lower()
    if not NAME.match(name):
        raise errors.Refused(
            f"{name!r} will not do as an identity name: lower-case letters, digits, "
            "and . - _ , up to 32 characters. The name is for typing; "
            "the identity is the key, and nothing requires either to be your legal name."
        )
    directory = ring(root)
    if (directory / f"{name}.pub").is_file():
        raise errors.Refused(
            f"{name!r} already exists here. Two identities under one name would make "
            "the record say one party acted where two did."
        )
    _guard(directory)
    return Identity(name, keys.generate(directory, name))


def adopt(root: Path, repo: Repo, name: str) -> Identity:
    """Make ``name`` able to act in ``repo``, keeping one key across records.

    Copying rather than referencing is deliberate: a record has to stay usable
    when it is moved to another machine on its own, and a record that pointed
    outside itself for its keys would not be (C10).
    """
    identity = find(root, name)
    repo.keys_dir.mkdir(parents=True, exist_ok=True)
    public = repo.keys_dir / f"{name}.pub"
    if public.is_file():
        held = public.read_text(encoding="utf-8").strip()
        if held != identity.party:
            raise errors.Refused(
                f"this record already knows a different key as {name!r}. Acting as "
                "them here would attribute your act to somebody else."
            )
    else:
        public.write_text(identity.party + "\n", encoding="utf-8")
    private = repo.keys_dir / f"{name}.key"
    if not private.is_file():
        private.write_bytes((ring(root) / f"{name}.key").read_bytes())
    return identity


def found(root: Path, repo: Repo, name: str) -> Identity:
    """Adopt, and record this identity as whose record it is.

    Only at creation.  Adopting into a record somebody else opened does not
    make it yours, and there is no operation that makes it yours later.
    """
    from . import store

    identity = adopt(root, repo, name)
    profile = repo.profile()
    profile["party"] = identity.party
    store.write_yaml(repo.profile_path, profile)
    return identity
