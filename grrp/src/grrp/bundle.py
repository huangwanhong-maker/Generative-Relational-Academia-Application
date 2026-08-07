"""Packing a record so it can be continued elsewhere.

Portability is not export.  A system offering a data dump leaves departing
participants with an archive; what makes the difference is that the record can
be **continued** under an implementation the original operator does not control,
with appended transitions referencing the obtained ones as parents, so the
result is one graph and not two.

This matters beyond convenience.  The bound on the authority of every position
in the arrangement -- registrar, steward, holder of disclosure authority,
custodian -- is the cost of exit for the participants subject to it.  There are
no rules here addressed to position holders, because enforcing such rules would
require an enforcing party, and that party would occupy a position in turn.

Two rules govern what happens to records that arrive:

*Never alter them.*  The prohibition extends to normalisation.  An
implementation that rewrote received records into its preferred form would
invalidate their signatures and destroy the property that makes propagation
worth having.  So bytes are copied verbatim, never parsed and re-serialised.

*Retain what cannot be verified.*  A signature that does not verify, a parent
that is absent, a vocabulary value that is unrecognised: each is marked and
kept.  Discarding what an implementation does not understand is how a record
quietly becomes a different record.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import canonical, errors, keys, store, views
from .store import Repo

MANIFEST = "manifest.yaml"


@dataclass
class Receipt:
    """What a continuation found, listed rather than counted."""

    added: list[str] = field(default_factory=list)
    already_held: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    missing_parents: list[str] = field(default_factory=list)
    content_withheld: list[str] = field(default_factory=list)
    trajectories: list[str] = field(default_factory=list)


def declaration(repo: Repo) -> dict:
    """What another implementation must read to make sense of these records.

    Two implementations exchanging records need agree on the record structure,
    the act and disposition vocabularies, the bound vocabularies and their
    versions, the construction of content-derived identifiers, and the
    signature scheme.  They need agree on nothing else -- not storage, not
    transport, not interface, not serialisation.

    The last two cannot be relaxed: two implementations computing identifiers
    differently produce records that cannot be verified across the boundary,
    and the record's credibility does not survive the crossing.
    """
    profile = repo.profile()
    charter = repo.charter()
    return {
        "protocol": profile.get("protocol"),
        "tier": profile.get("tier"),
        "hash": profile.get("hash"),
        "canonicalisation": profile.get("canonicalisation"),
        "covered_fields": list(canonical.COVERED_FIELDS),
        "excluded_fields": list(canonical.EXCLUDED_FIELDS),
        "signature": profile.get("signature"),
        "signing_input": "canonical of {id, registrar, time}",
        "vocabularies": profile.get("vocabularies"),
        "charter": {"id": charter.get("id"), "version": charter.get("version")}
        if charter
        else None,
        "custody": profile.get("custody") or [],
        "succession": profile.get("succession"),
    }


def _visible_content(repo: Repo, traj_id: str, record: dict, include_restricted: bool) -> bool:
    """Whether a transition's content travels with the bundle.

    The restrictive default is deliberate.  Disclosure may widen and never
    narrow, so an error in the direction of openness is uncorrectable, and
    defaults are where such errors occur.
    """
    if include_restricted:
        return True
    state = views.disclosure_of(repo, traj_id, record["id"])
    if not state or not state.get("grounds"):
        return True
    classes = repo.classes()
    return bool(classes) and state.get("effective_class") == classes[-1]


def write(
    repo: Repo,
    destination: Path,
    traj_ids: list[str],
    include_restricted: bool = False,
) -> dict:
    """Pack trajectories into a bundle, and return its manifest."""
    withheld: list[str] = []

    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for traj_id in traj_ids:
            directory = repo.trajectory_dir(traj_id)
            archive.write(directory / "trajectory.yaml", f"trajectories/{traj_id}/trajectory.yaml")

            for path in sorted(repo.transitions_dir(traj_id).glob("*.yaml")):
                archive.write(path, f"trajectories/{traj_id}/transitions/{path.name}")

            # A state's content is governed by the transition that produced
            # it, and by that one only. Deciding on a transition's prior state
            # as well would withhold content that an earlier, unrestricted
            # transition had already disclosed.
            for record in repo.transitions(traj_id):
                if record.get("kind") == "operation":
                    continue
                state_id = record.get("posterior_state")
                if not state_id:
                    continue
                source = repo.state_path(traj_id, state_id)
                if not source.is_file():
                    continue
                name = f"trajectories/{traj_id}/states/{source.name}"
                if _visible_content(repo, traj_id, record, include_restricted):
                    if name not in archive.namelist():
                        archive.write(source, name)
                elif state_id not in withheld:
                    withheld.append(state_id)

            for path in sorted(repo.releases_dir(traj_id).glob("*.yaml")):
                archive.write(path, f"trajectories/{traj_id}/releases/{path.name}")

        archive.write(repo.profile_path, "profile.yaml")
        if repo.charter_path.is_file():
            archive.write(repo.charter_path, "charter.yaml")
        for path in sorted(repo.keys_dir.glob("*.pub")):
            archive.write(path, f"keys/{path.name}")

        manifest = {
            "protocol": store.PROTOCOL,
            "bundled": store.now(),
            "bundled_by": repo.party(),
            "trajectories": list(traj_ids),
            "declaration": declaration(repo),
            # Named, never silently absent: a reader is entitled to know that a
            # record travelled without part of its content, and why.
            "content_withheld": withheld,
            "withholding_note": (
                "Content restricted below the widest class does not travel unless the "
                "receiving implementation can honour the class. The skeletons of those "
                "records are present, so the graph and its identifiers are complete."
            )
            if withheld
            else None,
        }
        archive.writestr(MANIFEST, _dump(manifest))
    return manifest


def _dump(data: dict) -> str:
    import io

    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.default_flow_style = False
    buffer = io.StringIO()
    yaml.dump(data, buffer)
    return buffer.getvalue()


def read_manifest(source: Path) -> dict:
    with zipfile.ZipFile(source) as archive:
        if MANIFEST not in archive.namelist():
            raise errors.GrrpError(f"{source.name} is not a grrp bundle: no manifest")
        return store._yaml.load(archive.read(MANIFEST).decode("utf-8")) or {}


def apply(repo: Repo, source: Path) -> Receipt:
    """Continue a bundle in this record.

    Records already held are left exactly as they are.  New ones are written
    byte for byte.  Nothing is normalised, merged, reconciled or renumbered.
    """
    receipt = Receipt()
    manifest = read_manifest(source)

    with zipfile.ZipFile(source) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith("trajectories/"):
                continue
            target = repo.root / name
            if target.exists():
                if "/transitions/" in name:
                    receipt.already_held.append(Path(name).stem)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
            if "/transitions/" in name:
                receipt.added.append(Path(name).stem)

        # A public key that arrives is a party we can now verify, and nothing
        # more. It confers no membership of anything.
        for name in archive.namelist():
            if name.startswith("keys/"):
                target = repo.keys_dir / Path(name).name
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))

    # After the bundle's public keys have been taken in, not before: otherwise
    # every record attested by a party this machine had not met would arrive
    # marked unverified, which is a different and much more alarming claim than
    # the truth, which is that we had not yet been given their key.
    known = set(keys.known(repo.keys_dir).values())
    receipt.trajectories = list(manifest.get("trajectories") or [])
    receipt.content_withheld = list(manifest.get("content_withheld") or [])

    for traj_id in receipt.trajectories:
        by_id = {r["id"] for r in repo.transitions(traj_id)}
        for record in repo.transitions(traj_id):
            registration = record.get("registration") or {}
            if registration.get("attested"):
                registrar = registration.get("registrar")
                data = canonical.signing_input(
                    record["id"], registrar or "", registration.get("time", "")
                )
                if registrar not in known or not keys.verify(
                    registrar, data, registration.get("signature") or ""
                ):
                    receipt.unverified.append(canonical.short(record["id"]))
            for parent in record.get("parents") or []:
                if parent not in by_id:
                    receipt.missing_parents.append(canonical.short(parent))

    # The declaration under which records were received is kept, because a
    # record's meaning depends on the version and vocabularies its writer used.
    received = repo.grrp_dir / "received"
    received.mkdir(parents=True, exist_ok=True)
    store.write_yaml(
        received / f"{source.stem}.yaml",
        {
            "source": source.name,
            "received": store.now(),
            "received_by": repo.party(),
            "manifest": manifest,
        },
    )
    return receipt
