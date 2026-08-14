"""A local page for reading a record and adding to it.

This is **Level 3**: an application over the record, outside conformance. The
protocol is implementable with none of it, every operation it offers is
available from the command line, and nothing in the record depends on it. If
this file were deleted the record would be unaffected -- which a test checks
rather than this comment asserting.

It binds to the loopback interface only. There is no account, no session, no
telemetry, and nothing leaves the machine. The one concession to being a page
in a browser is a per-run token in every form, so that another page you happen
to have open cannot post to it.

What it deliberately does not do, because the design forbids it and a screen is
where the temptation is strongest, and where a reader would most readily
believe a number if one appeared:

    no quantity over participants or trajectories -- no counts to compare, no
    progress bars, no health, no activity;
    no ordering of branches, and no branch marked principal, default or current;
    no combining of two states, and not the word for it;
    no control that narrows disclosure, and none that approves or refuses an
    absorption.
"""

from __future__ import annotations

import html
import http.cookies
import secrets
import threading
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from . import accounts, actions, canonical, errors, gitutil, identity, store, views, vocab
from .store import Repo

STYLE = """
:root { --bg:#fbfbfa; --fg:#1a1a1a; --dim:#6b6b6b; --line:#e2e0dc; --card:#fff;
        --live:#1f6f4a; --open:#8a5a00; --stop:#8a2020; --past:#b6b2ad; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#161514; --fg:#e8e6e3; --dim:#9a9691; --line:#2f2d2b; --card:#1d1c1a;
          --live:#6fc59a; --open:#d5a04a; --stop:#d98080; --past:#55514d; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.55 ui-serif,Georgia,serif; }
main { max-width:56rem; margin:0 auto; padding:2rem 1.25rem 5rem; }
h1 { font-size:1.5rem; margin:0 0 .25rem; font-weight:600; }
h2 { font-size:.78rem; text-transform:uppercase; letter-spacing:.09em; color:var(--dim);
     font-weight:600; margin:2.25rem 0 .6rem; }
a { color:inherit; }
.q { color:var(--dim); margin:0 0 1.5rem; }
.card { background:var(--card); border:1px solid var(--line); border-radius:6px;
        padding:.7rem .9rem; margin:.5rem 0; }
.card.live { border-left:3px solid var(--live); }
.card.open { border-left:3px solid var(--open); }
.card.stop { border-left:3px solid var(--stop); }
.id { font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--dim); }
.meta { font-size:.82rem; color:var(--dim); margin-top:.3rem; }
.note { font-size:.85rem; color:var(--dim); border-left:2px solid var(--line);
        padding-left:.8rem; margin:1rem 0; }
form { margin:.6rem 0 0; }
textarea { width:100%; min-height:5rem; font:inherit; padding:.6rem; border-radius:5px;
           border:1px solid var(--line); background:var(--bg); color:var(--fg); }
select,input[type=text] { font:inherit; padding:.35rem; border-radius:5px;
           border:1px solid var(--line); background:var(--bg); color:var(--fg); }
input[type=text] { min-width:14rem; }
button { font:inherit; padding:.4rem 1rem; border-radius:5px; border:1px solid var(--line);
         background:var(--fg); color:var(--bg); cursor:pointer; }
button.quiet { background:transparent; color:var(--fg); }
.row { display:flex; gap:.6rem; align-items:center; flex-wrap:wrap; margin-top:.5rem; }
.warn { color:var(--stop); }
.divergent { display:grid; grid-template-columns:repeat(auto-fit,minmax(16rem,1fr)); gap:.6rem; }
.scroll { overflow-x:auto; border:1px solid var(--line); border-radius:6px;
          background:var(--card); padding:.5rem; }
footer { margin-top:4rem; padding-top:1rem; border-top:1px solid var(--line);
         font-size:.8rem; color:var(--dim); }
header.cover { margin-bottom:1.5rem; }
.lede { color:var(--dim); max-width:44rem; margin:.4rem 0 0; }
.searchbar { display:flex; gap:.5rem; align-items:center; margin:1.5rem 0 .5rem; }
.searchbar input[type=text] { flex:1; min-width:0; padding:.55rem .7rem; }
.searchbar .clear { font-size:.82rem; color:var(--dim); }
mark { background:var(--open); color:var(--bg); border-radius:2px; padding:0 .15em; }
.snippet { margin-top:.35rem; }
.traj { margin:.55rem 0 0; padding-left:.75rem; border-left:2px solid var(--line); }
.traj a { text-decoration:none; }
.traj a:hover { text-decoration:underline; }
.open-mark { color:var(--open); }
.whoami { display:flex; align-items:center; gap:.5rem; font-size:.82rem; color:var(--dim);
          border-bottom:1px solid var(--line); padding-bottom:.6rem; margin-bottom:1.5rem; }
.whoami form { margin:0 0 0 auto; }
.whoami button { padding:.15rem .6rem; font-size:.82rem; }
.who { display:flex; gap:.6rem; align-items:baseline; }
.who form { margin:0; }
.signin label { display:block; margin:.7rem 0; font-size:.82rem; color:var(--dim); }
.signin input { display:block; width:100%; max-width:22rem; margin-top:.25rem;
                font:inherit; padding:.5rem; border-radius:5px; border:1px solid var(--line);
                background:var(--bg); color:var(--fg); }
.buttons button { background:transparent; color:var(--fg); }
.buttons button:hover { background:var(--fg); color:var(--bg); }
.act textarea { min-height:4.5rem; }
.n-box { fill:var(--card); stroke:var(--line); }
.n-box.live { stroke:var(--live); stroke-width:2; }
.n-box.open { stroke:var(--open); stroke-width:2; }
.n-text { fill:var(--fg); font:12px/1.3 ui-serif,Georgia,serif; }
.n-kind { fill:var(--dim); font:10px ui-monospace,Menlo,monospace;
          text-transform:uppercase; letter-spacing:.08em; }
.n-past .n-text { fill:var(--past); }
.e-line { stroke:var(--line); fill:none; stroke-width:1.5; }
.e-label { fill:var(--dim); font:10px ui-monospace,Menlo,monospace; }
"""

KINDS = {
    "question": ("question", "q"),
    "claim": ("position", "p"),
    "transformation": ("position", "p"),
    "challenge": ("objection", "o"),
    "decision": ("decision", "d"),
    "verification": ("check", "v"),
    "connection": ("connection", "c"),
}


# --------------------------------------------------------------------------- #
# a workspace: zero or more records under one directory
# --------------------------------------------------------------------------- #


@dataclass
class Workspace:
    root: Path

    def records(self) -> list[tuple[str, Repo]]:
        """Records here: this directory if it is one, and any directly inside it."""
        found: list[tuple[str, Repo]] = []
        if (self.root / store.GRRP_DIR).is_dir():
            found.append((self.root.name, Repo(self.root)))
        if self.root.is_dir():
            for child in sorted(self.root.iterdir()):
                if child.is_dir() and (child / store.GRRP_DIR).is_dir():
                    found.append((child.name, Repo(child)))
        return found

    def find(self, name: str) -> Repo:
        for candidate, repo in self.records():
            if candidate == name:
                return repo
        raise errors.UnknownReference(f"no record named {name!r}")

    def primary(self) -> Repo | None:
        return Repo(self.root) if (self.root / store.GRRP_DIR).is_dir() else None


@dataclass
class Found:
    """A trajectory a search turned up, and the line that matched."""

    record: str
    repo: Repo
    traj_id: str
    title: str
    question: str
    snippet: str
    where: str


def search(workspace: Workspace, query: str) -> list[Found]:
    """Find trajectories whose question, title or content mentions something.

    Search **filters; it does not rank.** Matches come back in the same order
    everything else is listed in, because an ordering by relevance is a
    numeric measure over trajectories, and a measure adopted to direct
    attention becomes the object of effort.
    """
    needle = query.strip().lower()
    found: list[Found] = []
    if not needle:
        return found

    for name, repo in workspace.records():
        for traj_id in repo.trajectory_ids():
            data = repo.trajectory(traj_id)
            title = str(data.get("title") or traj_id)
            question = str(data.get("question") or "")

            where, snippet = "", ""
            if needle in title.lower():
                where, snippet = "title", title
            elif needle in question.lower():
                where, snippet = "question", question
            else:
                for record in repo.transitions(traj_id):
                    state_id = record.get("posterior_state")
                    if not state_id:
                        continue
                    content = repo.read_state(traj_id, state_id)
                    if content and needle in content.lower():
                        line = next(
                            (l for l in content.splitlines() if needle in l.lower()), ""
                        )
                        where, snippet = str(record.get("act")), line.strip()
                        break
            if where:
                found.append(Found(name, repo, traj_id, title, question, snippet, where))
    return found


def bundle_module():
    from . import bundle

    return bundle


def _as_workspace(target: Workspace | Repo) -> Workspace:
    return target if isinstance(target, Workspace) else Workspace(target.root)


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #


def _e(text: object) -> str:
    return html.escape(str(text if text is not None else ""))


def _whoami(who: "identity.Identity | None", token: str) -> str:
    """The bar at the top of every page: which key is signing.

    Shown everywhere rather than on a settings screen, because the one thing a
    person must not be wrong about is which party an act will be attributed to.
    """
    if who is None:
        return ""
    return (
        "<div class='whoami'>signing as <strong>"
        f"{_e(who.name)}</strong> <span class='id'>{_e(who.short)}…</span>"
        "<form method='post' action='/sign-out'>"
        f"<input type='hidden' name='token' value='{_e(token)}'>"
        "<button type='submit' class='quiet'>switch</button></form></div>"
    )


def _page(
    title: str,
    body: str,
    who: "identity.Identity | None" = None,
    token: str = "",
) -> bytes:
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{_e(title)}</title><style>{STYLE}</style></head>"
        f"<body><main>{_whoami(who, token)}{body}"
        "<footer>grrp — a local page over your record. Level 3: an application, outside "
        "conformance. Everything here is available from the command line, and the record "
        "does not depend on this page existing.</footer>"
        "</main></body></html>"
    ).encode("utf-8")


def _headline(repo: Repo, traj_id: str, state_id: str | None) -> str:
    if not state_id:
        return "—"
    content = repo.read_state(traj_id, state_id)
    if content:
        return content.strip().splitlines()[0]
    removal = views.redactions(repo, traj_id).get(state_id)
    if removal:
        return f"(redacted on the ground of {(removal.get('payload') or {}).get('ground')})"
    if (repo.grrp_dir / "sealed" / f"{state_id.split(':')[-1]}.md").is_file():
        return "(sealed — held, and disclosed to nobody)"
    return "(content not held here)"


def _wrap(text: str, width: int = 30, lines: int = 2) -> list[str]:
    words, out, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            out.append(current)
            current = word
            if len(out) == lines:
                break
        else:
            current = f"{current} {word}".strip()
    if len(out) < lines and current:
        out.append(current)
    if len(out) == lines and (len(" ".join(out)) < len(text)):
        out[-1] = out[-1][: width - 1] + "…"
    return out or [""]


def graph(repo: Repo, traj_id: str) -> str:
    """The trajectory as a directed acyclic graph.

    Left to right, one column per step away from the question. Divergence is
    two boxes in the same column with the same parent, drawn identically:
    nothing here designates a principal line, because in inquiry a fork is
    frequently the correct outcome, and nothing offers to combine them.
    """
    records = [r for r in repo.transitions(traj_id) if r.get("kind") != "operation"]
    produced_by: dict[str, dict] = {}
    edges: list[tuple[str, str, dict]] = []
    depth: dict[str, int] = {}

    for record in records:
        prior, posterior = record.get("prior_state"), record.get("posterior_state")
        if posterior and posterior not in produced_by:
            produced_by[posterior] = record
        if prior and posterior and prior != posterior:
            edges.append((prior, posterior, record))
            depth.setdefault(prior, 0)
            depth[posterior] = max(depth.get(posterior, 0), depth[prior] + 1)
        elif posterior:
            depth.setdefault(posterior, 0)

    if not produced_by:
        return "<p class=note>Nothing recorded yet.</p>"

    columns: dict[int, list[str]] = {}
    for state_id in produced_by:
        columns.setdefault(depth.get(state_id, 0), []).append(state_id)

    live = set(views.current_states(repo, traj_id))
    unresolved = {
        item.transition.get("posterior_state") for item in views.open_items(repo, traj_id)
    }

    node_w, node_h, col_w, row_h, pad = 196, 58, 254, 84, 18
    width = pad * 2 + (max(columns) + 1) * col_w
    height = pad * 2 + max(len(v) for v in columns.values()) * row_h
    place = {
        state_id: (pad + column * col_w, pad + row * row_h)
        for column, members in columns.items()
        for row, state_id in enumerate(members)
    }

    parts = [
        f"<svg viewBox='0 0 {width} {height}' width='{width}' height='{height}' "
        "role='img' aria-label='trajectory'>"
    ]
    for prior, posterior, record in edges:
        if prior not in place or posterior not in place:
            continue
        x1, y1 = place[prior][0] + node_w, place[prior][1] + node_h / 2
        x2, y2 = place[posterior]
        y2 += node_h / 2
        mid = (x1 + x2) / 2
        parts.append(
            f"<path class='e-line' d='M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}'/>"
            f"<text class='e-label' x='{mid - 18}' y='{(y1 + y2) / 2 - 5}'>"
            f"{_e(record.get('act'))}</text>"
        )

    for state_id, (x, y) in place.items():
        record = produced_by[state_id]
        label, _ = KINDS.get(record.get("act", ""), ("state", "s"))
        classes = "n-box"
        group = ""
        if state_id in live:
            classes += " live"
        elif state_id in unresolved:
            classes += " open"
        else:
            group = " class='n-past'"
        parts.append(f"<g{group}>")
        parts.append(
            f"<rect class='{classes}' x='{x}' y='{y}' width='{node_w}' height='{node_h}' rx='5'/>"
            f"<title>{_e(_headline(repo, traj_id, state_id))}</title>"
            f"<text class='n-kind' x='{x + 10}' y='{y + 15}'>{_e(label)}</text>"
        )
        for index, line in enumerate(_wrap(_headline(repo, traj_id, state_id))):
            parts.append(
                f"<text class='n-text' x='{x + 10}' y='{y + 32 + index * 15}'>{_e(line)}</text>"
            )
        parts.append("</g>")
    parts.append("</svg>")
    return f"<div class='scroll'>{''.join(parts)}</div>"


STANDALONE_STYLE = """
  .n-box { fill:#ffffff; stroke:#d9d6d1; }
  .n-box.live { stroke:#1f6f4a; stroke-width:2; }
  .n-box.open { stroke:#8a5a00; stroke-width:2; }
  .n-text { fill:#1a1a1a; font:12px Georgia,serif; }
  .n-kind { fill:#6b6b6b; font:10px Menlo,monospace; letter-spacing:.08em; }
  .n-past .n-text { fill:#8d8983; }
  .e-line { stroke:#c9c5bf; fill:none; stroke-width:1.5; }
  .e-label { fill:#6b6b6b; font:10px Menlo,monospace; }
  @media (prefers-color-scheme: dark) {
    .n-box { fill:#1d1c1a; stroke:#3a3735; }
    .n-box.live { stroke:#6fc59a; }
    .n-box.open { stroke:#d5a04a; }
    .n-text { fill:#e8e6e3; }
    .n-kind, .e-label { fill:#9a9691; }
    .n-past .n-text { fill:#6a6560; }
    .e-line { stroke:#3a3735; }
  }
"""


def standalone_svg(repo: Repo, traj_id: str) -> str:
    """The drawing as a file that stands on its own.

    The page gets its colours from the document; a file has to carry its own,
    and has to read on a light background and a dark one, because it will be
    looked at in both and there is no telling which.
    """
    markup = graph(repo, traj_id)
    if "<svg" not in markup:
        raise errors.GrrpError("nothing recorded in this trajectory yet")
    inner = markup.split("<svg", 1)[1].rsplit("</svg>", 1)[0]
    attributes, body = inner.split(">", 1)
    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        f"<svg xmlns='http://www.w3.org/2000/svg'{attributes}>"
        f"<style>{STANDALONE_STYLE}</style>{body}</svg>\n"
    )


# --------------------------------------------------------------------------- #
# pages
# --------------------------------------------------------------------------- #


def _highlight(text: str, needle: str) -> str:
    """Show where a match landed, without ordering anything by it.

    (Worded to keep the token out of this file: ``grrp check`` greps the source
    for measure-shaped words, and the guard should stay strict on the page,
    which is where the temptation to introduce one is strongest.)
    """
    escaped = _e(text)
    if not needle:
        return escaped
    lowered, target = escaped.lower(), _e(needle).lower()
    at = lowered.find(target)
    if at < 0:
        return escaped
    return (
        escaped[:at] + "<mark>" + escaped[at : at + len(target)] + "</mark>"
        + escaped[at + len(target):]
    )


def sign_in(workspace: Workspace, token: str, message: str = "", back: str = "/") -> bytes:
    """The way in: a name and a password, standing in front of a keypair.

    What the password does and does not do is stated on the page rather than
    implied by the shape of it.  It controls who reaches this server through a
    browser.  It does not make anything true, and it is not what a reader
    elsewhere checks -- they check signatures, which are over keys this server
    never needed to see.
    """
    body = [
        "<header class='cover'><h1>Sign in</h1>"
        "<p class='lede'>Everything you record here is attributed to a key, and this is how "
        "you reach yours. The password guards access to this server. It is not what makes "
        "your work credible: that comes from other parties registering it, and it travels "
        "with the record to people who have no account here at all.</p></header>"
    ]
    if message:
        body.append(f"<div class='note'>{_e(message)}</div>")

    body.append(
        "<form method='post' action='/sign-in' class='signin'>"
        f"<input type='hidden' name='token' value='{_e(token)}'>"
        f"<input type='hidden' name='back' value='{_e(back)}'>"
        "<label>Name<input type='text' name='name' autocomplete='username' autofocus "
        "required></label>"
        "<label>Password<input type='password' name='password' "
        "autocomplete='current-password' required></label>"
        "<div class='row'><button type='submit'>sign in</button></div></form>"
    )

    body.append("<h2>New here</h2>")
    if accounts.REGISTRATION_OPEN:
        body.append(
            "<form method='post' action='/register'>"
            f"<input type='hidden' name='token' value='{_e(token)}'>"
            f"<input type='hidden' name='back' value='{_e(back)}'>"
            "<label>Name<input type='text' name='name' required></label>"
            "<label>Password<input type='password' name='password' "
            "autocomplete='new-password' required></label>"
            "<div class='row'><button type='submit'>make an account</button></div></form>"
        )
    else:
        body.append(
            "<div class='note'><strong>Registration is closed at the moment.</strong> "
            "Ask whoever runs this server; they add accounts with "
            "<span class='id'>grrp account add &lt;name&gt;</span>.<br><br>"
            "Not a queue and not an approval: an account is access to this particular "
            "server, and nothing here is a precondition for taking part. The record is "
            "plain files. Anyone can hold a copy, continue it under any implementation, "
            "and hand it back — with no account, and without asking.</div>"
        )

    body.append(
        "<div class='note'>Your account reaches a keypair; the keypair signs. Two people "
        "signed in here is the ordinary case rather than a trick: at group tier a "
        "transition must be registered by a party other than the one who performed it, so "
        "a second party is what makes an act attested. Private keys live in "
        f"<span class='id'>{_e(identity.RING_DIR)}/</span> beside the records, are never "
        "committed, and are never sent anywhere.</div>"
    )
    return _page("sign in — grrp", "".join(body))


def records_index(
    workspace: Workspace,
    token: str,
    message: str = "",
    query: str = "",
    who: identity.Identity | None = None,
) -> bytes:
    """The cover: everything on this machine, and the two ways in."""
    found = workspace.records()
    body = [
        "<header class='cover'><h1>Your records</h1>"
        "<p class='lede'>Each record is a directory of work with one or more questions in it. "
        "The record is plain files in your own filesystem — you can read it without this page, "
        "and take it anywhere without asking anyone.</p></header>"
    ]
    if message:
        body.append(f"<div class='note'>{_e(message)}</div>")

    body.append(
        "<form method='get' action='/' class='searchbar'>"
        f"<input type='text' name='q' value='{_e(query)}' "
        "placeholder='Search questions, positions, objections…' autofocus>"
        "<button type='submit'>search</button>"
        + (" <a class='clear' href='/'>clear</a>" if query else "")
        + "</form>"
    )

    if query:
        results = search(workspace, query)
        body.append(f"<h2>Matches for “{_e(query)}”</h2>")
        if not results:
            body.append("<div class='note'>Nothing here mentions that.</div>")
        for hit in results:
            body.append(
                f"<div class='card'>"
                f"<a href='/r/{_e(hit.record)}/t/{_e(hit.traj_id)}'>"
                f"<strong>{_highlight(hit.title, query)}</strong></a>"
                f"<div class='meta'>{_e(hit.record)} · matched in {_e(hit.where)}</div>"
                f"<div class='snippet'>{_highlight(hit.snippet, query)}</div></div>"
            )
        body.append(
            "<div class='note'>Search filters; it does not rank. Matches appear in the same "
            "order as everything else, because an ordering by relevance is a measure over "
            "trajectories, and a measure adopted to direct attention becomes the thing people "
            "work towards.</div>"
        )
        body.append("<h2>Everything</h2>")

    if not found:
        body.append(
            "<div class='note'>Nothing here yet. A record is a directory, and it works whether "
            "or not it is a git repository.</div>"
        )
    # Listed by name. Never by recency, size or anything else derived from the
    # work: that would be an ordering over trajectories, and it would quietly
    # tell you which of your questions matters.
    for name, repo in found:
        marks = [f"{repo.tier()} tier"]
        if (repo.root / ".git").is_dir():
            marks.append("git")
        if repo.charter():
            marks.append("charter")
        body.append(
            f"<div class='card'><a href='/r/{_e(name)}'><strong>{_e(name)}</strong></a>"
            f"<div class='meta'>{_e(' · '.join(marks))}</div>"
        )
        for traj_id in repo.trajectory_ids():
            data = repo.trajectory(traj_id)
            live = views.current_states(repo, traj_id)
            openings = views.open_items(repo, traj_id)
            body.append(
                f"<div class='traj'><a href='/r/{_e(name)}/t/{_e(traj_id)}'>"
                f"{_e(data.get('question'))}</a>"
            )
            for state_id in live:
                body.append(
                    f"<div class='meta'>→ {_e(_headline(repo, traj_id, state_id))}</div>"
                )
            if len(live) > 1:
                body.append("<div class='meta'>divergent — neither is the canonical one</div>")
            # The trajectory's own question is unresolved by design and is
            # printed above already, so repeating it here as "unanswered" is
            # noise. Everything else is shown in full: a cover that quietly
            # dropped some would read as though there were fewer.
            opening = views.opening_state(repo, traj_id)
            standing = [
                item for item in openings
                if item.transition.get("posterior_state") != opening
            ]
            for item in standing:
                body.append(
                    "<div class='meta open-mark'>unanswered: "
                    f"{_e(_headline(repo, traj_id, item.transition.get('posterior_state')))}"
                    "</div>"
                )
            body.append("</div>")
        body.append("</div>")

    body.append("<h2>Start a record</h2>")
    body.append(
        "<form method='post' action='/new-record'>"
        f"<input type='hidden' name='token' value='{_e(token)}'>"
        "<textarea name='question' placeholder='The question you are actually trying to answer' "
        "required></textarea>"
        "<div class='row'><input type='text' name='name' placeholder='a short name' required>"
        "<label class='meta'><input type='checkbox' name='git' checked> and a git repository"
        "</label><button type='submit'>open it</button></div>"
        "<div class='meta'>Write down what you are trying to find out, once, before the framing "
        "hardens and you forget you chose it. It stays open until something answers it.</div>"
        "</form>"
    )

    body.append("<h2>Continue someone's record</h2>")
    body.append(
        "<form method='post' action='/continue'>"
        f"<input type='hidden' name='token' value='{_e(token)}'>"
        "<div class='row'><input type='text' name='bundle' "
        "placeholder='path to a bundle they sent you — traj.zip' required>"
        "<button type='submit'>continue it</button></div>"
        "<div class='meta'>Someone hands you a file. What you record next references what you "
        "obtained as parents, so the two of you have one graph and not two. Nothing that arrives "
        "is altered, and anything that cannot be verified is kept and marked rather than "
        "discarded.</div></form>"
    )

    body.append(
        "<div class='note'>This lists records on this machine. There is no directory of other "
        "people's work here, and there is not going to be one: a service that knew where "
        "everyone's records were would be party to every entry, and what makes a record "
        "credible is registration by parties who did not coordinate. Work reaches you as a "
        "bundle somebody chose to give you.</div>"
    )
    return _page("grrp", "".join(body), who, token)


def index(
    repo: Repo,
    token: str = "",
    base: str = "",
    who: identity.Identity | None = None,
) -> bytes:
    """The trajectories of one record."""
    body = [f"<h1>{_e(repo.root.name)}</h1>"]
    traj_ids = repo.trajectory_ids()
    if not traj_ids:
        body.append("<p class=q>No trajectory open yet.</p>")
    for traj_id in traj_ids:
        trajectory_data = repo.trajectory(traj_id)
        live = views.current_states(repo, traj_id)
        body.append(
            f"<div class=card><a href='{_e(base)}/t/{_e(traj_id)}'><strong>"
            f"{_e(trajectory_data.get('title') or traj_id)}</strong></a>"
            f"<div class=meta>{_e(trajectory_data.get('question'))}</div>"
        )
        for state_id in live:
            body.append(f"<div class=meta>· {_e(_headline(repo, traj_id, state_id))}</div>")
        if len(live) > 1:
            body.append("<div class=meta>divergent — neither is the canonical one</div>")
        body.append("</div>")

    if token:
        body.append("<h2>Open another question</h2>")
        body.append(
            f"<form method=post action='{_e(base)}/new-trajectory'>"
            f"<input type=hidden name=token value='{_e(token)}'>"
            "<textarea name=question placeholder='What are you trying to find out?' required>"
            "</textarea>"
            "<div class=row><input type=text name=title placeholder='short title (optional)'>"
            "<button type=submit>open</button></div></form>"
        )
        body.append("<p><a href='/'>← all records</a></p>")
    return _page(repo.root.name, "".join(body), who, token)


ACTS = {
    "claim": "claim — state a position",
    "challenge": "challenge — object; it stands until something answers it",
    "transform": "transform — what it becomes",
    "decide": "decide — a decision, with its reason",
    "connect": "connect — relate it to something else",
    "verify": "verify — the outcome of a check",
    "release": "release — publish it, with the objections that stand",
}


#: Each button says what pressing it does, in the words someone would use for
#: the thing they are already doing. A select and two checkboxes made you
#: assemble the act out of parts before you could perform it.
BUTTONS = (
    ("claim", "Take a position", "what you currently think"),
    ("challenge", "Object to this", "it stands until something answers it"),
    ("transform", "Change it", "what it becomes, and what moved you"),
    ("decide", "Record a decision", "with the reason"),
    ("abandon", "Abandon this direction", "say what stopped it"),
    ("verify", "Record a check", "what you checked, and how it came out"),
    ("refute", "…that did not come out", "it joins what is unanswered"),
)


def _act_form(base: str, traj_id: str, token: str, state_id: str | None) -> str:
    buttons = "".join(
        f"<button type='submit' name='act' value='{key}' title='{_e(hint)}'>{_e(label)}</button>"
        for key, label, hint in BUTTONS
    )
    return (
        f"<form method='post' action='{_e(base)}/t/{_e(traj_id)}/act' class='act'>"
        f"<input type='hidden' name='token' value='{_e(token)}'>"
        f"<input type='hidden' name='state' value='{_e(state_id or '')}'>"
        "<textarea name='message' placeholder='What changed, and why?'></textarea>"
        f"<div class='row buttons'>{buttons}</div>"
        "<div class='row'>"
        "<input type='text' name='to' placeholder='a doi, a link, or another state'>"
        "<button type='submit' name='act' value='connect' class='quiet'>Connect to it</button>"
        "<button type='submit' name='act' value='release' class='quiet'>Publish this state</button>"
        "</div>"
        "<div class='meta'>Whatever you press is recorded as an act you performed. At the group "
        "tier it becomes a proposal until another party registers it. Publishing enumerates the "
        "objections standing against this state — which asserts that they stand, and nothing "
        "about whether they are right.</div></form>"
    )


def trajectory(
    repo: Repo,
    traj_id: str,
    token: str,
    message: str = "",
    base: str = "",
    who: identity.Identity | None = None,
) -> bytes:
    data = repo.trajectory(traj_id)
    body = [f"<h1>{_e(data.get('title') or traj_id)}</h1>"]
    body.append(f"<p class=q>{_e(data.get('question'))}</p>")
    if message:
        body.append(f"<div class=note>{_e(message)}</div>")

    body.append("<h2>The trajectory</h2>")
    body.append(graph(repo, traj_id))

    live = views.current_states(repo, traj_id)
    body.append("<h2>Live positions</h2>")
    if not live:
        body.append("<div class=note>No position taken yet.</div>")
    body.append("<div class=divergent>" if len(live) > 1 else "<div>")
    for state_id in live:
        body.append(
            f"<div class='card live'><div>{_e(_headline(repo, traj_id, state_id))}</div>"
            f"<div class=id>{_e(canonical.short(state_id))}</div>"
            f"{_act_form(base, traj_id, token, state_id)}</div>"
        )
    body.append("</div>")
    if len(live) > 1:
        body.append(
            "<div class=note>These diverged. Both are kept and neither is marked principal: "
            "in inquiry a fork is frequently the correct outcome, so plurality is the normal "
            "shape of a healthy record rather than an unfinished one. Nothing here combines "
            "them — a synthesis is an act someone performs, referencing both.</div>"
        )

    items = views.open_items(repo, traj_id)
    body.append("<h2>Unanswered</h2>")
    if not items:
        body.append("<div class=note>Nothing unresolved.</div>")
    for item in items:
        record = item.transition
        body.append(
            f"<div class='card open'>"
            f"<div>{_e(_headline(repo, traj_id, record.get('posterior_state')))}</div>"
            f"<div class=meta>{_e(record.get('act'))} · {_e(record.get('performed'))}</div>"
            f"<div class=id>{_e(canonical.short(record['id']))}</div></div>"
        )
    if items:
        body.append(
            "<div class=note>This is also the entry path: each of these is an identified state "
            "that someone holding no prior standing in your work could take up, and be judged "
            "on the act itself.</div>"
        )

    proposals = repo.proposals(traj_id)
    if proposals:
        body.append("<h2>Proposed, not yet registered</h2>")
        me = repo.party()
        for record in proposals:
            mine = record.get("performer") == me
            body.append(
                f"<div class=card>"
                f"<div>{_e(_headline(repo, traj_id, record.get('posterior_state')))}</div>"
                f"<div class=meta>{_e(record.get('act'))} · "
                + ("yours — waiting on another party" if mine else "waiting on you")
                + f"</div><div class=id>{_e(canonical.short(record['id']))}</div>"
            )
            if not mine:
                body.append(
                    f"<form method=post action='{_e(base)}/t/{_e(traj_id)}/register'>"
                    f"<input type=hidden name=token value='{_e(token)}'>"
                    f"<input type=hidden name=proposal value='{_e(record['id'])}'>"
                    "<div class=row><button class=quiet type=submit>register it</button>"
                    "<span class=meta>You assert that this party performed this act at this "
                    "time. Not that it is true, an improvement, or understood.</span>"
                    "</div></form>"
                )
            body.append("</div>")
        body.append(
            "<div class=note>Nothing proposed is in the log. A party cannot register their own "
            "act: credibility follows from registration by parties who did not coordinate, and "
            "from no property of the record itself.</div>"
        )

    restricted = []
    for record in repo.transitions(traj_id):
        if record.get("kind") == "operation":
            continue
        state = views.disclosure_of(repo, traj_id, record["id"])
        if state and state.get("grounds"):
            restricted.append((record, state))
    if restricted:
        body.append("<h2>Restricted</h2>")
        for record, state in restricted:
            schedule = state.get("release_at")
            when = f" · widens to {state.get('release_class')} on {schedule}" if schedule else ""
            body.append(
                f"<div class='card stop'><div class=id>{_e(canonical.short(record['id']))}</div>"
                f"<div class=meta>{_e(state['effective_class'])} · "
                f"{_e(', '.join(state['grounds']))}{_e(when)}</div>"
            )
            for name in state["grounds"]:
                body.append(
                    "<div class=meta>residue — still disclosable: "
                    f"{_e(vocab.GROUNDS[name]['residue'])}</div>"
                )
            body.append("</div>")
        body.append(
            "<div class=note>Every ground leaves a residue that must still be disclosed. That "
            "residue is the one question a reader can always ask: was what the ground leaves "
            "disclosable in fact disclosed? Disclosure may widen and never narrow, so there is "
            "no control here that takes anything back.</div>"
        )

    releases = repo.releases(traj_id)
    if releases:
        body.append("<h2>Released</h2>")
        for release in releases:
            body.append(
                f"<div class=card><div>"
                f"{_e(_headline(repo, traj_id, release.get('state')))}</div>"
                f"<div class=meta>{_e(release.get('time', '')[:10])} · "
                f"grrp export {_e(canonical.short(release['id']))} -o paper.md</div></div>"
            )

    body.append("<h2>Lineage</h2>")
    for record in repo.transitions(traj_id):
        if record.get("kind") == "operation":
            payload = record.get("payload") or {}
            body.append(
                f"<div class=card><div class=meta>[{_e(record.get('operation'))}] "
                f"{_e(payload.get('ground') or payload.get('class') or '')}</div>"
                f"<div class=id>{_e(canonical.short(record['id']))}</div></div>"
            )
            continue
        registration = record.get("registration") or {}
        mark = "attested" if registration.get("attested") else "unattested"
        body.append(
            f"<div class=card>"
            f"<div>{_e(_headline(repo, traj_id, record.get('posterior_state')))}</div>"
            f"<div class=meta>{_e(record.get('act'))} · {_e(record.get('disposition'))} · "
            f"{_e(mark)} · {_e(record.get('performed'))}</div>"
            f"<div class=id>{_e(canonical.short(record['id']))}</div></div>"
        )

    if not views.has_attestation(repo, traj_id):
        body.append(
            "<div class='note warn'>Unattested throughout. Every transition here was registered "
            "by the party who performed it, which is useful to you and is evidence to nobody. "
            "Credibility begins where a second party registers.</div>"
        )

    body.append(f"<p><a href='{_e(base) or '/'}'>← trajectories</a></p>")
    return _page(data.get("title") or traj_id, "".join(body), who, token)


# --------------------------------------------------------------------------- #
# acting
# --------------------------------------------------------------------------- #


def _perform(repo: Repo, traj_id: str, fields: dict[str, list[str]]) -> str:
    """Record an act. The same writer the command line uses."""
    act = (fields.get("act") or ["claim"])[0]
    text = (fields.get("message") or [""])[0].strip()
    state_ref = (fields.get("state") or [""])[0]
    target_ref = (fields.get("to") or [""])[0].strip()
    if fields.get("abandon") and act == "decide":   # older forms
        act = "abandon"
    if fields.get("failed") and act == "verify":
        act = "refute"
    if act not in actions.SHAPES:
        return f"{act!r} is not an act."

    prior = state_ref or None
    if prior:
        traj_id, prior = repo.resolve_state(traj_id, prior)
    else:
        live = views.current_states(repo, traj_id)
        if len(live) == 1:
            prior = live[0]
        elif not live:
            prior = views.opening_state(repo, traj_id)
        else:
            return (
                "Several positions are live and none is the canonical one. "
                "Record against the one you mean."
            )
    if not prior:
        return "There is no identified state to attach this to."

    if act == "release":
        return _release(repo, traj_id, prior)
    if not text:
        return "Nothing recorded: the message was empty."

    name, target, relation, disposition = actions.SHAPES[act]
    artefacts = []
    parents = actions.parents_for(repo, traj_id, prior)
    if act == "connect":
        if not target_ref:
            return "A connection needs something to connect to: a state, or doi:… / https://…"
        try:
            other_traj, other_state = repo.resolve_state(None, target_ref)
            artefacts.append(store.external_reference(other_state))
            parents += [
                r["id"] for r in repo.transitions(other_traj)
                if r.get("posterior_state") == other_state and r["id"] not in parents
            ]
        except (errors.UnknownReference, errors.AmbiguousReference):
            artefacts.append(store.external_reference(target_ref))

    state_id, _ = repo.write_state(traj_id, text)
    record = store.new_transition(
        trajectory=traj_id,
        act=name,
        performer=repo.party(),
        parents=parents,
        prior_state=prior,
        posterior_state=state_id,
        target=target,
        relation=vocab.RELATIONS[relation] if relation else None,
        trigger="objection" if name == "challenge" else "self",
        disposition=disposition,
        artefacts=artefacts,
    )
    result = actions.submit(repo, traj_id, record)
    gitutil.commit_paths(repo.root, result.paths, f"grrp: {name} {canonical.short(record['id'])}")
    if result.proposed:
        return (
            f"Proposed {canonical.short(record['id'])}. It is not in the log until another "
            f"party registers it: grrp register {canonical.short(record['id'])}"
        )
    return f"Recorded {canonical.short(record['id'])}. Unattested: you registered your own act."


def _release(repo: Repo, traj_id: str, state_id: str) -> str:
    standing = views.standing_objections(repo, traj_id, state_id)
    record = store.new_transition(
        trajectory=traj_id,
        act="release",
        performer=repo.party(),
        parents=actions.parents_for(repo, traj_id, state_id),
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
        "class": None,
        "standing_objections": [
            {"id": o["id"], "state": o.get("posterior_state"), "performed": o.get("performed")}
            for o in standing
        ],
    }
    path = repo.releases_dir(traj_id) / f"{record['id'].split(':')[-1]}.yaml"
    store.write_yaml(path, release_record)
    result = actions.submit(repo, traj_id, record, extra=[path])
    gitutil.commit_paths(repo.root, result.paths, f"grrp: release {canonical.short(record['id'])}")

    said = "Proposed" if result.proposed else "Released"
    if standing:
        objections = ", ".join(canonical.short(o["id"]) for o in standing)
        return (
            f"{said} {canonical.short(record['id'])}, enumerating the objections that stand "
            f"against it: {objections}. That asserts they stand, and nothing about their merit."
        )
    return f"{said} {canonical.short(record['id'])}. No objections stood against it."


# --------------------------------------------------------------------------- #
# serving
# --------------------------------------------------------------------------- #


COOKIE = "grrp_session"


class Sessions:
    """Who is signed in, in memory, for as long as the server runs.

    In memory and not on disk, deliberately: a session log is a record of who
    was here and when, which is precisely the kind of monitoring by-product the
    event plane is gitignored to avoid. Restarting the server signs everybody
    out, which is the correct trade.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._open: dict[str, str] = {}

    def begin(self, name: str) -> str:
        ticket = secrets.token_urlsafe(24)
        with self._lock:
            self._open[ticket] = name
        return ticket

    def name_for(self, ticket: str) -> str | None:
        with self._lock:
            return self._open.get(ticket)

    def end(self, ticket: str) -> None:
        with self._lock:
            self._open.pop(ticket, None)


def _cookie(ticket: str) -> str:
    """Hold the session ticket, and nothing else.

    Never the name, never the key: the cookie is an opaque reference to a
    session this process is holding, so a stolen one dies when the server
    restarts and reveals nothing on its own. An empty ticket clears it.
    """
    if not ticket:
        return f"{COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"
    return f"{COOKIE}={ticket}; Path=/; HttpOnly; SameSite=Strict"


def make_handler(target: Workspace | Repo, token: str, sessions: Sessions | None = None):
    workspace = _as_workspace(target)
    sessions = sessions if sessions is not None else Sessions()

    class Handler(BaseHTTPRequestHandler):
        server_version = "grrp"

        def log_message(self, *args) -> None:  # noqa: D102 - keep the console quiet
            return

        def _send(self, payload: bytes, status: int = 200, cookie: str = "") -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Referrer-Policy", "no-referrer")
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(payload)

        def _redirect(self, where: str, said: str = "", cookie: str = "") -> None:
            self.send_response(303)
            self.send_header("Location", f"{where}?said={quote(said)}" if said else where)
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()

        def _who(self) -> identity.Identity | None:
            """Which key this browser is signing as, if it still exists.

            Verified against the keyring on every request rather than trusted
            from the cookie: a name in a cookie is a claim, and the record must
            not attribute an act to a key that is not there.
            """
            jar = http.cookies.SimpleCookie(self.headers.get("Cookie") or "")
            morsel = jar.get(COOKIE)
            name = sessions.name_for(morsel.value) if morsel and morsel.value else None
            if not name:
                return None
            try:
                return identity.find(workspace.root, name)
            except errors.GrrpError:
                return None

        def _resolve(self, parts: list[str], who: identity.Identity | None = None) -> tuple[Repo, str]:
            """(repo, base) from a path, with '/t/...' meaning the root record."""
            if len(parts) > 1 and parts[0] == "r":
                repo, base = workspace.find(parts[1]), f"/r/{parts[1]}"
            else:
                primary = workspace.primary()
                if not primary:
                    raise errors.NotARepository("no record here")
                repo, base = primary, ""
            if who is not None:
                repo = Repo(repo.root, acting_as=who.name)
            return repo, base

        def do_GET(self) -> None:  # noqa: N802
            url = urlparse(self.path)
            parts = [p for p in url.path.split("/") if p]
            said = (parse_qs(url.query).get("said") or [""])[0]
            who = self._who()
            try:
                if parts == ["sign-in"]:
                    back = (parse_qs(url.query).get("back") or ["/"])[0]
                    self._send(sign_in(workspace, token, said, back))
                    return
                if who is None:
                    # Before anything is attributed to a key, say which key.
                    self._redirect(f"/sign-in?back={quote(self.path)}")
                    return
                if not parts:
                    query = (parse_qs(url.query).get("q") or [""])[0]
                    self._send(records_index(workspace, token, said, query, who))
                    return
                repo, base = self._resolve(parts, who)
                rest = parts[2:] if base else parts
                if not rest:
                    self._send(index(repo, token, base, who))
                elif rest[0] == "t" and len(rest) > 1:
                    traj_id = repo.resolve_trajectory(rest[1])
                    self._send(trajectory(repo, traj_id, token, said, base, who))
                else:
                    self._send(_page("not found", "<h1>Not found</h1>", who, token), 404)
            except errors.GrrpError as error:
                self._send(
                    _page("grrp", f"<h1>Refused</h1><p class=q>{_e(error)}</p>", who, token), 400
                )

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            fields = parse_qs(self.rfile.read(length).decode("utf-8"))
            if (fields.get("token") or [""])[0] != token:
                self._send(_page("grrp", "<h1>Refused</h1><p class=q>stale page</p>"), 403)
                return

            parts = [p for p in urlparse(self.path).path.split("/") if p]
            who = self._who()
            try:
                if parts in (["sign-in"], ["register"]):
                    name = (fields.get("name") or [""])[0].strip().lower()
                    password = (fields.get("password") or [""])[0]
                    back = (fields.get("back") or ["/"])[0] or "/"
                    said = ""
                    if parts == ["register"]:
                        if not accounts.REGISTRATION_OPEN:
                            self._redirect("/sign-in", "Registration is closed here.")
                            return
                        account = accounts.create(workspace.root, name, password)
                        said = (
                            f"{account.name} has an account and a keypair. The private half "
                            f"is in {identity.RING_DIR}/ and is never sent anywhere; lose it "
                            "and you cannot sign as this party again."
                        )
                    else:
                        account = accounts.authenticate(workspace.root, name, password)
                    self._redirect(back, said, cookie=_cookie(sessions.begin(account.name)))
                    return

                if parts == ["sign-out"]:
                    jar = http.cookies.SimpleCookie(self.headers.get("Cookie") or "")
                    morsel = jar.get(COOKIE)
                    if morsel and morsel.value:
                        sessions.end(morsel.value)
                    self._redirect("/sign-in", "", cookie=_cookie(""))
                    return

                if who is None:
                    self._redirect(f"/sign-in?back={quote(self.path)}")
                    return

                if parts == ["continue"]:
                    source = Path((fields.get("bundle") or [""])[0].strip().strip('"'))
                    if not source.is_file():
                        self._redirect("/", f"No bundle at {source}.")
                        return
                    manifest = bundle_module().read_manifest(source)
                    if manifest.get("protocol") != store.PROTOCOL:
                        self._redirect(
                            "/",
                            f"That bundle is {manifest.get('protocol')!r} and this is "
                            f"{store.PROTOCOL!r}. Records are not read as though they were of "
                            "a version they are not.",
                        )
                        return
                    target = workspace.primary() or workspace.find(
                        (manifest.get("trajectories") or ["record"])[0]
                    )
                    receipt = bundle_module().apply(target, source)
                    self._redirect(
                        "/",
                        "Continued "
                        + ", ".join(receipt.trajectories)
                        + ". What you record next references what arrived as parents."
                        + (
                            " Some of it could not be verified here and is kept and marked."
                            if receipt.unverified
                            else ""
                        ),
                    )
                    return

                if parts == ["new-record"]:
                    name = (fields.get("name") or [""])[0].strip()
                    question = (fields.get("question") or [""])[0].strip()
                    if not name or not question:
                        self._redirect("/", "A record needs a name and a question.")
                        return
                    repo, traj_id = actions.create_record(
                        workspace.root, name, question, use_git=bool(fields.get("git"))
                    )
                    identity.found(workspace.root, repo, who.name)
                    self._redirect(f"/r/{repo.root.name}/t/{traj_id}", "Opened.")
                    return

                repo, base = self._resolve(parts, who)
                identity.adopt(workspace.root, repo, who.name)
                rest = parts[2:] if base else parts

                if rest and rest[0] == "new-trajectory":
                    question = (fields.get("question") or [""])[0].strip()
                    title = (fields.get("title") or [""])[0].strip() or None
                    traj_id, paths = actions.open_trajectory(repo, question, title)
                    gitutil.commit_paths(repo.root, paths, f"grrp: open {traj_id}")
                    self._redirect(f"{base}/t/{traj_id}", "Opened.")
                    return

                traj_id = repo.resolve_trajectory(rest[1])
                if rest[2] == "register":
                    _, proposal = repo.resolve_proposal(traj_id, (fields.get("proposal") or [""])[0])
                    record = actions.register_proposal(repo, traj_id, proposal)
                    said = (
                        f"Registered {canonical.short(record['id'])}. It is attested: you and "
                        "the performer are different parties."
                    )
                else:
                    said = _perform(repo, traj_id, fields)
                self._redirect(f"{base}/t/{traj_id}", said)
            except errors.GrrpError as error:
                if parts in (["sign-in"], ["register"]):
                    self._redirect("/sign-in", str(error))
                else:
                    self._redirect(self.path.rsplit("/", 1)[0] or "/", str(error))

    return Handler


def serve(
    target: Workspace | Repo,
    host: str = "127.0.0.1",
    port: int = 7373,
    open_browser: bool = True,
) -> None:
    token = secrets.token_urlsafe(16)
    server = ThreadingHTTPServer((host, port), make_handler(target, token))
    url = f"http://{host}:{server.server_port}/"
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
