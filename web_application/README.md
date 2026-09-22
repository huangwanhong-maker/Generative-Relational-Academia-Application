# GRA — the web platform

A host for records, which is **not** their authority.

Three packages, and the boundary between them is the design:

| | | |
|---|---|---|
| `packages/protocol` | GRRP v0.1 in TypeScript | canonicalisation, identifiers, signing — the same code in the browser and on the server |
| `packages/server` | Fastify + SQLite | accounts, sessions, an index. Owns no protocol decisions |
| `packages/client` | React + Vite | the pages. Disposable by design |

The front page is public. Reading what people have shared, and searching across
it, needs no account — an account is access to this host, not permission to
look, and a front door that demanded a login before it showed you anything
would have already decided it was the authority. Signing in adds one thing:
your own projects, and the ability to open one.

**Project** is the top-level object, the way a repository is on a forge. It is
created with a name and, if you want, a description — kept as a plain
`README.md` in the project directory, so it travels with the record and
outlives this server.

A project starts **empty**, and a question is opened separately inside it. The
two are different things: a project is a container, a question anchors a
*trajectory*, and a trajectory is what transitions attach to (C4). Demanding a
question at creation conflates them, and implies a project is one enquiry.

Nothing can be recorded in a project with no question open — every act changes
an identified state, and the question is the first state there is. The
interface says so rather than preventing the situation.

The reference implementation, [`grrp`](../domain_packages/grrp), stays Python and stays the
thing the protocol is defined against. This server invokes it as a subprocess
to create records, for the same reason a git forge shells out to `git`.

## Running it after relocation

See the [application guide](../README.md) for installation, the independent port 8001,
and absolute runtime settings. Source packages stay under this directory; retained
accounts and records live under `applicative_infrastructure/.runtime/academia`.
The source location determines defaults regardless of the process working directory.

The Python implementation is installed from `../domain_packages/grrp` into
`../../.runtime/environments/academia`. `GRA_PYTHON` selects its interpreter;
`GRA_RECORDS`, `GRA_DB`, and `GRA_CLIENT` can select explicit absolute paths.
Back up the account database together with the complete records tree.

## What the database is not

No database is the system of record (C11). The record is plain files:
transitions in YAML, state content in files named by the hash of their bytes.
The SQLite file holds two things — *accounts*, which are local to this host and
part of no record, and *an index*, which is derived and rebuilt by
`POST /api/reindex`.

This is tested rather than asserted. Delete `index.sqlite`, restart, and every
record comes back identical from the files. Accounts do not, because they are
the one thing not derived from anything — back them up, or make them again.

## What this platform refuses to do

Each of these will be asked for, and each request is the design working:

- **No count, score, ranking or index over participants or trajectories** (C6).
  There is no `stars` column and there will not be one. A count *within* one
  trajectory, shown beside its own question and never next to another's, is
  permitted — that is the line.
- **Search filters; it does not rank.** No relevance ordering, no "best match".
  The API says so in its own payload so a second client cannot present results
  as ranked without contradicting it.
- **Disclosure widens and never narrows** (C7). There is a route that lists a
  record and none that unlists it.
- **No combining of two divergent states, and not the word for it** (C5).
- **No directory of people.** Not of accounts here, and certainly not of
  records elsewhere. A service that knew where everyone's records were would
  be party to every entry.

## Keys

An **account** is a name and a password. It reaches an identity; it signs
nothing. An **identity** is a keypair, and the keypair is what signs.

The account database stores public keys only. The record runtime can also contain
private GRRP signing keys used by subprocess operations. Browser-generated keys and
record-local signing keys have different custody paths; a database schema alone
does not establish that the host cannot sign for a party. Back up and restrict
access to the complete runtime accordingly.

The bootstrap path is the weak point and is not glossed: `account add` without
`--party` generates a keypair in this process and prints the private half once.
Prefer `--party` with a key the person generated themselves. Browser-side key
generation is the next piece of work.

## Two implementations

`packages/protocol` and `grrp` must agree on every identifier for every input.
`../domain_packages/grrp/tools/make_vectors.py` generates the vectors; the TypeScript suite must
reproduce all of them. A disagreement is a specification bug.

The first run of that suite found one: Python and TypeScript stripped different
sets of trailing whitespace, so the same document got two different state
identifiers. See `TRAILING_WHITESPACE` in `canonical.py` and `TRAILING` in
`canonical.ts`.
