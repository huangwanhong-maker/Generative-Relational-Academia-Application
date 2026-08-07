"""The operations that write to a record.

Shared by the command line and the local page, so that the two cannot drift
apart.  A record made from a page and a record made from a terminal must be the
same record, byte for byte, or the claim that the page is an application over
the protocol rather than a second implementation of it stops being true.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import canonical, errors, gitutil, keys, store, vocab
from .store import Repo

#: How each act is shaped.  The command line exposes more of the dimensions as
#: options; these are the defaults both surfaces start from.
SHAPES = {
    "claim": ("claim", "hypothesis", None, "accepted"),
    "challenge": ("challenge", "assumption", "disagrees", "unresolved"),
    "transform": ("transformation", "hypothesis", "modifies", "accepted"),
    "decide": ("decision", "path", "extends", "accepted"),
    "abandon": ("decision", "path", "retracts", "accepted"),
    "connect": ("connection", "artefact", "relates", "accepted"),
    "verify": ("verification", "hypothesis", "confirms", "accepted"),
    "refute": ("verification", "hypothesis", "refutes", "unresolved"),
    "release": ("release", "artefact", None, "accepted"),
}


@dataclass
class Written:
    """What an act produced, so a caller can report it in its own words."""

    record: dict
    paths: list[Path]
    proposed: bool


def initialise(root: Path, key_name: str = "self") -> tuple[Repo, list[Path]]:
    """Set up a record in a directory.

    The event plane is gitignored from the first moment.  A complete log of who
    attended, who commented and whose files changed is a monitoring record by
    construction, and it is the failure with the largest consequence for
    participants.
    """
    if (root / store.GRRP_DIR).exists():
        raise errors.AlreadyInitialised(f"{root / store.GRRP_DIR} already exists")

    repo = Repo(root)
    repo.grrp_dir.mkdir(parents=True)
    repo.events_dir.mkdir(parents=True)
    (repo.events_dir / ".keep").write_text("", encoding="utf-8")
    party = keys.generate(repo.keys_dir, key_name)

    (repo.grrp_dir / ".gitignore").write_text(
        "# The local event plane is never exported and never published.\n"
        "events/\n"
        "# Private keys never leave this machine.\n"
        "keys/*.key\n"
        "# Sealed content is disclosed to nobody until you open it.\n"
        "sealed/\n"
        "# Bundles obtained from elsewhere are kept here, not republished.\n"
        "received/\n",
        encoding="utf-8",
    )
    store.write_yaml(
        repo.profile_path,
        {
            "protocol": store.PROTOCOL,
            "tier": "personal",
            "hash": canonical.HASH,
            "canonicalisation": canonical.CANONICALISATION,
            "signature": "none",
            "party": party,
            "vocabularies": vocab.VOCABULARIES,
            "charter": None,
            "created": store.now(),
        },
    )
    repo.trajectories_dir.mkdir(exist_ok=True)
    return repo, [repo.profile_path, repo.grrp_dir / ".gitignore"]


def open_trajectory(repo: Repo, question: str, title: str | None = None) -> tuple[str, list[Path]]:
    """Open a trajectory on a question.

    The question is a state and is not a position: it is what the work is
    about, it does not stop being so when someone takes a view, and it stays on
    the open register until something answers it.  It also anchors the first
    claim, so even the first transition references an identified prior state.
    """
    traj_id = store.slugify(title or question)
    directory = repo.trajectory_dir(traj_id)
    if directory.exists():
        traj_id = f"{traj_id}-{canonical.sha256_hex(store.now().encode())[:6]}"
        directory = repo.trajectory_dir(traj_id)
    directory.mkdir(parents=True)

    trajectory_path = directory / "trajectory.yaml"
    store.write_yaml(
        trajectory_path,
        {
            "id": f"traj:{traj_id}",
            "protocol": store.PROTOCOL,
            "title": title or question,
            "question": question,
            "created": store.now(),
            "creator": repo.party(),
            "parents": [],
            "charter": None,
        },
    )
    state_id, state_path = repo.write_state(traj_id, question)
    record = store.new_transition(
        trajectory=traj_id,
        act="question",
        performer=repo.party(),
        parents=[],
        prior_state=None,
        posterior_state=state_id,
        target="question",
        trigger="self",
        disposition="unresolved",
    )
    path = repo.append_transition(traj_id, record)
    return traj_id, [trajectory_path, state_path, path]


def create_record(
    root: Path, name: str, question: str, use_git: bool = True, key_name: str = "self"
) -> tuple[Repo, str]:
    """Make a directory a record, optionally a git repository too.

    Version control is a substrate, not a requirement: everything works in a
    directory that is not one.  What it supplies is append-only history and the
    transport by which a complete record is copied and continued elsewhere.
    """
    directory = root / store.slugify(name)
    if directory.exists() and any(directory.iterdir()):
        raise errors.GrrpError(f"{directory.name} already exists and is not empty")
    directory.mkdir(parents=True, exist_ok=True)

    if use_git and gitutil.available() and not (directory / ".git").exists():
        import subprocess

        subprocess.run(["git", "init", "-q"], cwd=directory, capture_output=True)

    repo, paths = initialise(directory, key_name)
    traj_id, more = open_trajectory(repo, question, name)
    gitutil.commit_paths(repo.root, [*paths, *more], f"grrp: open {traj_id}")
    return repo, traj_id


def parents_for(repo: Repo, traj_id: str, state_id: str | None) -> list[str]:
    """The transitions that produced the state being altered."""
    if not state_id:
        return []
    return [
        record["id"]
        for record in repo.transitions(traj_id)
        if record.get("posterior_state") == state_id
    ][-1:]


def submit(repo: Repo, traj_id: str, record: dict, extra: list[Path] | None = None) -> Written:
    """Enter an act into the log, or propose it, according to the tier.

    At the group tier a party cannot register their own act, so what they
    perform waits for someone else.  That is where a record's credibility comes
    from: not from its content, its length or its detail, but from being
    registered by parties who did not coordinate.
    """
    paths = list(extra or [])
    for state_id in (record.get("prior_state"), record.get("posterior_state")):
        if state_id:
            path = repo.state_path(traj_id, state_id)
            if path.is_file():
                paths.append(path)

    if repo.tier() == "personal":
        paths.insert(0, repo.append_transition(traj_id, record))
        return Written(record, paths, proposed=False)

    record = dict(record)
    record["registration"] = None
    paths.insert(0, repo.write_proposal(traj_id, record))
    return Written(record, paths, proposed=True)


def register_proposal(repo: Repo, traj_id: str, proposal: dict) -> dict:
    """Take responsibility for another party's act, entering it in the log."""
    registrar = repo.party()
    if registrar == proposal.get("performer"):
        raise errors.ConstraintViolation(
            "C2",
            "you cannot register your own act. Credibility follows from the "
            "distribution of registrations across parties who did not coordinate, "
            "and follows from no property of the record itself.",
        )
    when = store.now()
    record = dict(proposal)
    record["registration"] = {
        "registrar": registrar,
        "time": when,
        "attested": True,
        "signature": keys.sign(
            repo.keys_dir,
            canonical.signing_input(record["id"], registrar, when),
            repo.key_name(),
        ),
    }
    repo.append_transition(traj_id, record)
    repo.proposal_path(traj_id, record["id"]).unlink(missing_ok=True)
    return record
