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
import secrets
import threading
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from . import actions, canonical, errors, gitutil, store, views, vocab
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


def _as_workspace(target: Workspace | Repo) -> Workspace:
    return target if isinstance(target, Workspace) else Workspace(target.root)


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #


def _e(text: object) -> str:
    return html.escape(str(text if text is not None else ""))


def _page(title: str, body: str) -> bytes:
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{_e(title)}</title><style>{STYLE}</style></head>"
        f"<body><main>{body}"
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


def records_index(workspace: Workspace, token: str, message: str = "") -> bytes:
    body = ["<h1>Records</h1>"]
    if message:
        body.append(f"<div class=note>{_e(message)}</div>")
    found = workspace.records()
    if not found:
        body.append(
            "<p class=q>Nothing here yet. A record is a directory, and it works whether or "
            "not it is a git repository.</p>"
        )
    # Listed, never ordered by anything and never counted.
    for name, repo in found:
        trajectories = repo.trajectory_ids()
        body.append(
            f"<div class=card><a href='/r/{_e(name)}'><strong>{_e(name)}</strong></a>"
            f"<div class=meta>{_e(repo.tier())} tier"
            + (" · git" if (repo.root / '.git').is_dir() else "")
            + "</div>"
        )
        for traj_id in trajectories:
            body.append(
                f"<div class=meta>· {_e(repo.trajectory(traj_id).get('question'))}</div>"
            )
        body.append("</div>")

    body.append("<h2>Start a record</h2>")
    body.append(
        f"<form method=post action='/new-record'>"
        f"<input type=hidden name=token value='{_e(token)}'>"
        "<div class=row><input type=text name=name placeholder='a short name' required>"
        "<label class=meta><input type=checkbox name=git checked> make it a git repository"
        "</label></div>"
        "<textarea name=question placeholder='The question you are actually trying to answer' "
        "required></textarea>"
        "<div class=row><button type=submit>open it</button></div>"
        "<div class=meta>Write down what you are trying to find out, once, before the framing "
        "hardens and you forget you chose it. It becomes the question the record is about, and "
        "it stays open until something answers it.</div></form>"
    )
    return _page("grrp", "".join(body))


def index(repo: Repo, token: str = "", base: str = "") -> bytes:
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
    return _page(repo.root.name, "".join(body))


ACTS = {
    "claim": "claim — state a position",
    "challenge": "challenge — object; it stands until something answers it",
    "transform": "transform — what it becomes",
    "decide": "decide — a decision, with its reason",
    "connect": "connect — relate it to something else",
    "verify": "verify — the outcome of a check",
    "release": "release — publish it, with the objections that stand",
}


def _act_form(base: str, traj_id: str, token: str, state_id: str | None) -> str:
    options = "".join(f"<option value='{k}'>{_e(v)}</option>" for k, v in ACTS.items())
    return (
        f"<form method=post action='{_e(base)}/t/{_e(traj_id)}/act'>"
        f"<input type=hidden name=token value='{_e(token)}'>"
        f"<input type=hidden name=state value='{_e(state_id or '')}'>"
        "<textarea name=message placeholder='What changed, and why?'></textarea>"
        f"<div class=row><select name=act>{options}</select>"
        "<input type=text name=to placeholder='connect to: doi:… or a state'>"
        "</div><div class=row>"
        "<label class=meta><input type=checkbox name=abandon> abandon this direction</label>"
        "<label class=meta><input type=checkbox name=failed> the check failed</label>"
        "<button type=submit>record</button></div>"
        "<div class=meta>Recorded as an act you performed. At the group tier it becomes a "
        "proposal until another party registers it.</div></form>"
    )


def trajectory(repo: Repo, traj_id: str, token: str, message: str = "", base: str = "") -> bytes:
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
    return _page(data.get("title") or traj_id, "".join(body))


# --------------------------------------------------------------------------- #
# acting
# --------------------------------------------------------------------------- #


def _perform(repo: Repo, traj_id: str, fields: dict[str, list[str]]) -> str:
    """Record an act. The same writer the command line uses."""
    act = (fields.get("act") or ["claim"])[0]
    text = (fields.get("message") or [""])[0].strip()
    state_ref = (fields.get("state") or [""])[0]
    target_ref = (fields.get("to") or [""])[0].strip()
    if (fields.get("abandon") and act == "decide"):
        act = "abandon"
    if (fields.get("failed") and act == "verify"):
        act = "refute"

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


def make_handler(target: Workspace | Repo, token: str):
    workspace = _as_workspace(target)

    class Handler(BaseHTTPRequestHandler):
        server_version = "grrp"

        def log_message(self, *args) -> None:  # noqa: D102 - keep the console quiet
            return

        def _send(self, payload: bytes, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(payload)

        def _redirect(self, where: str, said: str = "") -> None:
            self.send_response(303)
            self.send_header("Location", f"{where}?said={quote(said)}" if said else where)
            self.end_headers()

        def _resolve(self, parts: list[str]) -> tuple[Repo, str]:
            """(repo, base) from a path, with '/t/...' meaning the root record."""
            if len(parts) > 1 and parts[0] == "r":
                return workspace.find(parts[1]), f"/r/{parts[1]}"
            primary = workspace.primary()
            if not primary:
                raise errors.NotARepository("no record here")
            return primary, ""

        def do_GET(self) -> None:  # noqa: N802
            url = urlparse(self.path)
            parts = [p for p in url.path.split("/") if p]
            said = (parse_qs(url.query).get("said") or [""])[0]
            try:
                if not parts:
                    primary = workspace.primary()
                    if primary and len(workspace.records()) == 1:
                        self._send(index(primary, token, ""))
                    else:
                        self._send(records_index(workspace, token, said))
                    return
                repo, base = self._resolve(parts)
                rest = parts[2:] if base else parts
                if not rest:
                    self._send(index(repo, token, base))
                elif rest[0] == "t" and len(rest) > 1:
                    traj_id = repo.resolve_trajectory(rest[1])
                    self._send(trajectory(repo, traj_id, token, said, base))
                else:
                    self._send(_page("not found", "<h1>Not found</h1>"), 404)
            except errors.GrrpError as error:
                self._send(_page("grrp", f"<h1>Refused</h1><p class=q>{_e(error)}</p>"), 400)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            fields = parse_qs(self.rfile.read(length).decode("utf-8"))
            if (fields.get("token") or [""])[0] != token:
                self._send(_page("grrp", "<h1>Refused</h1><p class=q>stale page</p>"), 403)
                return

            parts = [p for p in urlparse(self.path).path.split("/") if p]
            try:
                if parts == ["new-record"]:
                    name = (fields.get("name") or [""])[0].strip()
                    question = (fields.get("question") or [""])[0].strip()
                    if not name or not question:
                        self._redirect("/", "A record needs a name and a question.")
                        return
                    repo, traj_id = actions.create_record(
                        workspace.root, name, question, use_git=bool(fields.get("git"))
                    )
                    self._redirect(f"/r/{repo.root.name}/t/{traj_id}", "Opened.")
                    return

                repo, base = self._resolve(parts)
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
