# GRA — the web platform

A host for records, which is **not** their authority.

Three packages, and the boundary between them is the design:

| | | |
|---|---|---|
| `packages/protocol` | GRRP v0.1 in TypeScript | canonicalisation, identifiers, signing — the same code in the browser and on the server |
| `packages/server` | Fastify + SQLite | accounts, sessions, an index. Owns no protocol decisions |
| `packages/client` | React + Vite | four pages. Disposable by design |

The reference implementation, [`grrp`](../grrp), stays Python and stays the
thing the protocol is defined against. This server invokes it as a subprocess
to create records, for the same reason a git forge shells out to `git`.

## Running it

```bash
npm install
npm run build --workspace @gra/protocol
npm run build --workspace @gra/client

# Registration is closed, so accounts are made here.
npm run account --workspace @gra/server -- add ada --password '…'

npm run dev            # http://127.0.0.1:5173
```

`grrp` must be reachable. Set `GRA_GRRP` if it is not on the path as
`python -m grrp.cli`.

| variable | default | |
|---|---|---|
| `GRA_RECORDS` | `data/records` | the records. **These are the record.** |
| `GRA_DB` | `data/index.sqlite` | the index. Delete it whenever you like. |
| `GRA_GRRP` | `python -m grrp.cli` | how to invoke the reference implementation |
| `GRA_HOST` / `GRA_PORT` | `127.0.0.1` / `5173` | loopback by default, deliberately |

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

The server stores public keys only. It has no column a private key could go
in, which is why an attestation registered here means something: a host holding
both parties' keys could forge one, and C2 would be bookkeeping rather than
evidence.

The bootstrap path is the weak point and is not glossed: `account add` without
`--party` generates a keypair in this process and prints the private half once.
Prefer `--party` with a key the person generated themselves. Browser-side key
generation is the next piece of work.

## Two implementations

`packages/protocol` and `grrp` must agree on every identifier for every input.
`grrp/tools/make_vectors.py` generates the vectors; the TypeScript suite must
reproduce all of them. A disagreement is a specification bug.

The first run of that suite found one: Python and TypeScript stripped different
sets of trailing whitespace, so the same document got two different state
identifiers. See `TRAILING_WHITESPACE` in `canonical.py` and `TRAILING` in
`canonical.ts`.
