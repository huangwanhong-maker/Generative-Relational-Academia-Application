"""Emission of a citable document from a release.

This is what makes the tool worth adopting by someone who is not persuaded of
anything.  A researcher who has been recording as they work gets, with no extra
effort, the paper-shaped object their institution already accepts — carrying an
appendix no other process can produce: the chain of transitions that led to the
released state, the parties attributed to specific changes, the content
absorbed from elsewhere, and the objections standing unresolved at the moment
of release.

Nothing here asks anybody to stop publishing.
"""

from __future__ import annotations

from . import canonical, views
from .store import Repo


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _describe(record: dict) -> str:
    bits = [record.get("act", "?")]
    if record.get("target"):
        bits.append(f"of {_article(record['target'])} {record['target']}")
    if record.get("relation"):
        bits.append(f"({record['relation']})")
    if record.get("trigger") and record["trigger"] != "self":
        bits.append(f"— occasioned by {record['trigger']}")
    return " ".join(bits)


def render_release(repo: Repo, traj_id: str, release: dict) -> str:
    trajectory = repo.trajectory(traj_id)
    state_id = release["state"]
    content = repo.read_state(traj_id, state_id)
    chain = views.chain_to_state(repo, traj_id, state_id)

    lines: list[str] = []
    lines.append(f"# {trajectory.get('title') or traj_id}")
    lines.append("")
    if trajectory.get("question"):
        lines.append(f"**Question.** {trajectory['question']}")
        lines.append("")
    lines.append(
        f"Released {release['time']} · release `{canonical.short(release['id'])}` · "
        f"state `{canonical.short(state_id)}` · protocol `{release.get('protocol')}`"
    )
    lines.append("")

    if not release.get("attested", False):
        lines.append(
            "> **Unattested.** Every transition in this record was registered by the "
            "party who performed it. A record registered by one party alone carries "
            "utility to its author and no evidential weight, and this document does "
            "not claim otherwise."
        )
        lines.append("")

    lines.append("## Released state")
    lines.append("")
    if content:
        lines.append(content.rstrip())
    else:
        removal = views.redactions(repo, traj_id).get(state_id)
        lines.append(
            f"*(content redacted on the ground of {removal.get('ground')}; the transition, "
            "its position in the graph and the record of the removal remain)*"
            if removal else "*(content not available)*"
        )
    lines.append("")

    lines.append("## Objections standing at release")
    lines.append("")
    standing = release.get("standing_objections") or []
    if not standing:
        lines.append("None recorded at the time of release.")
    else:
        lines.append(
            "These objections were unresolved when this state was released. "
            "Their enumeration asserts that they stand; it asserts nothing about "
            "their merit, and the release is not a certification."
        )
        lines.append("")
        for objection in standing:
            text = repo.read_state(traj_id, objection.get("state") or "")
            summary = (text or "").strip().splitlines()
            headline = summary[0] if summary else "*(content not available)*"
            lines.append(
                f"- `{canonical.short(objection['id'])}` "
                f"({objection.get('performed', '')}) — {headline}"
            )
    lines.append("")

    lines.append("## Lineage")
    lines.append("")
    if not chain:
        lines.append("*(no recorded chain)*")
    for record in chain:
        registration = record.get("registration") or {}
        mark = "attested" if registration.get("attested") else "unattested"
        lines.append(
            f"- `{canonical.short(record['id'])}` {record.get('performed', '')} — "
            f"{_describe(record)} · disposition `{record.get('disposition')}` · {mark}"
        )
        prior = record.get("prior_state")
        posterior = record.get("posterior_state")
        if prior or posterior:
            lines.append(
                f"  - `{canonical.short(prior) if prior else '—'}` → "
                f"`{canonical.short(posterior) if posterior else '—'}`"
            )
    lines.append("")

    lines.append("## Contributors")
    lines.append("")
    people = views.contributors(chain)
    if not people:
        lines.append("*(none recorded)*")
    for party, roles in people:
        role_text = ", ".join(roles) if roles else "performer"
        lines.append(f"- `{canonical.short(party, 16)}` — {role_text}")
    lines.append("")

    absorbed = views.absorptions(chain)
    if absorbed:
        lines.append("## Absorbed content")
        lines.append("")
        lines.append(
            "Content taken into this line of work from elsewhere, attributed to the "
            "party who produced it. Attribution confers no power to prevent, "
            "condition or reverse the use."
        )
        lines.append("")
        for link in absorbed:
            lines.append(
                f"- from state `{canonical.short(link.get('state', ''))}` "
                f"by `{canonical.short(link.get('party', ''), 16)}` "
                f"into `{canonical.short(link['into'])}`"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"Generated from release `{release['id']}` by grrp, "
        f"an implementation of {release.get('protocol')}. "
        "The record this document was generated from can be obtained and "
        "continued under a different implementation without anyone's permission."
    )
    lines.append("")
    return "\n".join(lines)
