"""The command surface.

Every command below serves a purpose the person running it has anyway.  That is
not a style rule.  Systems for recording scholarly reasoning have existed since
1970, they were adequate to the representation, and they were not adopted,
because the work of recording fell on the party who gained least from the
record.  So each command's help text names what the person running it gets, and
a command that could only say "so that a record exists" does not get written.

The marker "Purpose (for you):" is checked by the test suite.
"""

from __future__ import annotations

import functools
import sys
from pathlib import Path

import typer

from . import (
    canonical,
    check as check_module,
    editor,
    errors,
    export,
    gitutil,
    keys,
    store,
    views,
    vocab,
)
from .store import Repo

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help=(
        "Record how an understanding changed, in plain text, in an ordinary git "
        "repository. No server, no account, no network."
    ),
)

TRAJ_OPTION = typer.Option(None, "--traj", "-t", help="Trajectory, if you have more than one.")


def command(*args, **kwargs):
    """Register a command whose refusals reach the user as guidance.

    A protocol that refuses things has to say which rule it is applying and
    what to do instead, or the refusal reads as a bug.  Errors go to stderr so
    that ``grrp export ... > paper.md`` does not put them in the paper.
    """

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*positional, **keyword):
            try:
                return function(*positional, **keyword)
            except errors.GrrpError as error:
                typer.secho(str(error), err=True, fg=typer.colors.RED)
                raise typer.Exit(code=1) from None

        return app.command(*args, **kwargs)(wrapper)

    return decorator


CONTRIBUTOR_OPTION = typer.Option(
    None,
    "--contributor",
    help="Another party's part in this act: name=Role. Repeatable. CRediT roles.",
)
ABSORB_OPTION = typer.Option(
    None,
    "--from",
    help="A state whose content you took. Repeatable. Credits whoever produced it.",
)
WITH_OPTION = typer.Option(
    None,
    "--with",
    help="Another state this composes from, making it a synthesis. Repeatable.",
)


def _resolve_party(repo: Repo, ref: str) -> str:
    """A party, by local name or by key."""
    if ref.startswith(keys.PREFIX):
        return ref
    known = keys.known(repo.keys_dir)
    if ref in known:
        return known[ref]
    raise errors.GrrpError(
        f"no party named {ref!r}. Known: {', '.join(known) or 'none'}. "
        "Add one with: grrp key add <name> <key:ed25519:...>"
    )


def _contributions(repo: Repo, values: list[str] | None) -> list[dict]:
    """Parties and their CRediT roles in this act.

    Attribution attaches to an act rather than to a finished work.  A
    contributor statement says a person contributed to a paper; this says which
    change in the content of a claim a person produced.
    """
    entries: list[dict] = []
    for value in values or []:
        if "=" not in value:
            raise errors.GrrpError(
                f"say --contributor name=Role, not {value!r}. "
                f"Roles: {', '.join(vocab.CREDIT_ROLES)}"
            )
        name, role = value.split("=", 1)
        try:
            entries.append(
                {"party": _resolve_party(repo, name.strip()), "role": vocab.resolve_role(role)}
            )
        except ValueError as error:
            raise errors.GrrpError(str(error)) from None
    return entries


def _absorptions(repo: Repo, refs: list[str] | None) -> list[dict]:
    """Content taken from a state elsewhere, credited to whoever produced it.

    The link confers attribution and no power to prevent, condition or reverse
    the use.  Rights to exclude, multiplied across many small contributions,
    produce the fragmentation in which downstream work needs so many
    permissions that it does not occur.

    A party who does not wish their state absorbed has one instrument, and it
    is the disclosure class of that state: absorption operates on what has been
    disclosed to the absorbing party.
    """
    links: list[dict] = []
    for ref in refs or []:
        _, state_id = repo.resolve_state(None, ref)
        found = views.producer_of(repo, state_id)
        if not found:
            raise errors.GrrpError(
                f"no transition produced {canonical.short(state_id)}, so there is nobody to credit"
            )
        links.append({"state": state_id, "party": found[1]["performer"]})
    return links



def _echo(message: str = "") -> None:
    typer.echo(message)


def _repo() -> Repo:
    return Repo.discover()


CUT = "--- everything below this line is ignored ---"

#: What the editor asks for, per act.  The decision act gets the longest prompt
#: because it is the expensive one: articulating why a direction was set aside
#: is work whose benefit accrues to someone else later, and it is the act the
#: reuse of abandoned work depends on entirely.
PROMPTS = {
    "claim": "What position are you taking?",
    "challenge": "What is the objection? Say what it is about the state that does not hold.",
    "transform": "What does the state become?",
    "decide": (
        "Why? If you are setting a direction aside, say what stopped it -- the\n"
        "assumption that failed, the obstruction you met. A direction recorded as\n"
        "abandoned without a reason cannot be revisited by anyone, including you."
    ),
    "connect": "Why does this connection matter to the state you are connecting from?",
    "verify": "What was the outcome? Say what you checked and what came of it.",
    "withdraw": "Why are you withdrawing this registration?",
    "contest": "What is wrong with the attribution? Say what the record should say.",
    "new": "What are you actually trying to find out?",
}


def _message(message: str | None, file: Path | None, act: str) -> str:
    """The text of a state: from the command line, a file, or your editor.

    Writing a paragraph inside shell quotes is friction, and it falls hardest
    on the act that matters most.  So an omitted message opens $EDITOR rather
    than being an error.
    """
    if file is not None:
        return file.read_text(encoding="utf-8")
    if message:
        return message

    template = f"\n\n{CUT}\n{PROMPTS.get(act, 'What changed?')}\n"
    edited = editor.edit(template)
    if edited is None:
        raise errors.GrrpError(
            "nothing recorded: no editor is configured, or it exited with an error.\n"
            "Set $GRRP_EDITOR or $EDITOR, or pass -m \"<text>\" or --file <path>."
        )
    text = edited.split(CUT)[0].strip()
    if not text:
        raise errors.GrrpError("nothing recorded: the message was empty.")
    return text


def _commit(repo: Repo, paths: list[Path], summary: str) -> None:
    if gitutil.commit_paths(repo.root, paths, f"grrp: {summary}"):
        _echo("  committed to git")


def _record(
    repo: Repo, traj_id: str, record: dict, note: str, extra: list[Path] | None = None
) -> None:
    """Enter an act into the record, or propose it, according to the tier.

    At the personal tier there is one party, so an act is written directly and
    marked unattested: useful to its author, and evidence to nobody.

    At the group tier a party cannot register their own act, so what they
    perform is a proposal until another party takes responsibility for it.
    That is the whole of where a record's credibility comes from -- not from
    the content, its length or its detail, but from being registered by parties
    who did not coordinate.
    """
    written = [*(extra or [])]
    for state_id in (record.get("prior_state"), record.get("posterior_state")):
        if state_id:
            state_path = repo.state_path(traj_id, state_id)
            if state_path.is_file():
                written.append(state_path)

    if repo.tier() == "personal":
        written.insert(0, repo.append_transition(traj_id, record))
        _echo(f"{note}  {canonical.short(record['id'])}")
        if record.get("posterior_state"):
            _echo(f"  state    {canonical.short(record['posterior_state'])}")
        _echo("  unattested (you registered your own act)")
    else:
        record = dict(record)
        record["registration"] = None
        written.insert(0, repo.write_proposal(traj_id, record))
        _echo(f"{note}  {canonical.short(record['id'])}  (proposed)")
        if record.get("posterior_state"):
            _echo(f"  state    {canonical.short(record['posterior_state'])}")
        _echo("  not yet in the log. Another party registers it:")
        _echo(f"    grrp register {canonical.short(record['id'])}")

    _commit(repo, written, f"{record.get('act')} {canonical.short(record['id'])}")


# --------------------------------------------------------------------------- #
# setting up
# --------------------------------------------------------------------------- #


@command()
def init(
    name: str = typer.Option("self", help="Local name for your keypair."),
) -> None:
    """Set up a record in this directory.

    Purpose (for you): somewhere to put the reasoning you currently keep in
    your head and lose. Creates .grrp/ with a profile and a keypair, and
    nothing else. Works inside an existing git repository or on its own.
    """
    root = Path.cwd()
    if (root / store.GRRP_DIR).exists():
        raise errors.AlreadyInitialised(f"{store.GRRP_DIR} already exists here")

    repo = Repo(root)
    repo.grrp_dir.mkdir(parents=True)
    repo.events_dir.mkdir(parents=True)
    (repo.events_dir / ".keep").write_text("", encoding="utf-8")

    party = keys.generate(repo.keys_dir, name)

    # The event plane is a monitoring log by construction: who attended, whose
    # files changed, when. It stays local, is never exported, and reaches
    # disclosure only through a transition that references it.
    (repo.grrp_dir / ".gitignore").write_text(
        "# The local event plane is never exported and never published.\n"
        "events/\n"
        "# Private keys never leave this machine.\n"
        "keys/*.key\n",
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

    _echo(f"initialised in {root}")
    _echo(f"  you are {party}")
    _echo("  tier     personal - useful alone, and carrying no evidential weight")
    _echo("")
    _echo('next: grrp new "the question you are actually working on"')
    _commit(repo, [repo.profile_path, repo.grrp_dir / ".gitignore"], "init")


@command()
def profile() -> None:
    """Print what another implementation would need to read your records.

    Purpose (for you): to know which protocol version, hash and vocabularies
    your record commits to, before you rely on anyone else being able to read it.
    """
    repo = _repo()
    data = repo.profile()
    for key, value in data.items():
        _echo(f"{key:18} {value}")
    _echo("")
    _echo("Your record can be obtained and continued elsewhere without anyone's")
    _echo("permission. Portability is the only bound on the authority of whoever")
    _echo("holds it, including you.")


# --------------------------------------------------------------------------- #
# recording
# --------------------------------------------------------------------------- #


@command()
def new(
    question: str = typer.Argument(..., help="The question you are opening."),
    title: str = typer.Option(None, help="Short title. Defaults to the question."),
) -> None:
    """Open a trajectory.

    Purpose (for you): to write down what you are actually trying to find out,
    once, in a place you will look again, before the framing hardens and you
    forget you chose it.
    """
    repo = _repo()
    traj_id = store.slugify(title or question)
    directory = repo.trajectory_dir(traj_id)
    if directory.exists():
        suffix = canonical.sha256_hex(store.now().encode())[:6]
        traj_id = f"{traj_id}-{suffix}"
        directory = repo.trajectory_dir(traj_id)
    directory.mkdir(parents=True)

    party = repo.party()
    trajectory_path = directory / "trajectory.yaml"
    store.write_yaml(
        trajectory_path,
        {
            "id": f"traj:{traj_id}",
            "protocol": store.PROTOCOL,
            "title": title or question,
            "question": question,
            "created": store.now(),
            "creator": party,
            "parents": [],
            "charter": None,
        },
    )

    state_id, state_path = repo.write_state(traj_id, question)
    record = store.new_transition(
        trajectory=traj_id,
        act="question",
        performer=party,
        parents=[],
        prior_state=None,
        posterior_state=state_id,
        target="question",
        trigger="self",
        disposition="unresolved",
    )
    path = repo.append_transition(traj_id, record)
    _echo(f"opened   {traj_id}")
    _echo(f"  question {canonical.short(state_id)}")
    _echo("")
    _echo('next: grrp claim -m "<what you currently think>"   (omit -m to use your editor)')
    _commit(repo, [trajectory_path, state_path, path], f"open {traj_id}")


@command()
def claim(
    ref: str = typer.Argument(None, help="Trajectory, or the state you are answering."),
    message: str = typer.Option(None, "-m", "--message", help="The position you are taking."),
    file: Path = typer.Option(None, "--file", help="Read the position from a file."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    target: str = typer.Option("hypothesis", help=f"One of: {', '.join(vocab.TARGETS)}."),
    trigger: str = typer.Option("self", help=f"One of: {', '.join(vocab.TRIGGERS)}."),
) -> None:
    """State a position.

    Purpose (for you): to fix what you currently think, so that when it changes
    you can see what changed it. A position you never wrote down cannot be
    shown to have been abandoned for a reason.
    """
    repo = _repo()
    traj_id, prior = _resolve_prior(repo, ref)
    text = _message(message, file, "claim")
    state_id, _ = repo.write_state(traj_id, text)
    record = store.new_transition(
        trajectory=traj_id,
        act="claim",
        performer=repo.party(),
        contributions=_contributions(repo, contributor),
        absorption=_absorptions(repo, absorb),
        parents=_parents_for(repo, traj_id, prior),
        prior_state=prior,
        posterior_state=state_id,
        target=target,
        trigger=trigger,
        disposition="accepted",
    )
    _record(repo, traj_id, record, "claim   ")


@command()
def challenge(
    state: str = typer.Argument(None, help="The state you are objecting to. Defaults to the live position."),
    message: str = typer.Option(None, "-m", "--message", help="The objection."),
    file: Path = typer.Option(None, "--file", help="Read the objection from a file."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    traj: str = TRAJ_OPTION,
    target: str = typer.Option("assumption", help=f"One of: {', '.join(vocab.TARGETS)}."),
    trigger: str = typer.Option("objection", help=f"One of: {', '.join(vocab.TRIGGERS)}."),
    disposition: str = typer.Option(
        "unresolved", help="accepted, contested, or unresolved."
    ),
) -> None:
    """Object to an identified state.

    Purpose (for you): to stop losing the objection. Yours, or one somebody
    made to you in a seminar and you half-remember three months later when it
    turns out to have been right.

    A challenge does not alter the state it challenges. If you accept it, the
    change is a separate transformation, and the two are linked.
    """
    repo = _repo()
    text = _message(message, file, "challenge")
    if disposition not in vocab.DISPOSITIONS:
        raise errors.GrrpError(
            f"disposition must be one of {', '.join(vocab.DISPOSITIONS)}"
        )
    traj_id, prior = _resolve_prior(repo, state, traj)
    state_id, _ = repo.write_state(traj_id, text)
    relation, _bound = vocab.resolve_relation("disagrees")
    record = store.new_transition(
        trajectory=traj_id,
        act="challenge",
        performer=repo.party(),
        contributions=_contributions(repo, contributor),
        absorption=_absorptions(repo, absorb),
        parents=_parents_for(repo, traj_id, prior),
        prior_state=prior,
        posterior_state=state_id,
        target=target,
        relation=relation,
        trigger=trigger,
        disposition=disposition,
    )
    _record(repo, traj_id, record, "challenge")
    if disposition == "unresolved":
        _echo("  standing - it will appear in 'grrp open' until something answers it")


@command()
def transform(
    state: str = typer.Argument(None, help="The state you are changing. Defaults to the live position."),
    message: str = typer.Option(None, "-m", "--message", help="What it becomes."),
    file: Path = typer.Option(None, "--file", help="Read the new state from a file."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    with_: list[str] = WITH_OPTION,
    relation: str = typer.Option(
        "modifies", help=f"One of: {', '.join(sorted(vocab.RELATIONS))}."
    ),
    answering: list[str] = typer.Option(
        None, "--answering", help="Challenge this responds to. Repeatable."
    ),
    traj: str = TRAJ_OPTION,
    target: str = typer.Option("hypothesis", help=f"One of: {', '.join(vocab.TARGETS)}."),
    trigger: str = typer.Option("self", help=f"One of: {', '.join(vocab.TRIGGERS)}."),
) -> None:
    """Change a state into its successor.

    Purpose (for you): so that in a year you can see not only what you think
    but which objection, result or reading moved you there. That is the part
    you will not reconstruct from the paper.

    Use --answering to name the challenge this responds to. The challenge then
    stops standing, without anything being edited: the graph records it.
    """
    repo = _repo()
    text = _message(message, file, "transform")
    relation_value, bound = vocab.resolve_relation(relation)
    if not bound:
        _echo(f"  note: {relation_value} is a local value and needs a charter to define it")
    traj_id, prior = _resolve_prior(repo, state, traj)
    state_id, _ = repo.write_state(traj_id, text)

    parents = _parents_for(repo, traj_id, prior)
    for reference in answering or []:
        _, answered_record = repo.resolve_transition(traj_id, reference)
        if answered_record["id"] not in parents:
            parents.append(answered_record["id"])

    # A transformation drawing on several branches is a synthesis: a state its
    # performer composed from what those branches reached. It does not close
    # them. Nothing is combined by rule, because two revisions of a concept do
    # not compose and no test decides the result.
    for reference in with_ or []:
        _, other_state = repo.resolve_state(traj_id, reference)
        for candidate in repo.transitions(traj_id):
            if candidate.get("posterior_state") == other_state and candidate["id"] not in parents:
                parents.append(candidate["id"])

    record = store.new_transition(
        trajectory=traj_id,
        act="transformation",
        performer=repo.party(),
        contributions=_contributions(repo, contributor),
        absorption=_absorptions(repo, absorb),
        parents=parents,
        prior_state=prior,
        posterior_state=state_id,
        target=target,
        relation=relation_value,
        trigger=trigger if not answering else "objection",
        disposition="accepted",
    )
    _record(repo, traj_id, record, "transform")
    if with_:
        _echo(f"  synthesis of {len(parents)} parents. The branches it draws on continue.")


@command()
def decide(
    state: str = typer.Argument(None, help="The state you are deciding about. Defaults to the live position."),
    message: str = typer.Option(None, "-m", "--message", help="The reason."),
    file: Path = typer.Option(None, "--file", help="Read the reason from a file."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    abandon: bool = typer.Option(
        False, "--abandon", help="Retire this direction rather than continue it."
    ),
    answering: list[str] = typer.Option(
        None, "--answering", help="Challenge this responds to. Repeatable."
    ),
    traj: str = TRAJ_OPTION,
) -> None:
    """Record a decision, with its reason.

    Purpose (for you): so that you do not spend a second six months on the
    approach you already ruled out, and so that when someone asks why the
    project went this way you have the answer rather than a recollection.

    This is the expensive act, and the one everything else depends on. An
    approach recorded as abandoned without a reason cannot be revisited by
    anyone, including you.
    """
    repo = _repo()
    text = _message(message, file, "decide")
    traj_id, prior = _resolve_prior(repo, state, traj)
    state_id, _ = repo.write_state(traj_id, text)

    parents = _parents_for(repo, traj_id, prior)
    for reference in answering or []:
        _, answered_record = repo.resolve_transition(traj_id, reference)
        if answered_record["id"] not in parents:
            parents.append(answered_record["id"])

    relation_value = vocab.RELATIONS["retracts"] if abandon else vocab.RELATIONS["extends"]
    record = store.new_transition(
        trajectory=traj_id,
        act="decision",
        performer=repo.party(),
        contributions=_contributions(repo, contributor),
        absorption=_absorptions(repo, absorb),
        parents=parents,
        prior_state=prior,
        posterior_state=state_id,
        target="path",
        relation=relation_value,
        trigger="self",
        disposition="accepted",
    )
    _record(repo, traj_id, record, "decide  ")
    if abandon:
        _echo(f"  retired  {canonical.short(prior)} - the record of why it was tried stays")


@command()
def release(
    state: str = typer.Argument(None, help="The state you are publishing. Defaults to the live position."),
    traj: str = TRAJ_OPTION,
) -> None:
    """Publish a state, enumerating the objections standing against it.

    Purpose (for you): to get something citable out of the record you already
    have, with no extra writing. 'grrp export' then emits the document.

    A release declares that a state is published and that these objections
    stand. It asserts nothing about their merit, and it is not a certification
    of anything. You cannot make a release conditional on resolving them.
    """
    repo = _repo()
    traj_id, state_id = _resolve_prior(repo, state, traj)

    standing = views.standing_objections(repo, traj_id, state_id)
    record = store.new_transition(
        trajectory=traj_id,
        act="release",
        performer=repo.party(),
        parents=_parents_for(repo, traj_id, state_id),
        prior_state=state_id,
        posterior_state=state_id,
        target="artefact",
        trigger="self",
        disposition="accepted",
    )
    release_record = {
        "id": record["id"],
        "protocol": store.PROTOCOL,
        "trajectory": f"traj:{traj_id}",
        "state": state_id,
        "time": record["performed"],
        "registrant": record["performer"],
        # Disclosure classes arrive with the group tier. At the personal tier
        # there is one party and therefore no class to declare.
        "class": None,
        "standing_objections": [
            {
                "id": objection["id"],
                "state": objection.get("posterior_state"),
                "performed": objection.get("performed"),
            }
            for objection in standing
        ],
    }
    path = repo.releases_dir(traj_id) / f"{record['id'].split(':')[-1]}.yaml"
    store.write_yaml(path, release_record)
    _record(repo, traj_id, record, "release ", extra=[path])

    if standing:
        _echo(f"  standing objections enumerated: {len(standing)}")
        for objection in standing:
            _echo(f"    {canonical.short(objection['id'])}")
    else:
        _echo("  no objections standing at release")
    _echo(f"  export it: grrp export {canonical.short(record['id'])}")


@command()
def connect(
    to: str = typer.Option(..., "--to", help="A state, or an external work: doi:… arxiv:… https://…"),
    state: str = typer.Argument(None, help="The state you are connecting from. Defaults to the live position."),
    message: str = typer.Option(None, "-m", "--message", help="Why the connection matters."),
    file: Path = typer.Option(None, "--file", help="Read the note from a file."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    relation: str = typer.Option("relates", help=f"One of: {', '.join(sorted(vocab.RELATIONS))}."),
    traj: str = TRAJ_OPTION,
    trigger: str = typer.Option("literature", help=f"One of: {', '.join(vocab.TRIGGERS)}."),
) -> None:
    """Relate a state to another state, or to work outside the trajectory.

    Purpose (for you): so that the paper you found at 2am, and the reason it
    bears on what you are doing, are attached to the thing they bear on rather
    than to a tab you will close.

    An external reference records its identifier scheme and the date you made
    it, because a reference to something that has since changed is
    uninterpretable without knowing when it was made.
    """
    repo = _repo()
    relation_value, bound = vocab.resolve_relation(relation)
    if not bound:
        _echo(f"  note: {relation_value} is a local value and needs a charter to define it")
    traj_id, prior = _resolve_prior(repo, state, traj)
    text = _message(message, file, "connect")

    parents = _parents_for(repo, traj_id, prior)
    artefacts: list[dict] = []
    try:
        # A connection to a state elsewhere is recorded in the graph: the
        # transition that produced it becomes a parent, so no new field is
        # needed and the link travels with the record.
        other_traj, other_state = repo.resolve_state(None, to)
        for record in repo.transitions(other_traj):
            if record.get("posterior_state") == other_state and record["id"] not in parents:
                parents.append(record["id"])
        artefacts.append(store.external_reference(other_state))
    except (errors.UnknownReference, errors.AmbiguousReference):
        artefacts.append(store.external_reference(to))

    state_id, _ = repo.write_state(traj_id, text)
    record = store.new_transition(
        trajectory=traj_id,
        act="connection",
        performer=repo.party(),
        contributions=_contributions(repo, contributor),
        absorption=_absorptions(repo, absorb),
        parents=parents,
        prior_state=prior,
        posterior_state=state_id,
        target="artefact",
        relation=relation_value,
        trigger=trigger,
        disposition="accepted",
        artefacts=artefacts,
    )
    _record(repo, traj_id, record, "connect ")
    _echo(f"  to       {artefacts[0]['ref']}  ({artefacts[0]['scheme']})")


@command()
def verify(
    state: str = typer.Argument(None, help="The state you checked. Defaults to the live position."),
    message: str = typer.Option(None, "-m", "--message", help="The outcome."),
    file: Path = typer.Option(None, "--file", help="Read the outcome from a file."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    failed: bool = typer.Option(False, "--failed", help="The check did not come out as predicted."),
    traj: str = TRAJ_OPTION,
    trigger: str = typer.Option("experiment", help=f"One of: {', '.join(vocab.TRIGGERS)}."),
) -> None:
    """Report the outcome of a check performed on a state.

    Purpose (for you): so that "we already ran that" is answerable, and so that
    a result which did not come out as predicted is attached to the claim it
    bears on instead of being remembered as a vague misgiving.

    A failed check is recorded as unresolved, so it stands on the open register
    until something answers it -- which is also where a stranger could take it up.
    """
    repo = _repo()
    traj_id, prior = _resolve_prior(repo, state, traj)
    text = _message(message, file, "verify")
    state_id, _ = repo.write_state(traj_id, text)
    record = store.new_transition(
        trajectory=traj_id,
        act="verification",
        performer=repo.party(),
        contributions=_contributions(repo, contributor),
        absorption=_absorptions(repo, absorb),
        parents=_parents_for(repo, traj_id, prior),
        prior_state=prior,
        posterior_state=state_id,
        target="hypothesis",
        relation=vocab.RELATIONS["refutes"] if failed else vocab.RELATIONS["confirms"],
        trigger="failure" if failed and trigger == "experiment" else trigger,
        disposition="unresolved" if failed else "accepted",
    )
    _record(repo, traj_id, record, "verify  ")
    if failed:
        _echo("  standing - it will appear in 'grrp open' until something answers it")


@command()
def redact(
    state: str = typer.Argument(..., help="The state whose content is to be removed."),
    ground: str = typer.Option(
        ..., "--ground", help=f"One of: {', '.join(vocab.REDACTION_GROUNDS)}."
    ),
    traj: str = TRAJ_OPTION,
    yes: bool = typer.Option(False, "--yes", help="Do not ask for confirmation."),
) -> None:
    """Remove the content of a state, keeping the record that it existed.

    Purpose (for you): so that a participant can withdraw what they wrote, or
    personal material can be removed, without the record of the work becoming a
    lie about its own history.

    What survives: that a transition occurred, by whom, of what type, at what
    position in the graph, and that a redaction was performed and on what
    ground. What does not: what was said.
    """
    repo = _repo()
    if ground not in vocab.REDACTION_GROUNDS:
        raise errors.GrrpError(
            f"ground must be one of: {', '.join(vocab.REDACTION_GROUNDS)}"
        )
    traj_id, state_id = repo.resolve_state(repo.resolve_trajectory(traj) if traj else None, state)
    path = repo.state_path(traj_id, state_id)
    if not path.is_file():
        raise errors.GrrpError(f"{canonical.short(state_id)} has no content to remove")

    _echo(f"about to remove the content of {canonical.short(state_id)}:")
    _echo(f"  {_headline(repo, traj_id, state_id)}")
    _echo("")
    _echo("This cannot be undone, and the fact that you did it stays in the record.")
    if not yes and not typer.confirm("remove it?"):
        raise errors.GrrpError("nothing removed")

    path.unlink()
    record = store.new_operation(
        trajectory=traj_id,
        operation="redaction",
        performer=repo.party(),
        ground=ground,
        prior_state=state_id,
        parents=_parents_for(repo, traj_id, state_id),
    )
    written = repo.append_transition(traj_id, record)
    _echo(f"redacted  {canonical.short(record['id'])}  ground {ground}")
    _echo("  the graph is unchanged and the chain still verifies: grrp check")
    _commit(repo, [written, path], f"redaction {canonical.short(record['id'])}")
    _echo("")
    _echo("  Note: earlier git commits still contain the removed text. Removing it")
    _echo("  from history is a separate operation on the substrate (git filter-repo),")
    _echo("  and any copy already obtained by another party is beyond reach of both.")


# --------------------------------------------------------------------------- #
# attestation
# --------------------------------------------------------------------------- #


@command(name="key")
def key_cmd(
    action: str = typer.Argument("list", help="list, add, or mine."),
    name: str = typer.Argument(None, help="A local name for the party."),
    party: str = typer.Argument(None, help="Their key: key:ed25519:…"),
) -> None:
    """Know another party's key, so they can register your transitions.

    Purpose (for you): a record you registered yourself is useful to you and is
    evidence to nobody. Adding one colleague's key is what makes it evidence,
    and it is the whole of the setup that takes.

    Adding a key moves this record to the group tier, where you can no longer
    register your own acts: what you perform becomes a proposal until someone
    else takes responsibility for it.
    """
    repo = _repo()
    if action == "mine":
        _echo(repo.party())
        _echo("")
        _echo("Give this to whoever will register your transitions. They run:")
        _echo(f"  grrp key add <a-name-for-you> {repo.party()}")
        return

    if action == "list":
        for local, identifier in keys.known(repo.keys_dir).items():
            mark = "  (you)" if identifier == repo.party() else ""
            _echo(f"{local:<16} {identifier}{mark}")
        _echo("")
        _echo(f"tier  {repo.tier()}")
        return

    if action != "add":
        raise errors.GrrpError("say: grrp key list | grrp key mine | grrp key add <name> <key>")
    if not name or not party:
        raise errors.GrrpError("grrp key add <name> <key:ed25519:…>")

    try:
        keys.add(repo.keys_dir, name, party)
    except ValueError as error:
        raise errors.GrrpError(str(error)) from None

    _echo(f"added    {name}  {party}")
    if party != repo.party() and repo.tier() == "personal":
        repo.set_tier("group")
        _echo("")
        _echo("  tier is now group. Credibility begins here, and so does the rule that")
        _echo("  you cannot register your own acts: what you perform is a proposal, and")
        _echo(f"  {name} registers it. Registering is one action, and is meant to be.")
    _commit(repo, [repo.keys_dir / f"{name}.pub", repo.profile_path], f"key add {name}")


@command(name="pending")
def pending_cmd(
    traj: str = typer.Argument(None, help="Trajectory. Defaults to all of them."),
) -> None:
    """List acts proposed but not yet registered.

    Purpose (for you): to see what is waiting on you, and what of yours is
    waiting on someone else. Nothing here is in the log yet.
    """
    repo = _repo()
    traj_ids = [repo.resolve_trajectory(traj)] if traj else repo.trajectory_ids()
    me = repo.party()
    anything = False
    for traj_id in traj_ids:
        proposals = repo.proposals(traj_id)
        if not proposals:
            continue
        anything = True
        _echo(f"{traj_id}")
        for record in proposals:
            mine = record.get("performer") == me
            who = "yours, waiting on another party" if mine else "waiting on you"
            _echo(
                f"  {canonical.short(record['id'])}  {record.get('act'):<14} "
                f"{record.get('performed')}  ({who})"
            )
            state_id = record.get("posterior_state")
            if state_id:
                _echo(f"      {_headline(repo, traj_id, state_id, width=84)}")
        _echo()
    if not anything:
        _echo("nothing proposed.")


@command()
def register(
    proposal: str = typer.Argument(..., help="The proposed act you are registering."),
    traj: str = TRAJ_OPTION,
) -> None:
    """Take responsibility for another party's act, entering it in the log.

    Purpose (for you): so that the record of work you were part of says so, and
    so that your colleague's record is worth something to a reader who was not
    there. It is one action, deliberately: the work falls on the party who
    gains least from it.

    What you assert is that this party performed this act at this time. Not
    that it was an improvement, not that the claim is true, and not that you
    understood it. Assessment of content lies outside the protocol.
    """
    repo = _repo()
    traj_id = repo.resolve_trajectory(traj) if traj else None
    traj_id, record = repo.resolve_proposal(traj_id, proposal)

    registrar = repo.party()
    if registrar == record.get("performer"):
        raise errors.ConstraintViolation(
            "C2",
            "you cannot register your own act. Credibility follows from the "
            "distribution of registrations across parties who did not coordinate, "
            "and follows from no property of the record itself.\n"
            f"Ask another party to run: grrp register {canonical.short(record['id'])}",
        )

    when = store.now()
    signature = keys.sign(
        repo.keys_dir,
        canonical.signing_input(record["id"], registrar, when),
        repo.key_name(),
    )
    record = dict(record)
    record["registration"] = {
        "registrar": registrar,
        "time": when,
        "attested": True,
        "signature": signature,
    }
    path = repo.append_transition(traj_id, record)
    repo.proposal_path(traj_id, record["id"]).unlink(missing_ok=True)

    _echo(f"registered {canonical.short(record['id'])}  {record.get('act')}")
    _echo(f"  performed by  {canonical.short(record['performer'], 16)}")
    _echo(f"  registered by {canonical.short(registrar, 16)}  (attested)")
    _commit(repo, [path], f"register {canonical.short(record['id'])}")


@command()
def attribute(
    proposal: str = typer.Argument(..., help="The proposed act to attribute."),
    contributor: list[str] = CONTRIBUTOR_OPTION,
    absorb: list[str] = ABSORB_OPTION,
    traj: str = TRAJ_OPTION,
) -> None:
    """Add contributors or absorbed content to an act you have proposed.

    Purpose (for you): so that the colleague whose objection reshaped this, or
    the line of work you took the method from, is named in the record rather
    than in your memory.

    This works on a proposal, before anyone has registered it. A recorded
    transition is never edited: if an attribution in the log is wrong, that is
    contested by a further act, with 'grrp contest'.
    """
    repo = _repo()
    traj_id = repo.resolve_trajectory(traj) if traj else None

    try:
        traj_id, record = repo.resolve_proposal(traj_id, proposal)
    except errors.UnknownReference:
        try:
            traj_id, recorded = repo.resolve_transition(traj_id, proposal)
        except errors.UnknownReference:
            raise errors.GrrpError(f"nothing proposed or recorded matches {proposal!r}") from None
        raise errors.ConstraintViolation(
            "C3",
            f"{canonical.short(recorded['id'])} is already in the log, and a recorded "
            "transition is never edited. If its attribution is wrong, contest it:\n"
            f"  grrp contest {canonical.short(recorded['id'])} -m \"<what is wrong>\"",
        ) from None

    additions = _contributions(repo, contributor)
    links = _absorptions(repo, absorb)
    if not additions and not links:
        raise errors.GrrpError("nothing to add: pass --contributor name=Role or --from <state>")

    updated = dict(record)
    updated["contributions"] = [*(record.get("contributions") or []), *additions]
    updated["absorption"] = [*(record.get("absorption") or []), *links]
    updated["id"] = canonical.transition_id(updated)

    repo.proposal_path(traj_id, record["id"]).unlink(missing_ok=True)
    path = repo.write_proposal(traj_id, updated)

    _echo(f"attributed {canonical.short(updated['id'])}")
    if updated["id"] != record["id"]:
        _echo(f"  the proposal's identifier changed from {canonical.short(record['id'])},")
        _echo("  because contributions and absorption are part of what it asserts.")
    for entry in additions:
        _echo(f"  contributor  {canonical.short(entry['party'], 16)}  {entry['role']}")
    for link in links:
        _echo(
            f"  absorbed     {canonical.short(link['state'])} "
            f"by {canonical.short(link['party'], 16)}"
        )
    if links:
        _echo("  attribution, and no power to prevent, condition or reverse the use.")
    _commit(repo, [path], f"attribute {canonical.short(updated['id'])}")


@command()
def contest(
    transition: str = typer.Argument(..., help="The transition whose attribution is wrong."),
    message: str = typer.Option(None, "-m", "--message", help="What is wrong with it."),
    file: Path = typer.Option(None, "--file", help="Read the ground from a file."),
    traj: str = TRAJ_OPTION,
) -> None:
    """Record that an attribution is wrong, or that content was taken without a link.

    Purpose (for you): so that a record naming the wrong party, or omitting
    yours, does not stand unanswered under your nose.

    Nothing is deleted or altered. The protocol supplies no procedure for
    settling this and no party empowered to settle it: what the record
    contributes is that both positions are visible, with their dates.
    """
    repo = _repo()
    traj_id = repo.resolve_trajectory(traj) if traj else None
    traj_id, target = repo.resolve_transition(traj_id, transition)
    text = _message(message, file, "contest")

    state_id, _ = repo.write_state(traj_id, text)
    record = store.new_transition(
        trajectory=traj_id,
        act="challenge",
        performer=repo.party(),
        parents=[target["id"]],
        prior_state=target.get("posterior_state") or target.get("prior_state"),
        posterior_state=state_id,
        target="artefact",
        relation=vocab.RELATIONS["disputes"],
        trigger="self",
        disposition="unresolved",
    )
    _record(repo, traj_id, record, "contest ")
    _echo(f"  {canonical.short(target['id'])} is unchanged, with this linked to it.")
    _echo("  Both stand in the record. Nobody here decides between them.")


@command()
def withdraw(
    transition: str = typer.Argument(..., help="The registered transition you are withdrawing."),
    message: str = typer.Option(None, "-m", "--message", help="The ground of withdrawal."),
    file: Path = typer.Option(None, "--file", help="Read the ground from a file."),
    traj: str = TRAJ_OPTION,
) -> None:
    """Withdraw an attestation you made, by recording a further act.

    Purpose (for you): so that a registration you have come to think
    misdescribes what occurred does not stand in your name.

    Nothing is deleted. A reader sees both the original registration and its
    withdrawal, which is more informative than either a deletion or a silent
    correction, and it places the disagreement in the record where a later
    reader can weigh it.
    """
    repo = _repo()
    traj_id = repo.resolve_trajectory(traj) if traj else None
    traj_id, target = repo.resolve_transition(traj_id, transition)
    registration = target.get("registration") or {}

    if registration.get("registrar") != repo.party():
        raise errors.GrrpError(
            f"{canonical.short(target['id'])} was registered by "
            f"{canonical.short(registration.get('registrar') or 'nobody', 16)}, not by you. "
            "An attestation is withdrawn by the party who made it."
        )

    text = _message(message, file, "withdraw")
    state_id, _ = repo.write_state(traj_id, text)
    record = store.new_transition(
        trajectory=traj_id,
        act="challenge",
        performer=repo.party(),
        parents=[target["id"]],
        prior_state=target.get("posterior_state") or target.get("prior_state"),
        posterior_state=state_id,
        target="artefact",
        relation=vocab.RELATIONS["retracts"],
        trigger="self",
        disposition="unresolved",
    )
    _record(repo, traj_id, record, "withdraw")
    _echo(f"  the registration of {canonical.short(target['id'])} stands in the log,")
    _echo("  with this withdrawal linked to it. Neither is removed.")


# --------------------------------------------------------------------------- #
# reading
# --------------------------------------------------------------------------- #


@command(name="show")
def show_cmd(
    traj: str = typer.Argument(None, help="Trajectory. Defaults to all of them."),
) -> None:
    """Show where a trajectory stands: question, live positions, what is open.

    Purpose (for you): the one screen you want on a Monday morning, or before a
    supervision meeting -- what you are asking, where you got to, and what you
    still owe an answer to.

    Everything here is derived from the log and concerns one trajectory at a
    time. Nothing is compared across trajectories or across people, and there is
    no number summarising how any of it is going.
    """
    repo = _repo()
    traj_ids = [repo.resolve_trajectory(traj)] if traj else repo.trajectory_ids()
    if not traj_ids:
        _echo("nothing recorded yet.")
        _echo('start with: grrp new "the question you are actually working on"')
        return

    for traj_id in traj_ids:
        trajectory = repo.trajectory(traj_id)
        _echo(f"{trajectory.get('title')}   ({traj_id})")
        _echo(f"  question   {trajectory.get('question')}")
        _echo()

        live = views.current_states(repo, traj_id)
        _echo("  live position" + ("s" if len(live) > 1 else ""))
        if not live:
            _echo("    (none yet - take one with: grrp claim -m \"...\")")
        for state_id in live:
            _echo(f"    {canonical.short(state_id)}  {_headline(repo, traj_id, state_id)}")
        if len(live) > 1:
            _echo("    these diverged. Neither is the canonical one.")
        _echo()

        items = views.open_items(repo, traj_id)
        _echo("  unanswered")
        if not items:
            _echo("    (nothing)")
        for item in items:
            record = item.transition
            target = item.transition.get("posterior_state") or ""
            _echo(
                f"    {canonical.short(record['id'])}  {record.get('act'):<11} "
                f"{_headline(repo, traj_id, target, width=56)}"
            )
        _echo()

        releases = repo.releases(traj_id)
        if releases:
            _echo("  released")
            for release in releases:
                _echo(
                    f"    {canonical.short(release['id'])}  {release.get('time', '')[:10]}  "
                    f"{_headline(repo, traj_id, release['state'], width=52)}"
                )
            _echo()

        if not views.has_attestation(repo, traj_id):
            _echo("  unattested throughout - useful to you, evidence to nobody")
        _echo()


@command(name="log")
def log_cmd(
    traj: str = typer.Argument(None, help="Trajectory. Defaults to all of them."),
) -> None:
    """Show the transitions, oldest first.

    Purpose (for you): to reconstruct what happened without reading your own
    notes chronologically and guessing. This is what you paste into a progress
    report or a supervision meeting.
    """
    repo = _repo()
    traj_ids = [repo.resolve_trajectory(traj)] if traj else repo.trajectory_ids()
    for traj_id in traj_ids:
        trajectory = repo.trajectory(traj_id)
        _echo(f"{traj_id} - {trajectory.get('title')}")
        for record in repo.transitions(traj_id):
            registration = record.get("registration") or {}
            mark = " " if registration.get("attested") else "!"
            if record.get("kind") == "operation":
                _echo(
                    f"  . {canonical.short(record['id'])}  {record.get('performed')}  "
                    f"[{record.get('operation')}]".ljust(14)
                    + f" ground {record.get('ground')}"
                )
                continue
            _echo(
                f"  {mark} {canonical.short(record['id'])}  {record.get('performed')}  "
                f"{record.get('act'):<14} {record.get('disposition')}"
            )
            state_id = record.get("posterior_state")
            if state_id:
                _echo(f"      {_headline(repo, traj_id, state_id, width=88)}")
        _echo()
    _echo("!  registered by the party who performed it - unattested")
    _echo(".  an operation on the record, not a transition")


@command(name="state")
def state_cmd(
    traj: str = typer.Argument(None, help="Trajectory."),
    full: bool = typer.Option(False, "--full", help="Print the whole content."),
) -> None:
    """Show the live positions, derived from the log.

    Purpose (for you): to see where the work actually stands, including when it
    stands in two places at once.

    Nothing here is stored. If several positions are live, all are shown and
    none is marked principal: in inquiry a fork is often the right outcome.
    """
    repo = _repo()
    traj_ids = [repo.resolve_trajectory(traj)] if traj else repo.trajectory_ids()
    for traj_id in traj_ids:
        trajectory = repo.trajectory(traj_id)
        _echo(f"{traj_id} - {trajectory.get('title')}")
        live = views.current_states(repo, traj_id)
        if not live:
            _echo("  (no live position)")
            opening = views.opening_state(repo, traj_id)
            if opening:
                _echo(f"  question {canonical.short(opening)}")
                _echo(f"    {trajectory.get('question')}")
        for state_id in live:
            content = repo.read_state(traj_id, state_id) or "(redacted)"
            _echo(f"  {canonical.short(state_id)}")
            body = content.strip() if full else content.strip().splitlines()[0]
            for line in body.splitlines():
                _echo(f"    {line}")
        if len(live) > 1:
            _echo("  these are divergent. Neither is the canonical one.")
        _echo()


@command(name="open")
def open_cmd(
    traj: str = typer.Argument(None, help="Trajectory. Defaults to all of them."),
) -> None:
    """List what is unresolved: the register of open problems.

    Purpose (for you): the list of things you still owe an answer to, which is
    the thing you would otherwise keep on a scrap of paper.

    It is also the entry path. Every item is an identified state that someone
    with no prior standing in your work can reference in a challenge, a
    connection or a verification, and be judged on the act itself.
    """
    repo = _repo()
    traj_ids = [repo.resolve_trajectory(traj)] if traj else repo.trajectory_ids()
    for traj_id in traj_ids:
        items = views.open_items(repo, traj_id)
        trajectory = repo.trajectory(traj_id)
        _echo(f"{traj_id} - {trajectory.get('title')}")
        if not items:
            _echo("  (nothing unresolved)")
        for item in items:
            record = item.transition
            headline = (item.text or "").strip().splitlines()
            _echo(
                f"  {canonical.short(record['id'])}  {record.get('act'):<12} "
                f"{record.get('performed')}"
            )
            if headline:
                _echo(f"      {headline[0][:88]}")
            if item.attaches_to:
                _echo(f"      against {canonical.short(item.attaches_to)}")
        _echo()


@command(name="export")
def export_cmd(
    release_ref: str = typer.Argument(..., help="The release to emit."),
    out: Path = typer.Option(None, "-o", "--out", help="Write to a file."),
) -> None:
    """Emit a citable document from a release.

    Purpose (for you): the paper-shaped object your institution accepts,
    assembled from records you made while working, with no additional writing.

    It carries an appendix nothing else can produce: the chain of transitions
    that led here, the parties attributed to particular changes, and the
    objections standing at release.
    """
    repo = _repo()
    traj_id, release_record = repo.resolve_release(release_ref)
    document = export.render_release(repo, traj_id, release_record)
    if out:
        out.write_text(document, encoding="utf-8")
        _echo(f"written to {out}")
    else:
        _echo(document)


@command(name="check")
def check_cmd() -> None:
    """Verify the record, and this implementation against the protocol.

    Purpose (for you): to know whether the record you are relying on has been
    altered, and whether the tool you are relying on has drifted. Both fail
    silently otherwise.
    """
    repo = _repo()
    report = check_module.check_repo(repo)
    for note in report.notes:
        _echo(f"note   {note}")
    for failure in report.failures:
        _echo(f"FAIL   {failure}")
    _echo()
    if report.ok:
        _echo("ok - identifiers recompute, the graph is acyclic, no scalars are defined")
    else:
        _echo(f"{len(report.failures)} failure(s)")
        raise typer.Exit(code=1)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _resolve_prior(repo: Repo, ref: str | None, traj: str | None = None) -> tuple[str, str]:
    """Find the state an act attaches to.

    Accepts a state identifier or prefix, a trajectory, or nothing at all. With
    nothing, it uses the live position, which is what you almost always mean and
    saves copying a hash out of another command's output.

    A transition still references a specific identified prior state either way.
    Where the answer is not unique -- a divergence -- this refuses and lists the
    candidates rather than picking one, because nothing in the design gives it a
    basis for picking.
    """
    scope = repo.resolve_trajectory(traj) if traj else None

    if ref:
        try:
            traj_id = repo.resolve_trajectory(ref)
        except (errors.UnknownReference, errors.AmbiguousReference):
            return repo.resolve_state(scope, ref)
    else:
        traj_id = scope or repo.resolve_trajectory(None)

    live = views.current_states(repo, traj_id)
    if len(live) == 1:
        return traj_id, live[0]
    if not live:
        # No position taken yet: the act attaches to the question.
        opening = views.opening_state(repo, traj_id)
        if opening:
            return traj_id, opening
        raise errors.ConstraintViolation(
            "C4",
            f"{traj_id} has no state to attach to. Name a state explicitly.",
        )
    raise errors.AmbiguousReference(
        f"{traj_id} has several live positions and none is the canonical one. "
        "Name the one you mean:\n"
        + "\n".join(
            f"  {canonical.short(s)}  {_headline(repo, traj_id, s)}" for s in live
        )
    )


def _headline(repo: Repo, traj_id: str, state_id: str, width: int = 72) -> str:
    content = repo.read_state(traj_id, state_id)
    if not content:
        removal = views.redactions(repo, traj_id).get(state_id)
        if removal:
            return f"(redacted on the ground of {removal.get('ground')})"
        return "(content not available)"
    first = content.strip().splitlines()[0]
    return first if len(first) <= width else first[: width - 1] + "…"


def _parents_for(repo: Repo, traj_id: str, state_id: str | None) -> list[str]:
    """The transitions that produced the state being altered."""
    if not state_id:
        return []
    return [
        record["id"]
        for record in repo.transitions(traj_id)
        if record.get("posterior_state") == state_id
    ][-1:]


def main() -> None:
    # An emitted document is UTF-8 whether or not the console agrees. Ask the
    # console to keep up rather than degrading the record to fit it.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    try:
        app()
    except errors.GrrpError as error:
        typer.secho(str(error), err=True, fg=typer.colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
