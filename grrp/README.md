# grrp

Reference implementation of the **Generative Relational Research Protocol v0.1**, specified in
[*Specifying the GRRP*](../papers/GRA-paper-IV-Specifying-the-GRRP.pdf). **The specification governs
where the two differ.**

A command-line tool that records the trajectory of an inquiry as **typed transitions** in an ordinary
git repository, in plain text, **with no server, no account, and no network**.

**Status: M0 + M1 + M2.** Personal tier, all eight acts, and redaction. Useful alone, and carrying
**no evidential weight** — every transition is registered by the party who performed it, and is
marked unattested wherever it is shown or exported. Attestation, disclosure grounds, bundling and
continuation are M3–M4 and are not built.

---

## The unit of record

Not a document. Not a comment. A **transition**: an identified prior state became an identified
posterior state, through a typed act performed by a party and registered by a party.

```
state s_k  ──[ act: challenge · target: assumption · relation: cito:disagreesWith ]──▶  s_k+1
               performer: key:ed25519:…    disposition: unresolved
```

A **trajectory** is the directed acyclic graph of these. **The current state is computed from the
graph on demand and is never stored as an authority** — a stored snapshot becomes the thing people
trust, the log drifts from it or is edited to match it, and every claim about integrity fails at once.

## Install and use

```bash
pipx install -e .          # or: python -m pip install -e .

grrp init
grrp new "Is trust a property obtaining between individuals?"
grrp claim      -m "Trust obtains between individuals."
grrp challenge  -m "This omits institutional power."
grrp transform  -m "Trust is a process shaped by asymmetry of power." --answering <challenge>
grrp decide     --abandon        # no -m: opens your editor and asks for the reason
grrp connect    --to doi:10.1234/x -m "Same obstruction, other field."
grrp verify     --failed -m "Ran it on the target domain; independence fails."
grrp redact     <state> --ground consent_withdrawn

grrp show                  # where this stands: question, live positions, what is open
grrp open                  # what you still owe an answer to — and the entry path
grrp state                 # the live positions, derived
grrp log
grrp release               # publishes, enumerating objections that still stand
grrp export <release> -o paper.md
grrp check                 # verify the record, and this tool against the protocol
```

**You rarely need to name a state.** `challenge`, `transform`, `decide` and `release` default to the
live position, which is what you almost always mean, and saves copying a hash out of one command into
the next. Where two positions are live they refuse and list both with their text — nothing in the
design gives the tool a basis for picking one.

**Omit `-m` and your editor opens**, with a prompt for the act you are performing. `decide` gets the
longest prompt, because articulating why a direction was set aside is the expensive act and the one
everything else depends on. Set `$GRRP_EDITOR` if you want a different editor here than in git.

Every command's `--help` states **`Purpose (for you):`** — what the person running it gets. That is
checked by the test suite, because the reason every comparable system since 1970 went unadopted is
that the work of recording fell on the party who gained least from the record.

## Layout

```
.grrp/
  profile.yaml              protocol version, tier, hash, canonicalisation, party, vocabularies
  keys/self.pub             the private key is gitignored and never leaves the machine
  events/                   local event plane — gitignored, never exported
trajectories/<traj-id>/
  trajectory.yaml
  states/<hash>.md          content: separable, redactable
  transitions/<hash>.yaml   skeleton: append-only, never rewritten
  disclosure/<hash>.yaml    sidecar (M3): class and ground, outside the identifier
  releases/<hash>.yaml
```

## Two design decisions worth stating

**Disclosure is a sidecar, not a field in the transition file.** The illustrative skeleton in the
build brief shows `disclosure:` inline. Keeping it there forces a choice between two rules that both
have to hold: *any edit under `transitions/` is detected*, and *changing a class or a scheduled
release firing invalidates nothing*. Putting disclosure in `disclosure/<id>.yaml` lets both stay
strict, and it is what the specification's own git deployment (§21.5) recommends for the same reason.
Touches **C3, C7, C8**.

**Registration is excluded from the identifier; the signature covers the identifier.** The identifier
is computed over the covered payload and the parent identifiers, and excludes `registration` and
`disclosure`. A signature (M3) will cover `{id, registrar, time}`, so it binds the registrar and the
time without self-reference and stays valid when disclosure widens or content is redacted. The cost,
stated plainly: at the personal tier, where nothing is signed, **editing the `registration` block of a
transition is not detectable by `grrp check`.** Every covered field is. This is acceptable only
because the personal tier carries no evidential weight in the first place, and it closes at M3.

## Derivation rules

Views are computed, never stored. The rules are choices you are entitled to disagree with, so they
are stated in one place ([`views.py`](src/grrp/views.py)):

| | |
|---|---|
| produces a state | every act writes a posterior state |
| **supersedes** its prior | `transformation` only |
| **retires** its prior | `decision` whose relation is `cito:retracts` (i.e. `--abandon`) |
| a **live position** | posterior of `claim` or `transformation`, not superseded and not retired |
| **answered** | a challenge or failed verification that a later `transformation` or `decision` names among its parents |

A trajectory's opening **question is a state and not a position**: it is what the work is about, it
does not stop being so when someone takes a view, and it stays on the open register until something
answers it. It also anchors the first claim, so that even the first transition references an
identified prior state rather than the project as a whole.

Objections, decisions and releases produce states too, but those are annotations on a position rather
than positions themselves, so they are not candidates for "the current state". Nothing is edited to
mark a challenge answered — the graph already records it.

## What this tool will not do

- **No scores, rankings, counts across trajectories, or dashboards.** No quantity over participants
  or over trajectories is computed, stored, displayed or exported. Counts *within* one trajectory,
  shown without comparison, are permitted. When something feels like it wants a number, that is the
  constraint working.
- **No merge.** Two revisions of a concept do not compose, no conflict region localises, and no test
  decides the result. Integration is a **synthesis** (a state with several parents) or an
  **absorption** (content taken with attribution). The word does not appear in the interface.
- **No principal branch.** Where the work diverges, both directions are kept and neither is marked
  canonical, default or current. In inquiry a fork is frequently the correct outcome.
- **No unpublish.** Disclosure may widen and never narrow. A party who has read a record retains what
  they read, and an operation offering the appearance of withdrawal would misdescribe the world to the
  people relying on it.
- **No model, no network, no database.** Every operation runs with a text editor and git. A model may
  *propose* a transition and may not author or register one; a model-originated proposal is marked as
  such (`trigger: ai_suggestion`).
- **No editing.** A recorded transition is never altered or removed. A correction is a further
  transition referencing the one corrected.
- **No silent erasure.** `redact` removes a state's content and leaves everything else: that the
  transition occurred, by whom, of what type, where in the graph — and that a redaction was performed
  and on what ground. A system that erased the trace of an erasure would leave a record misdescribing
  its own history in a way no later reader could detect. It also tells you plainly that earlier git
  commits still hold the text, because possibility is not lawfulness.

## Bindings

Relations bind to **CiTO**, contributor roles to **CRediT**, provenance concepts to **PROV**. Values
stored are identifiers, never display labels — a record holding the word `extends` is uninterpretable
once a second vocabulary uses the same word differently. Three relations the design names have no CiTO
counterpart (`generalises`, `specialises`, `transfers`); they are available as `local:` values, are
flagged as local, and need a charter to define them.

## Tests

```bash
python -m pytest
```

The acceptance tests are written against the constraints, not the features:

| | |
|---|---|
| 1 | no scalar over participants or trajectories, in source or in any command's output |
| 2 | the whole flow runs with no network, no model and no service |
| 3 | every command's `--help` names the purpose it serves for the person running it |
| 4 | editing anything under `transitions/` is detected by `grrp check` |
| 5 | a disclosure change does not invalidate verification |
| 6 | after `grrp redact`, the chain verifies, the graph is unchanged, and the redaction is recorded |
| — | acts default to the live position, and refuse rather than guess at a divergence |
| — | omitting `-m` opens an editor; the prompt below the cut is never recorded |
| 7 | *(M3)* `register` refuses when performer and registrar are identical — **skipped** |
| 8 | *(M4)* `bundle` here, `continue` there, one graph and not two — **skipped** |

Skipped tests are present and named, so what is not yet built is visible rather than absent.

## Next

Use it on real work for two weeks before M2. Record what was annoying — those notes are the input to
everything after this, and they belong in a trajectory.

## Licence

**MIT** — see [LICENSE.md](../LICENSE.md).

Not incidental: a record must be licensed so that **continuation elsewhere is permitted** (Paper I
Req. 16.2, property 4), and the specification must be licensed so that **any party may fork it**
(Paper IV Req. 19.4). Portability is the only bound this design places on the authority of any
position within it, including the authority of whoever wrote this.
