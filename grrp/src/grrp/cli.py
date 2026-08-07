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
    bundle,
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
    "seal": "What are you recording now that you are not ready to show anyone?",
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

    _echo(f"initialised in {root}")
    _echo(f"  you are {party}")
    _echo("  tier     personal - useful alone, and carrying no evidential weight")
    _echo("")
    _echo('next: grrp new "the question you are actually working on"')
    _commit(repo, [repo.profile_path, repo.grrp_dir / ".gitignore"], "init")


@command()
def profile(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable, for another implementation."),
) -> None:
    """Print what another implementation would need to read your records.

    Purpose (for you): to know which protocol version, hash and vocabularies
    your record commits to, before you rely on anyone else being able to read it.

    Two implementations exchanging records must agree on the record structure,
    the act and disposition vocabularies, the bound vocabularies and their
    versions, the identifier construction and the signature scheme. On nothing
    else -- not storage, not transport, not interface, not serialisation.
    """
    repo = _repo()
    if json_out:
        import json

        _echo(json.dumps(bundle.declaration(repo), indent=2, sort_keys=True))
        return
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
        subject=state_id,
        payload={"ground": ground},
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
# disclosure
# --------------------------------------------------------------------------- #


@command(name="charter")
def charter_cmd(
    action: str = typer.Argument("show", help="show or adopt."),
    classes: str = typer.Option(
        None, "--classes", help="Your disclosure classes, narrowest first: private,group,public"
    ),
    identifier: str = typer.Option(None, "--id", help="A persistent identifier for the charter."),
) -> None:
    """Adopt or print the operating charter this record runs under.

    Purpose (for you): to decide, once, who your work is visible to -- and to
    have a record that says which rules were in force when each entry was made.

    The protocol supplies no model charter, no default charter and no minimum
    standard of conduct. A specification supplying one would be a specification
    of governance, and communities that reject the model could not conform. It
    asks only that certain matters be settled somewhere, because a record
    referring to a class nobody has defined is uninterpretable.
    """
    repo = _repo()
    if action == "show":
        charter = repo.charter()
        if not charter:
            _echo("no charter adopted.")
            _echo("")
            _echo("Without one there are no disclosure classes, so nothing can be")
            _echo("restricted or released to anyone in particular.")
            _echo("")
            _echo("  grrp charter adopt --classes private,group,public")
            return
        for key, value in charter.items():
            _echo(f"{key:14} {value}")
        return

    if action != "adopt":
        raise errors.GrrpError("say: grrp charter show | grrp charter adopt --classes a,b,c")
    if not classes:
        raise errors.GrrpError(
            "name your disclosure classes, narrowest first:\n"
            "  grrp charter adopt --classes private,group,public\n"
            "The protocol supplies no default set: which classes exist, and who belongs "
            "to each, is yours to decide."
        )

    names = [name.strip() for name in classes.split(",") if name.strip()]
    if len(names) < 2:
        raise errors.GrrpError("a charter needs at least two classes to order by inclusion")

    existing = repo.charter()
    version = int(existing.get("version", 0)) + 1 if existing else 1
    store.write_yaml(
        repo.charter_path,
        {
            "id": identifier or existing.get("id") if existing else identifier or "charter:local",
            "version": version,
            "protocol": store.PROTOCOL,
            "classes": names,
            "adopted": store.now(),
            # Left for the community to settle. The protocol carries the fields
            # and interprets none of them.
            "membership": existing.get("membership") if existing else {},
            "assurance": existing.get("assurance") if existing else {},
            "retention": existing.get("retention") if existing else None,
            "consent": existing.get("consent") if existing else None,
            "amendment": existing.get("amendment") if existing else None,
            "extended_targets": existing.get("extended_targets") if existing else [],
            "extended_triggers": existing.get("extended_triggers") if existing else [],
        },
    )
    _echo(f"charter version {version}")
    _echo(f"  classes  {' < '.join(names)}   (narrowest first, ordered by inclusion)")
    _echo("")
    _echo("  An amendment applies to records made after it and never alters the")
    _echo("  interpretation of records made before it.")
    _echo("")
    _echo("  Still yours to settle, and the protocol interprets none of it:")
    _echo("  membership of each class, assurance per act, retention, consent, amendment.")
    _commit(repo, [repo.charter_path], f"charter v{version}")


@command()
def disclose(
    transition: str = typer.Argument(..., help="The transition to disclose."),
    class_: str = typer.Option(..., "--class", help="A class from your charter."),
    ground: list[str] = typer.Option(
        None, "--ground", help=f"Why. One of: {', '.join(vocab.GROUNDS)}. Repeatable."
    ),
    release_at: str = typer.Option(
        None, "--release-at", help="Date this widens by itself. Vulnerability only."
    ),
    release_class: str = typer.Option(
        None, "--release-class", help="The class it widens to. Defaults to the widest."
    ),
    traj: str = TRAJ_OPTION,
) -> None:
    """Disclose a transition at a class, on a stated ground.

    Purpose (for you): so that work you cannot show everyone is visible to the
    people who need it, without your reasons for withholding it being a matter
    of anyone's guesswork -- including yours, later.

    A restriction here is an assertion, dated and attributable, where under
    ordinary practice it is a default that asserts nothing. Every ground leaves
    a residue that must still be disclosed, and that residue is the one question
    a reader can always ask: was what the ground leaves disclosable in fact
    disclosed?
    """
    repo = _repo()
    available = repo.classes()
    if not available:
        raise errors.GrrpError(
            "no charter, so there are no classes to disclose at.\n"
            "  grrp charter adopt --classes private,group,public"
        )
    if class_ not in available:
        raise errors.GrrpError(
            f"{class_!r} is not a class in your charter. Classes: {' < '.join(available)}"
        )

    traj_id = repo.resolve_trajectory(traj) if traj else None
    traj_id, target = repo.resolve_transition(traj_id, transition)

    widest = available[-1]
    grounds = list(ground or [])
    for name in grounds:
        if name not in vocab.GROUNDS:
            raise errors.GrrpError(
                f"{name!r} is not a ground of restriction. The set is closed: "
                f"{', '.join(vocab.GROUNDS)}.\n"
                "A community free to invent grounds is free to withhold anything by "
                "naming a reason."
            )
    if class_ != widest and not grounds:
        raise errors.ConstraintViolation(
            "C7",
            f"disclosing at {class_!r} is less than the widest class ({widest!r}), "
            "so it must declare a ground.\n"
            f"  --ground {' | '.join(vocab.GROUNDS)}",
        )

    if release_at and "vulnerability" not in grounds:
        raise errors.GrrpError(
            "a schedule belongs to exploratory vulnerability, which is the only ground "
            "with a terminus.\n"
            "Rivalry ends when the resource is uncontended, appropriability when the "
            "funding purpose is served -- neither observable from here. Hazard does not end."
        )

    history = views.disclosure_operations(repo, traj_id, target["id"])
    # Chain the operations, so their order is fixed by the graph rather than by
    # a timestamp that two changes in the same second would share.
    chain_parents = [target["id"]] + ([history[-1]["id"]] if history else [])

    current = views.disclosure_of(repo, traj_id, target["id"])
    if current:
        old_index = available.index(current["effective_class"]) if current["effective_class"] in available else -1
        if available.index(class_) < old_index:
            raise errors.ConstraintViolation(
                "C7",
                f"disclosure may widen and never narrow. {canonical.short(target['id'])} is "
                f"at {current['effective_class']!r}; {class_!r} is narrower.\n"
                "A party who has read a record retains what they read, so an operation "
                "offering the appearance of withdrawal would misdescribe to your own "
                "participants a state of affairs obtaining outside this record.",
            )
        old_schedule = current.get("release_at")
        if old_schedule and release_at and str(release_at) > str(old_schedule):
            _echo(f"refused: a schedule may be shortened, never extended ({old_schedule}).")
            _echo("  Recording the attempt, because it should be visible that it was made.")
            attempt = store.new_operation(
                trajectory=traj_id,
                operation="disclosure_changed",
                performer=repo.party(),
                subject=target["id"],
                payload={
                    "attempted": "extend_schedule",
                    "from": str(old_schedule),
                    "to": str(release_at),
                    "refused": True,
                },
                parents=chain_parents,
            )
            path = repo.append_transition(traj_id, attempt)
            _commit(repo, [path], f"refused schedule extension {canonical.short(attempt['id'])}")
            raise errors.ConstraintViolation(
                "C7",
                "a delay that can be extended indefinitely is a permanent withholding "
                "made to look temporary.",
            )

    payload: dict = {"class": class_, "grounds": grounds}
    if release_at:
        payload["release_at"] = release_at
        payload["release_class"] = release_class or widest
    charter = repo.charter() or {}
    payload["charter"] = {"id": charter.get("id"), "version": charter.get("version")}

    record = store.new_operation(
        trajectory=traj_id,
        operation="disclosure_changed",
        performer=repo.party(),
        subject=target["id"],
        payload=payload,
        parents=chain_parents,
    )
    path = repo.append_transition(traj_id, record)

    _echo(f"disclosed {canonical.short(target['id'])}  at {class_}")
    for name in grounds:
        _echo(f"  ground   {name} - {vocab.GROUNDS[name]['object']}")
    if release_at:
        _echo(f"  widens to {payload['release_class']} on {release_at}, by itself")
    _commit(repo, [path], f"disclose {canonical.short(record['id'])}")

    if grounds:
        _echo("")
        _echo("  What this ground leaves disclosable, and what you must still disclose:")
        for name in grounds:
            _echo(f"    {name}: {vocab.GROUNDS[name]['residue']}")
        if len(grounds) > 1:
            _echo("")
            _echo("  Several grounds: the residue is the intersection of theirs. Each is an")
            _echo("  assertion a reader may find false, so declaring more is not free.")
        _echo("")
        _echo(f"  Misapplied, this is: {vocab.GROUNDS[grounds[0]]['failure']}.")


@command(name="grounds")
def grounds_cmd() -> None:
    """Print the four grounds of restriction and what each leaves disclosable.

    Purpose (for you): to pick the ground that actually applies before you
    withhold something, and to know what you are still obliged to disclose
    having withheld it.
    """
    for name, ground in vocab.GROUNDS.items():
        _echo(name)
        _echo(f"  when      {ground['condition']}")
        _echo(f"  restricts {ground['object']}")
        _echo(f"  residue   {ground['residue']}")
        _echo(f"  misapplied {ground['failure']}")
        _echo(f"  ends      {ground['terminus'] or 'no terminus'}")
        _echo()
    _echo("The set is closed. A restriction fitting none of the four is inadmissible,")
    _echo("because a community free to invent grounds is free to withhold anything by")
    _echo("naming a reason.")


# --------------------------------------------------------------------------- #
# the open tier
# --------------------------------------------------------------------------- #


@command(name="bundle")
def bundle_cmd(
    traj: str = typer.Argument(None, help="Trajectory. Defaults to all of them."),
    out: Path = typer.Option(Path("trajectory.zip"), "-o", "--out", help="Where to write it."),
    include_restricted: bool = typer.Option(
        False,
        "--include-restricted",
        help="Include content restricted below the widest class. Off by default.",
    ),
) -> None:
    """Pack the complete record so it can be continued elsewhere.

    Purpose (for you): so that leaving -- a service, a group, an institution --
    costs you the arrangement and not the work. You can take this to another
    machine, another implementation, or nobody in particular, and continue.

    That capacity is the only bound this design places on the authority of
    anyone holding a position over your record, including whoever wrote this
    tool. There are no rules here addressed to position holders, because
    enforcing such rules needs an enforcing party, and that party would hold a
    position in turn.
    """
    repo = _repo()
    traj_ids = [repo.resolve_trajectory(traj)] if traj else repo.trajectory_ids()
    if not traj_ids:
        raise errors.GrrpError("nothing to bundle yet")

    manifest = bundle.write(repo, out, traj_ids, include_restricted=include_restricted)
    _echo(f"bundled  {out}")
    for traj_id in traj_ids:
        _echo(f"  {traj_id}")
    if manifest["content_withheld"]:
        _echo("")
        _echo("  content withheld for these states, the skeletons travelling without it:")
        for state_id in manifest["content_withheld"]:
            _echo(f"    {canonical.short(state_id)}")
        _echo("  pass --include-restricted if the recipient can honour the class.")
    _echo("")
    _echo("  Continue it anywhere: grrp continue " + out.name)


@command(name="continue")
def continue_cmd(
    source: Path = typer.Argument(..., help="A bundle to continue."),
) -> None:
    """Continue a record obtained from elsewhere, as one graph.

    Purpose (for you): to pick up a line of work where another party left it --
    or to carry your own between machines -- without asking anyone's permission
    and without the two copies becoming two records.

    Nothing that arrives is altered, and that includes normalisation: rewriting
    received records into this tool's preferred form would invalidate their
    signatures. What cannot be verified is kept and marked, because discarding
    what an implementation does not understand is how a record quietly becomes
    a different record.
    """
    repo = _repo()
    if not source.is_file():
        raise errors.GrrpError(f"no bundle at {source}")

    manifest = bundle.read_manifest(source)
    version = manifest.get("protocol")
    if version != store.PROTOCOL:
        kept = repo.grrp_dir / "received" / source.name
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_bytes(source.read_bytes())
        raise errors.GrrpError(
            f"this bundle is {version!r}; this implementation is {store.PROTOCOL!r}.\n"
            f"Kept unprocessed at {kept}. Records are not read as though they were of a "
            "version they are not: a record created under one version asserts what that "
            "version's fields meant."
        )

    receipt = bundle.apply(repo, source)

    _echo(f"continued from {source.name}")
    for traj_id in receipt.trajectories:
        _echo(f"  {traj_id}")
    for identifier in receipt.added:
        _echo(f"  + {identifier[:12]}")
    for identifier in receipt.already_held:
        _echo(f"  = {identifier[:12]}  (already held, untouched)")

    if receipt.unverified:
        _echo("")
        _echo("  unverified - retained and marked, not discarded:")
        for identifier in receipt.unverified:
            _echo(f"    {identifier}")
        _echo("  Either the registrar's key is unknown here, or the signature does not verify.")
    if receipt.missing_parents:
        _echo("")
        _echo("  parents not present. The subgraph is retained and is not complete;")
        _echo("  nothing has been synthesised to fill the gaps:")
        for identifier in sorted(set(receipt.missing_parents)):
            _echo(f"    {identifier}")
    if receipt.content_withheld:
        _echo("")
        _echo("  content withheld by the sender for some states; their skeletons are here.")

    _echo("")
    _echo("  Anything you record now references these as parents: one graph, not two.")
    _commit(repo, [repo.root / "trajectories"], f"continue {source.name}")


@command(name="deposit")
def deposit_cmd(
    release_ref: str = typer.Argument(..., help="The release to deposit."),
    out: Path = typer.Option(None, "-o", "--out", help="Directory to write the package to."),
    identifier: str = typer.Option(
        None, "--identifier", help="Record an identifier an archive has issued."
    ),
) -> None:
    """Package a release for an archive, or record the identifier one issued.

    Purpose (for you): a citable, archived object with its lineage attached,
    held somewhere that outlives your laptop and your institution.

    Released material only. Depositing sealed or restricted content with a
    third party would place it outside the disclosure regime that governs it.
    """
    repo = _repo()
    traj_id, release = repo.resolve_release(release_ref)

    if identifier:
        record = store.new_operation(
            trajectory=traj_id,
            operation="deposit_recorded",
            performer=repo.party(),
            subject=release["id"],
            payload={"identifier": identifier, "scheme": store.external_reference(identifier)["scheme"]},
            parents=[release["id"]],
        )
        path = repo.append_transition(traj_id, record)
        _echo(f"recorded  {identifier}  for release {canonical.short(release['id'])}")
        _commit(repo, [path], f"deposit {canonical.short(record['id'])}")
        return

    directory = out or Path(f"deposit-{canonical.short(release['id'])}")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "release.md").write_text(
        export.render_release(repo, traj_id, release), encoding="utf-8"
    )
    store.write_yaml(directory / "release.yaml", dict(release))
    store.write_yaml(
        directory / "declaration.yaml",
        {
            "protocol": store.PROTOCOL,
            "deposited": store.now(),
            "trajectory": traj_id,
            "release": release["id"],
            "declaration": bundle.declaration(repo),
        },
    )
    bundle.write(repo, directory / "record.zip", [traj_id], include_restricted=False)

    _echo(f"packaged  {directory}")
    _echo("  release.md         the citable document, with its lineage")
    _echo("  release.yaml       the release record")
    _echo("  declaration.yaml   what another implementation needs to read it")
    _echo("  record.zip         the trajectory, continuable elsewhere")
    _echo("")
    _echo("  Deposit it with an archive that operates independently of this")
    _echo("  implementation and states its preservation commitments, then:")
    _echo(f"    grrp deposit {canonical.short(release['id'])} --identifier <doi:...>")


@command(name="seal")
def seal_cmd(
    traj: str = typer.Argument(None, help="Trajectory."),
    message: str = typer.Option(None, "-m", "--message", help="The content to seal."),
    file: Path = typer.Option(None, "--file", help="Read the content from a file."),
    anchor: str = typer.Option(
        None, "--anchor", help="How the time was anchored, if you anchored it."
    ),
) -> None:
    """Register that you held something at a time, without disclosing what.

    Purpose (for you): to start recording on the first day of a piece of work
    you are not ready to show anyone, instead of the alternative, which is
    silence.

    It records that you held content with this identifier at this time. It does
    not establish priority: priority is a community's recognition of a claim,
    and no tool manufactures that. And a sealed state generates nothing -- no
    objection, no connection, no encounter -- because nobody can see it.
    """
    repo = _repo()
    traj_id, prior = _resolve_prior(repo, traj, None)
    text = _message(message, file, "seal")

    content = canonical.normalise_content(text)
    state_id = canonical.state_id(content)
    sealed = repo.grrp_dir / "sealed"
    sealed.mkdir(parents=True, exist_ok=True)
    (sealed / f"{state_id.split(':')[-1]}.md").write_text(content, encoding="utf-8")

    record = store.new_transition(
        trajectory=traj_id,
        act="claim",
        performer=repo.party(),
        parents=_parents_for(repo, traj_id, prior),
        prior_state=prior,
        posterior_state=state_id,
        target="hypothesis",
        trigger="self",
        disposition="accepted",
    )
    _record(repo, traj_id, record, "sealed  ")
    _echo(f"  content is at .grrp/sealed/, which is never committed and never exported.")
    _echo(f"  open it when you choose: grrp openseal {canonical.short(state_id)}")
    _echo("")
    if anchor:
        _echo(f"  time anchored by: {anchor}")
    else:
        _echo("  The time here is your own assertion. It is evidence to a party who does")
        _echo("  not trust you only if it is anchored in a medium you do not control --")
        _echo("  publish the identifier somewhere public, then record it with --anchor.")


@command(name="openseal")
def openseal_cmd(
    state: str = typer.Argument(..., help="The sealed state to open."),
    traj: str = TRAJ_OPTION,
) -> None:
    """Disclose content you sealed earlier, so anyone can check it.

    Purpose (for you): to show, when you are ready, that what you are saying
    now is what you held then.

    Any party can verify from the record alone that the content yields the
    identifier registered earlier. It proves possession at a time, and nothing
    about understanding, and nothing against a party who arrived at the same
    place independently.
    """
    repo = _repo()
    traj_id = repo.resolve_trajectory(traj) if traj else None
    traj_id, state_id = repo.resolve_state(traj_id, state)

    source = repo.grrp_dir / "sealed" / f"{state_id.split(':')[-1]}.md"
    if not source.is_file():
        raise errors.GrrpError(f"nothing sealed under {canonical.short(state_id)}")

    content = source.read_text(encoding="utf-8")
    if canonical.state_id(content) != state_id:
        raise errors.GrrpError(
            "the sealed content does not yield the registered identifier. "
            "Recording the failure rather than removing either record."
        )

    target = repo.state_path(traj_id, state_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    source.unlink()

    _echo(f"opened   {canonical.short(state_id)}")
    _echo("  it yields the identifier registered earlier, and anyone holding both can check.")
    _commit(repo, [target], f"open seal {canonical.short(state_id)}")


@command(name="custody")
def custody_cmd(
    action: str = typer.Argument("show", help="show, add, or succession."),
    value: str = typer.Argument(None, help="A party holding a copy, or the arrangement."),
) -> None:
    """Record who else holds a copy, and what happens if you stop.

    Purpose (for you): so that the record survives one disk, one institution
    and one person, and so that anyone relying on it knows in advance whose
    commitment they are relying on.

    A right to obtain a record from a party who has ceased to exist is a right
    without an object.
    """
    repo = _repo()
    profile = repo.profile()

    if action == "show":
        holders = profile.get("custody") or []
        _echo("custody")
        for holder in holders or ["(nobody but you)"]:
            _echo(f"  {holder}")
        _echo("")
        _echo(f"succession  {profile.get('succession') or '(not published)'}")
        if len(holders) < 2:
            _echo("")
            _echo("  A record held by one party does not survive that party. At the group")
            _echo("  tier and above it should be held by at least two who do not share an")
            _echo("  operator: grrp custody add <who>")
        return

    if action == "add":
        if not value:
            raise errors.GrrpError("grrp custody add <who holds a copy>")
        profile["custody"] = [*(profile.get("custody") or []), value]
        store.write_yaml(repo.profile_path, profile)
        _echo(f"custody  {value}")
    elif action == "succession":
        if not value:
            raise errors.GrrpError("grrp custody succession \"<what becomes of the records>\"")
        profile["succession"] = value
        store.write_yaml(repo.profile_path, profile)
        _echo("succession arrangement published in the profile.")
        _echo("  Durability must not be claimed without one.")
    else:
        raise errors.GrrpError("say: grrp custody show | add <who> | succession \"<what>\"")
    _commit(repo, [repo.profile_path], f"custody {action}")


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

        restricted = [
            (record, views.disclosure_of(repo, traj_id, record["id"]))
            for record in repo.transitions(traj_id)
            if record.get("kind") != "operation"
        ]
        restricted = [
            (record, state) for record, state in restricted
            if state and state.get("grounds")
        ]
        if restricted:
            _echo("  restricted")
            for record, state in restricted:
                schedule = state.get("release_at")
                when = f", widens to {state.get('release_class')} on {schedule}" if schedule else ""
                _echo(
                    f"    {canonical.short(record['id'])}  {state['effective_class']}  "
                    f"({', '.join(state['grounds'])}){when}"
                )
            _echo("    each ground leaves a residue that must still be disclosed: grrp grounds")
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
                    + f" {_operation_summary(record)}"
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


def _operation_summary(record: dict) -> str:
    payload = record.get("payload") or {}
    if record.get("operation") == "redaction":
        return f"ground {payload.get('ground')}"
    if record.get("operation") == "disclosure_changed":
        if payload.get("refused"):
            return f"refused: {payload.get('attempted')}"
        grounds = ", ".join(payload.get("grounds") or []) or "no ground"
        return f"class {payload.get('class')} ({grounds})"
    return ""


def _headline(repo: Repo, traj_id: str, state_id: str, width: int = 72) -> str:
    content = repo.read_state(traj_id, state_id)
    if not content:
        removal = views.redactions(repo, traj_id).get(state_id)
        if removal:
            ground = (removal.get("payload") or {}).get("ground")
            return f"(redacted on the ground of {ground})"
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
