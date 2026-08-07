"""A local page for reading and adding to a record.

This is **Level 3**: an application over the record, outside conformance. The
protocol is implementable with none of it, every operation it offers is
available from the command line, and nothing in the record depends on it. If
this file were deleted the record would be unaffected.

It binds to the loopback interface only. There is no account, no session, no
telemetry, and nothing leaves the machine. The one concession to being a page
in a browser is a per-run token in every form, so that another page you happen
to have open cannot post to it.

What it deliberately does not do, because the design forbids it and a screen is
where the temptation is strongest:

    no quantity over participants or trajectories -- no counts to compare, no
    progress bars, no health, no activity;
    no ordering of branches, and no branch marked principal, default or current;
    no merge, and not the word;
    no button that narrows disclosure.
"""

from __future__ import annotations

import html
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import canonical, errors, store, views, vocab
from .store import Repo

STYLE = """
:root { --bg:#fbfbfa; --fg:#1a1a1a; --dim:#6b6b6b; --line:#e2e0dc; --card:#fff;
        --live:#1f6f4a; --open:#8a5a00; --stop:#8a2020; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#161514; --fg:#e8e6e3; --dim:#9a9691; --line:#2f2d2b; --card:#1d1c1a;
          --live:#6fc59a; --open:#d5a04a; --stop:#d98080; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.55 ui-serif,Georgia,serif; }
main { max-width:52rem; margin:0 auto; padding:2rem 1.25rem 5rem; }
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
textarea { width:100%; min-height:5.5rem; font:inherit; padding:.6rem; border-radius:5px;
           border:1px solid var(--line); background:var(--bg); color:var(--fg); }
select,input[type=text] { font:inherit; padding:.35rem; border-radius:5px;
           border:1px solid var(--line); background:var(--bg); color:var(--fg); }
button { font:inherit; padding:.4rem 1rem; border-radius:5px; border:1px solid var(--line);
         background:var(--fg); color:var(--bg); cursor:pointer; }
.row { display:flex; gap:.6rem; align-items:center; flex-wrap:wrap; margin-top:.5rem; }
.warn { color:var(--stop); }
.divergent { display:grid; grid-template-columns:repeat(auto-fit,minmax(15rem,1fr)); gap:.6rem; }
footer { margin-top:4rem; padding-top:1rem; border-top:1px solid var(--line);
         font-size:.8rem; color:var(--dim); }
"""


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
        ground = (removal.get("payload") or {}).get("ground")
        return f"(redacted on the ground of {ground})"
    return "(content not held here)"


def index(repo: Repo) -> bytes:
    body = ["<h1>Your trajectories</h1>"]
    traj_ids = repo.trajectory_ids()
    if not traj_ids:
        body.append(
            "<p class=q>Nothing recorded yet. Open one from a terminal:<br>"
            "<span class=id>grrp new \"the question you are actually working on\"</span></p>"
        )
    # Listed, never ordered by anything and never counted: no quantity over
    # trajectories is computed, stored, displayed or exported.
    for traj_id in traj_ids:
        trajectory = repo.trajectory(traj_id)
        live = views.current_states(repo, traj_id)
        body.append(
            f"<div class=card><a href='/t/{_e(traj_id)}'><strong>"
            f"{_e(trajectory.get('title') or traj_id)}</strong></a>"
            f"<div class=meta>{_e(trajectory.get('question'))}</div>"
        )
        for state_id in live:
            body.append(f"<div class=meta>· {_e(_headline(repo, traj_id, state_id))}</div>")
        if len(live) > 1:
            body.append("<div class=meta>divergent — neither is the canonical one</div>")
        body.append("</div>")
    return _page("grrp", "".join(body))


def _act_form(traj_id: str, token: str, state_id: str | None) -> str:
    prompts = {
        "claim": "state a position",
        "challenge": "object to this state — it will stand until something answers it",
        "transform": "what it becomes",
        "decide": "a decision, with its reason — the act reuse depends on",
        "connect": "relate this to something else",
        "verify": "the outcome of a check",
    }
    options = "".join(
        f"<option value='{k}'>{_e(k)} — {_e(v)}</option>" for k, v in prompts.items()
    )
    return (
        f"<form method=post action='/t/{_e(traj_id)}/act'>"
        f"<input type=hidden name=token value='{_e(token)}'>"
        f"<input type=hidden name=state value='{_e(state_id or '')}'>"
        "<textarea name=message placeholder='What changed, and why?' required></textarea>"
        f"<div class=row><select name=act>{options}</select>"
        "<label class=meta><input type=checkbox name=abandon> abandon this direction</label>"
        "<button type=submit>record</button></div>"
        "<div class=meta>Recorded as an act you performed. At the group tier it becomes a "
        "proposal until another party registers it.</div>"
        "</form>"
    )


def trajectory(repo: Repo, traj_id: str, token: str, message: str = "") -> bytes:
    data = repo.trajectory(traj_id)
    body = [f"<h1>{_e(data.get('title') or traj_id)}</h1>"]
    body.append(f"<p class=q>{_e(data.get('question'))}</p>")
    if message:
        body.append(f"<div class=note>{_e(message)}</div>")

    live = views.current_states(repo, traj_id)
    body.append("<h2>Live positions</h2>")
    if not live:
        body.append("<div class=note>No position taken yet.</div>")
    body.append("<div class=divergent>" if len(live) > 1 else "<div>")
    for state_id in live:
        body.append(
            f"<div class='card live'><div>{_e(_headline(repo, traj_id, state_id))}</div>"
            f"<div class=id>{_e(canonical.short(state_id))}</div>"
            f"{_act_form(traj_id, token, state_id)}</div>"
        )
    body.append("</div>")
    if len(live) > 1:
        body.append(
            "<div class=note>These diverged. Both are kept and neither is marked principal: "
            "in inquiry a fork is frequently the correct outcome, so plurality is the normal "
            "shape of a healthy record rather than an unfinished one. Nothing here combines "
            "them — a synthesis is an act someone performs.</div>"
        )

    items = views.open_items(repo, traj_id)
    body.append("<h2>Unanswered</h2>")
    if not items:
        body.append("<div class=note>Nothing unresolved.</div>")
    for item in items:
        record = item.transition
        body.append(
            f"<div class='card open'><div>{_e(_headline(repo, traj_id, record.get('posterior_state')))}</div>"
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
            who = "yours — waiting on another party" if record.get("performer") == me else "waiting on you"
            body.append(
                f"<div class='card'><div>{_e(_headline(repo, traj_id, record.get('posterior_state')))}</div>"
                f"<div class=meta>{_e(record.get('act'))} · {_e(who)}</div>"
                f"<div class=id>{_e(canonical.short(record['id']))}</div></div>"
            )
        body.append(
            "<div class=note>Nothing proposed is in the log. A party cannot register their own "
            "act: credibility follows from registration by parties who did not coordinate, and "
            "from no property of the record itself. Register from a terminal: "
            "<span class=id>grrp register &lt;id&gt;</span></div>"
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
            grounds = ", ".join(state["grounds"])
            schedule = state.get("release_at")
            when = f" · widens to {state.get('release_class')} on {schedule}" if schedule else ""
            body.append(
                f"<div class='card stop'><div class=id>{_e(canonical.short(record['id']))}</div>"
                f"<div class=meta>{_e(state['effective_class'])} · {_e(grounds)}{_e(when)}</div>"
            )
            for name in state["grounds"]:
                body.append(
                    f"<div class=meta>residue — still disclosable: "
                    f"{_e(vocab.GROUNDS[name]['residue'])}</div>"
                )
            body.append("</div>")
        body.append(
            "<div class=note>Every ground leaves a residue that must still be disclosed. That "
            "residue is the one question a reader can always ask: was what the ground leaves "
            "disclosable in fact disclosed? Disclosure may widen and never narrow, so there is "
            "no control here that takes anything back.</div>"
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
            f"<div class=card><div>{_e(_headline(repo, traj_id, record.get('posterior_state')))}</div>"
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

    body.append("<p><a href='/'>← all trajectories</a></p>")
    return _page(data.get("title") or traj_id, "".join(body))


def _perform(repo: Repo, traj_id: str, fields: dict[str, list[str]]) -> str:
    """Record an act. The same code paths the command line uses."""
    act = (fields.get("act") or ["claim"])[0]
    text = (fields.get("message") or [""])[0].strip()
    state_ref = (fields.get("state") or [""])[0]
    abandon = bool(fields.get("abandon"))
    if not text:
        return "Nothing recorded: the message was empty."

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

    state_id, _ = repo.write_state(traj_id, text)
    shape = {
        "claim": ("claim", "hypothesis", None, "accepted"),
        "challenge": ("challenge", "assumption", vocab.RELATIONS["disagrees"], "unresolved"),
        "transform": ("transformation", "hypothesis", vocab.RELATIONS["modifies"], "accepted"),
        "decide": ("decision", "path", vocab.RELATIONS["retracts" if abandon else "extends"], "accepted"),
        "connect": ("connection", "artefact", vocab.RELATIONS["relates"], "accepted"),
        "verify": ("verification", "hypothesis", vocab.RELATIONS["confirms"], "accepted"),
    }[act]

    record = store.new_transition(
        trajectory=traj_id,
        act=shape[0],
        performer=repo.party(),
        parents=[
            r["id"] for r in repo.transitions(traj_id) if r.get("posterior_state") == prior
        ][-1:],
        prior_state=prior,
        posterior_state=state_id,
        target=shape[1],
        relation=shape[2],
        trigger="self",
        disposition=shape[3],
    )
    if repo.tier() == "personal":
        repo.append_transition(traj_id, record)
        return f"Recorded {canonical.short(record['id'])}. Unattested: you registered your own act."
    record = dict(record)
    record["registration"] = None
    repo.write_proposal(traj_id, record)
    return (
        f"Proposed {canonical.short(record['id'])}. It is not in the log until another party "
        f"registers it: grrp register {canonical.short(record['id'])}"
    )


def make_handler(repo: Repo, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "grrp"

        def log_message(self, *args) -> None:  # noqa: D102 - silence the console
            return

        def _send(self, payload: bytes, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            query = parse_qs(urlparse(self.path).query)
            try:
                if path == "/":
                    self._send(index(repo))
                elif path.startswith("/t/"):
                    traj_id = repo.resolve_trajectory(path.split("/")[2])
                    said = (query.get("said") or [""])[0]
                    self._send(trajectory(repo, traj_id, token, said))
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
            path = urlparse(self.path).path
            traj_id = repo.resolve_trajectory(path.split("/")[2])
            try:
                said = _perform(repo, traj_id, fields)
            except errors.GrrpError as error:
                said = str(error)
            self.send_response(303)
            self.send_header("Location", f"/t/{traj_id}?said={said.replace(' ', '%20')}")
            self.end_headers()

    return Handler


def serve(repo: Repo, host: str = "127.0.0.1", port: int = 7373, open_browser: bool = True) -> None:
    token = secrets.token_urlsafe(16)
    server = ThreadingHTTPServer((host, port), make_handler(repo, token))
    url = f"http://{host}:{server.server_port}/"
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
