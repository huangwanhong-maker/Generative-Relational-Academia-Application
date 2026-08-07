"""The record on disk.

    .grrp/
      profile.yaml          protocol version, tier, hash and canonicalisation,
                            party identifier, bound vocabularies
      charter.yaml          optional: identifier and version of a charter
      keys/<party>.pub
      events/               local event plane, gitignored, never exported
    trajectories/<traj-id>/
      trajectory.yaml
      states/<hash>.md          content: separable, redactable
      transitions/<hash>.yaml   skeleton: append-only, never rewritten
      disclosure/<hash>.yaml    sidecar (M3): class and ground, outside the id
      releases/<hash>.yaml

Two placements are worth stating, because both look like fussiness and neither
is.

*Content is separate from the skeleton.*  A state's text lives in its own file,
referenced by hash.  Deleting it leaves the skeleton, its parent links and its
identifier chain intact, which is what makes redaction possible in a log that
is otherwise append-only.

*Disclosure is a sidecar.*  Widening a class, or a scheduled release firing, is
a lawful operation.  If it edited a file under ``transitions/`` then either
every such change would look like tampering, or edit detection would have to be
relaxed until it detected nothing.  Keeping disclosure out of ``transitions/``
lets both rules stay strict.
"""

from __future__ import annotations

import io
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ruamel.yaml import YAML

from . import canonical, errors

PROTOCOL = "grrp/0.1"
GRRP_DIR = ".grrp"
TRAJECTORIES_DIR = "trajectories"

_yaml = YAML()
_yaml.default_flow_style = False
_yaml.width = 100


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = _yaml.load(handle)
    return dict(data) if data else {}


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    _yaml.dump(data, buffer)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def topological(records: list[dict]) -> list[dict]:
    """Order records so that a parent always precedes its children.

    Ties among transitions with no path between them are broken by recorded
    time, then identifier, so that repeated listings agree.  A cycle would make
    every derived view ill-defined; ``grrp check`` reports one, and this
    function degrades to time order rather than looping.
    """
    by_id = {r.get("id"): r for r in records}
    remaining = {r["id"]: set(p for p in (r.get("parents") or []) if p in by_id) for r in records}
    ready = sorted(
        (i for i, parents in remaining.items() if not parents),
        key=lambda i: (by_id[i].get("performed", ""), i),
    )
    ordered: list[dict] = []
    while ready:
        current = ready.pop(0)
        ordered.append(by_id[current])
        remaining.pop(current, None)
        freed = []
        for identifier, parents in remaining.items():
            parents.discard(current)
            if not parents:
                freed.append(identifier)
        for identifier in freed:
            ready.append(identifier)
            remaining.pop(identifier)
        ready.sort(key=lambda i: (by_id[i].get("performed", ""), i))
    if remaining:  # a cycle: report it in order of time and let check fail
        ordered.extend(
            sorted(
                (by_id[i] for i in remaining),
                key=lambda r: (r.get("performed", ""), r.get("id", "")),
            )
        )
    return ordered


def slugify(text: str, limit: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:limit].strip("-") or "trajectory"


@dataclass(frozen=True)
class Repo:
    root: Path

    # -- discovery ------------------------------------------------------------

    @classmethod
    def discover(cls, start: Path | None = None) -> "Repo":
        current = (start or Path.cwd()).resolve()
        for candidate in [current, *current.parents]:
            if (candidate / GRRP_DIR).is_dir():
                return cls(candidate)
        raise errors.NotARepository(
            "no .grrp directory here or in any parent. Run 'grrp init' first."
        )

    # -- layout ---------------------------------------------------------------

    @property
    def grrp_dir(self) -> Path:
        return self.root / GRRP_DIR

    @property
    def profile_path(self) -> Path:
        return self.grrp_dir / "profile.yaml"

    @property
    def keys_dir(self) -> Path:
        return self.grrp_dir / "keys"

    @property
    def events_dir(self) -> Path:
        return self.grrp_dir / "events"

    @property
    def trajectories_dir(self) -> Path:
        return self.root / TRAJECTORIES_DIR

    def trajectory_dir(self, traj_id: str) -> Path:
        return self.trajectories_dir / traj_id.removeprefix("traj:")

    # -- profile --------------------------------------------------------------

    def profile(self) -> dict:
        return read_yaml(self.profile_path)

    def key_name(self) -> str:
        """Which local key is acting.

        One key is the ordinary case.  ``GRRP_KEY`` exists for a machine two
        parties share, and for the tests, which need a second party in order to
        exercise registration at all.
        """
        return os.environ.get("GRRP_KEY", "self")

    def party(self) -> str:
        name = self.key_name()
        if name != "self":
            path = self.keys_dir / f"{name}.pub"
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
            raise errors.UnknownReference(f"no key named {name!r} in {self.keys_dir}")
        return self.profile()["party"]

    def set_tier(self, tier: str) -> None:
        profile = self.profile()
        profile["tier"] = tier
        write_yaml(self.profile_path, profile)

    def tier(self) -> str:
        return self.profile().get("tier", "personal")

    # -- trajectories ---------------------------------------------------------

    def trajectory_ids(self) -> list[str]:
        if not self.trajectories_dir.is_dir():
            return []
        return sorted(
            p.name for p in self.trajectories_dir.iterdir()
            if (p / "trajectory.yaml").is_file()
        )

    def trajectory(self, traj_id: str) -> dict:
        path = self.trajectory_dir(traj_id) / "trajectory.yaml"
        if not path.is_file():
            raise errors.UnknownReference(f"no trajectory {traj_id!r}")
        return read_yaml(path)

    def resolve_trajectory(self, ref: str | None) -> str:
        """Resolve a trajectory reference, or the only one if there is one."""
        ids = self.trajectory_ids()
        if ref is None:
            if not ids:
                raise errors.UnknownReference(
                    "no trajectories yet. Open one with: grrp new \"<question>\""
                )
            if len(ids) > 1:
                raise errors.AmbiguousReference(
                    "several trajectories; name one: " + ", ".join(ids)
                )
            return ids[0]
        needle = ref.removeprefix("traj:")
        exact = [i for i in ids if i == needle]
        if exact:
            return exact[0]
        partial = [i for i in ids if i.startswith(needle)]
        if len(partial) == 1:
            return partial[0]
        if not partial:
            raise errors.UnknownReference(f"no trajectory matching {ref!r}")
        raise errors.AmbiguousReference(
            f"{ref!r} matches several trajectories: " + ", ".join(partial)
        )

    # -- states ---------------------------------------------------------------

    def states_dir(self, traj_id: str) -> Path:
        return self.trajectory_dir(traj_id) / "states"

    def state_path(self, traj_id: str, sid: str) -> Path:
        return self.states_dir(traj_id) / f"{sid.split(':')[-1]}.md"

    def write_state(self, traj_id: str, text: str) -> tuple[str, Path]:
        content = canonical.normalise_content(text)
        sid = canonical.state_id(content)
        path = self.state_path(traj_id, sid)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
        return sid, path

    def read_state(self, traj_id: str, sid: str) -> str | None:
        """Content of a state, or None where it has been redacted or is sealed."""
        path = self.state_path(traj_id, sid)
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def resolve_state(self, traj_id: str | None, ref: str) -> tuple[str, str]:
        """Resolve a state reference to (trajectory id, state id).

        Accepts a full identifier, a bare hash, or an unambiguous prefix.
        """
        needle = ref.split(":")[-1]
        traj_ids = [traj_id] if traj_id else self.trajectory_ids()
        matches: list[tuple[str, str]] = []
        for tid in traj_ids:
            directory = self.states_dir(tid)
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                if path.stem.startswith(needle):
                    matches.append((tid, f"state:sha256:{path.stem}"))
        # A state may be referenced after its content was redacted; fall back to
        # the identifiers named by transitions.
        if not matches:
            for tid in traj_ids:
                for record in self.transitions(tid):
                    for key in ("prior_state", "posterior_state"):
                        value = record.get(key)
                        if value and value.split(":")[-1].startswith(needle):
                            matches.append((tid, value))
        unique = sorted(set(matches))
        if not unique:
            raise errors.UnknownReference(f"no state matching {ref!r}")
        if len(unique) > 1:
            raise errors.AmbiguousReference(
                f"{ref!r} matches several states: "
                + ", ".join(canonical.short(s) for _, s in unique)
            )
        return unique[0]

    # -- transitions ----------------------------------------------------------

    def transitions_dir(self, traj_id: str) -> Path:
        return self.trajectory_dir(traj_id) / "transitions"

    def transition_path(self, traj_id: str, tx_id: str) -> Path:
        return self.transitions_dir(traj_id) / f"{tx_id.split(':')[-1]}.yaml"

    def transitions(self, traj_id: str) -> list[dict]:
        """Every transition of a trajectory, parents before children.

        Ordering follows from the graph and not from timestamps.  Two
        transitions with no path between them are unordered whatever their
        recorded times, and recorded times are evidence about when parties
        acted rather than the structure of the history.  Time is used only to
        break ties, so that the listing is stable.
        """
        directory = self.transitions_dir(traj_id)
        if not directory.is_dir():
            return []
        records = [read_yaml(p) for p in sorted(directory.glob("*.yaml"))]
        return topological(records)

    def all_transitions(self) -> Iterator[tuple[str, dict]]:
        for traj_id in self.trajectory_ids():
            for record in self.transitions(traj_id):
                yield traj_id, record

    def resolve_transition(self, traj_id: str | None, ref: str) -> tuple[str, dict]:
        needle = ref.split(":")[-1]
        traj_ids = [traj_id] if traj_id else self.trajectory_ids()
        matches = [
            (tid, record)
            for tid in traj_ids
            for record in self.transitions(tid)
            if record.get("id", "").split(":")[-1].startswith(needle)
        ]
        if not matches:
            raise errors.UnknownReference(f"no transition matching {ref!r}")
        if len(matches) > 1:
            raise errors.AmbiguousReference(
                f"{ref!r} matches several transitions: "
                + ", ".join(canonical.short(r["id"]) for _, r in matches)
            )
        return matches[0]

    def append_transition(self, traj_id: str, record: dict) -> Path:
        """Write a transition.  Never rewrites one.

        A correction is a further transition referencing the one corrected, so
        there is deliberately no update path here.
        """
        path = self.transition_path(traj_id, record["id"])
        if path.exists():
            raise errors.ConstraintViolation(
                "C3",
                f"transition {canonical.short(record['id'])} already recorded. "
                "Nothing is edited or deleted; record a further transition instead.",
            )
        write_yaml(path, record)
        return path

    # -- proposals ------------------------------------------------------------
    #
    # At the group tier a party cannot register their own act, so an act they
    # perform is a proposal until someone else takes responsibility for it.
    # Proposals are kept outside transitions/ so that nothing under that
    # directory is ever written twice: registering does not edit a proposal, it
    # writes a transition and drops the proposal.

    def proposals_dir(self, traj_id: str) -> Path:
        return self.trajectory_dir(traj_id) / "proposals"

    def proposal_path(self, traj_id: str, tx_id: str) -> Path:
        return self.proposals_dir(traj_id) / f"{tx_id.split(':')[-1]}.yaml"

    def proposals(self, traj_id: str) -> list[dict]:
        directory = self.proposals_dir(traj_id)
        if not directory.is_dir():
            return []
        return sorted(
            (read_yaml(p) for p in directory.glob("*.yaml")),
            key=lambda r: r.get("performed", ""),
        )

    def write_proposal(self, traj_id: str, record: dict) -> Path:
        path = self.proposal_path(traj_id, record["id"])
        write_yaml(path, record)
        return path

    def resolve_proposal(self, traj_id: str | None, ref: str) -> tuple[str, dict]:
        needle = ref.split(":")[-1]
        traj_ids = [traj_id] if traj_id else self.trajectory_ids()
        matches = [
            (tid, record)
            for tid in traj_ids
            for record in self.proposals(tid)
            if record.get("id", "").split(":")[-1].startswith(needle)
        ]
        if not matches:
            raise errors.UnknownReference(f"no proposal matching {ref!r}")
        if len(matches) > 1:
            raise errors.AmbiguousReference(f"{ref!r} matches several proposals")
        return matches[0]

    # -- releases -------------------------------------------------------------

    def releases_dir(self, traj_id: str) -> Path:
        return self.trajectory_dir(traj_id) / "releases"

    def releases(self, traj_id: str) -> list[dict]:
        directory = self.releases_dir(traj_id)
        if not directory.is_dir():
            return []
        return sorted(
            (read_yaml(p) for p in directory.glob("*.yaml")),
            key=lambda r: r.get("time", ""),
        )

    def resolve_release(self, ref: str) -> tuple[str, dict]:
        needle = ref.split(":")[-1]
        matches = [
            (tid, release)
            for tid in self.trajectory_ids()
            for release in self.releases(tid)
            if release.get("id", "").split(":")[-1].startswith(needle)
        ]
        if not matches:
            raise errors.UnknownReference(f"no release matching {ref!r}")
        if len(matches) > 1:
            raise errors.AmbiguousReference(f"{ref!r} matches several releases")
        return matches[0]

    # -- disclosure sidecar ---------------------------------------------------

    def disclosure_dir(self, traj_id: str) -> Path:
        return self.trajectory_dir(traj_id) / "disclosure"

    def disclosure(self, traj_id: str, tx_id: str) -> dict | None:
        path = self.disclosure_dir(traj_id) / f"{tx_id.split(':')[-1]}.yaml"
        return read_yaml(path) if path.is_file() else None


def external_reference(ref: str, note: str | None = None) -> dict:
    """An artefact reference, with its identifier scheme and the date it was made.

    The date matters more than it looks.  A reference to a resource that has
    since changed or vanished is uninterpretable without knowing when it was
    made, and a record whose value is expected to appear years later will
    contain many such references.
    """
    lowered = ref.lower()
    if lowered.startswith("doi:") or lowered.startswith("10."):
        scheme = "doi"
    elif lowered.startswith("arxiv:"):
        scheme = "arxiv"
    elif lowered.startswith("isbn:"):
        scheme = "isbn"
    elif lowered.startswith(("http://", "https://")):
        scheme = "url"
    elif lowered.startswith("state:"):
        scheme = "state"
    else:
        scheme = "other"
    entry = {"ref": ref, "scheme": scheme, "referenced_on": now()[:10]}
    if note:
        entry["note"] = note
    return entry


def new_operation(
    *,
    trajectory: str,
    operation: str,
    performer: str,
    ground: str | None = None,
    prior_state: str | None = None,
    parents: list[str] | None = None,
    performed: str | None = None,
) -> dict:
    """An administrative operation: a record about the arrangement, not the work.

    Recorded in the same envelope as a transition, with a mandatory ``kind`` so
    the two are never presented as records of the same sort.  Two reasons:
    administrative activity would otherwise inflate the apparent generativity of
    a trajectory, and the acts constituting a position have to be recorded and
    attributable, or a position holder could act without leaving anything a
    participant could inspect.
    """
    stamp = performed or now()
    record: dict[str, Any] = {
        "id": None,
        "protocol": PROTOCOL,
        "kind": "operation",
        "trajectory": f"traj:{trajectory}",
        "parents": parents or [],
        "prior_state": prior_state,
        "posterior_state": None,
        "operation": operation,
        "ground": ground,
        "performer": performer,
        "performed": stamp,
        "registration": {
            "registrar": performer,
            "time": stamp,
            "attested": False,
            "signature": None,
        },
    }
    record["id"] = canonical.transition_id(record)
    return record


def new_transition(
    *,
    trajectory: str,
    act: str,
    performer: str,
    parents: list[str] | None = None,
    prior_state: str | None = None,
    posterior_state: str | None = None,
    target: str | None = None,
    relation: str | None = None,
    trigger: str = "self",
    disposition: str = "accepted",
    contributions: list[dict] | None = None,
    absorption: list[dict] | None = None,
    artefacts: list[dict] | None = None,
    registrar: str | None = None,
    performed: str | None = None,
) -> dict:
    """Build a transition record and compute its identifier.

    ``registration`` is attached but excluded from the identifier, so that a
    proposal can later be registered by a distinct party without the identifier
    changing under it.
    """
    stamp = performed or now()
    registrar = registrar or performer
    record: dict[str, Any] = {
        "id": None,
        "protocol": PROTOCOL,
        "kind": "transition",
        "trajectory": f"traj:{trajectory}",
        "parents": parents or [],
        "prior_state": prior_state,
        "posterior_state": posterior_state,
        "act": act,
        "target": target,
        "relation": relation,
        "trigger": trigger,
        "disposition": disposition,
        "performer": performer,
        "performed": stamp,
        "contributions": contributions or [],
        "absorption": absorption or [],
        "artefacts": artefacts or [],
        "registration": {
            "registrar": registrar,
            "time": stamp,
            # Registration by a party distinct from the performer is what gives
            # a record evidential weight.  At the personal tier there is only
            # one party, so this is False and is displayed as such everywhere.
            "attested": registrar != performer,
            "signature": None,  # M3
        },
    }
    record["id"] = canonical.transition_id(record)
    return record
