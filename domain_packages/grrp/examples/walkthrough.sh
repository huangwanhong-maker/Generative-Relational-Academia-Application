#!/usr/bin/env bash
#
# A walkthrough of grrp, in four phases.
#
# It works the philosophy case from the specification: a claim about trust, an
# objection that it omits institutional power, a transformation accepting the
# objection, a second objection that is never resolved, a divergence, and a
# release that enumerates the objection still standing.
#
# Run it anywhere. It builds everything under ./grrp-walkthrough and touches
# nothing else. Delete that directory when you are done.
#
#   bash walkthrough.sh          all four phases
#   bash walkthrough.sh 1        just the first
#
set -euo pipefail

PHASE="${1:-all}"
ROOT="$(pwd)/grrp-walkthrough"
say() { printf '\n\033[1m── %s\033[0m\n\n' "$*"; }
run() { printf '\033[2m$ %s\033[0m\n' "$*"; eval "$@"; }

# The identifier of the one live position, and of the newest transition. Real
# use reads these off the screen; a script needs them in a variable.
live() { python -c "
from grrp.store import Repo; from grrp import views
print(views.current_states(Repo.discover(), '$1')[0].split(':')[-1][:10])"; }
newest() { python -c "
from grrp.store import Repo
print(Repo.discover().transitions('$1')[-1]['id'].split(':')[-1][:10])"; }
proposed() { python -c "
from grrp.store import Repo
print(Repo.discover().proposals('$1')[0]['id'].split(':')[-1][:10])"; }

rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT"

# ── 1. alone ─────────────────────────────────────────────────────────────────
# The tier that has to be worth using by one person on the first day. It
# delivers utility and no evidential weight, and the two are never confused.

say "1. Alone"
mkdir trust && cd trust && git init -q .
run "grrp init"
run "grrp new 'Is trust a property obtaining between individuals?' --title trust"
run "grrp claim -m 'Trust is a property obtaining between individuals.'"

# A challenge does not alter the state it challenges. If it is accepted, the
# change is a separate transformation, and the two are linked in the graph.
run "grrp challenge -m 'This omits institutional power: a relation between individuals of unequal standing is not the relation the account describes.'"
OBJECTION=$(newest trust)
CLAIMED=$(live trust)
run "grrp transform $CLAIMED -m 'Trust is a process shaped by asymmetry of power.' --relation modifies --answering $OBJECTION"

# Most objections in theoretical work are never resolved. They stand, and the
# work proceeds beside them.
run "grrp challenge -m 'The revision cannot now distinguish trust from compliance.'"

# In inquiry a fork is frequently the correct outcome, so both directions are
# kept and neither is marked principal.
SHARED=$(live trust)
run "grrp transform $SHARED -m 'Narrow the account to institutional settings.'"
run "grrp transform $SHARED -m 'Keep the general scope and weaken the claim.'"

run "grrp show"

[ "$PHASE" = "1" ] && exit 0

# ── 2. what the record is for ────────────────────────────────────────────────
# Connections, checks that failed, and the expensive act: a decision with its
# reason, recorded at the moment of setting a direction aside.

say "2. Connections, failed checks, and abandoning something"

# Two positions are live, so the tool will not guess which one this attaches
# to. Name a branch; nothing in the design gives it a basis for picking.
run "grrp connect $(live trust) --to doi:10.1234/ostrom1990 -m 'Monitoring and graduated sanction: the same obstruction, in commons governance.'"

cd "$ROOT" && mkdir transfer && cd transfer && git init -q .
run "grrp init"
run "grrp new 'Does the regulariser transfer across domains?' --title transfer"
run "grrp claim -m 'It transfers under an independence assumption.'"
run "grrp verify --failed -m 'Ran it on the target domain. Independence does not hold there.'"
DOOMED=$(live transfer)
run "grrp decide $DOOMED --abandon -m 'Independence is not available in the target domain, and nothing weaker was enough. This route stops here.'"
run "grrp open"

[ "$PHASE" = "2" ] && exit 0

# ── 3. a second party ────────────────────────────────────────────────────────
# A record you registered yourself is evidence to nobody. One colleague's key
# is what makes it evidence, and it is the whole of the setup that takes.

say "3. A second party"
cd "$ROOT/trust"
BO=$(python -c "
from grrp.store import Repo; from grrp import keys
print(keys.generate(Repo.discover().keys_dir, 'bo'))")
run "grrp key add bo $BO"
run "grrp claim $(live trust) -m 'Trust is generated and maintained under governance arrangements.'"

PROPOSAL=$(proposed trust)
GOVERNANCE=$(python -c "
from grrp.store import Repo
print(Repo.discover().proposals('trust')[0]['posterior_state'].split(':')[-1][:10])")

# You cannot register your own act. That is where credibility comes from: not
# from the content of a record, its length or its detail, but from being
# registered by parties who did not coordinate.
set +e
run "grrp register $PROPOSAL"
set -e
run "GRRP_KEY=bo grrp register $PROPOSAL"

# A release asserts that a state is published and that these objections stand.
# It asserts nothing about their merit, and it is not a certification.
run "grrp release $GOVERNANCE"
GRRP_KEY=bo grrp register "$(proposed trust)" > /dev/null
RELEASE=$(python -c "
from grrp.store import Repo
print(Repo.discover().releases('trust')[0]['id'].split(':')[-1][:10])")
run "grrp export $RELEASE -o paper.md"
run "head -24 paper.md"

[ "$PHASE" = "3" ] && exit 0

# ── 4. withholding, and leaving ──────────────────────────────────────────────
# The question is never whether to withhold but on what ground, and what
# follows from the ground. Every ground leaves a residue that must still be
# disclosed.

say "4. Withholding, and leaving"
run "grrp charter adopt --classes private,group,public"
run "grrp claim $(live trust) -m 'An early framing I am not ready to have read.'"
GRRP_KEY=bo grrp register "$(proposed trust)" > /dev/null
EARLY=$(newest trust)
run "grrp disclose $EARLY --class private --ground vulnerability --release-at 2027-06-01"

# A delay that can be extended indefinitely is a permanent withholding made to
# look temporary. The attempt is refused, and recorded.
set +e
run "grrp disclose $EARLY --class private --ground vulnerability --release-at 2030-01-01"
set -e

run "grrp bundle -o $ROOT/trust.zip"
cd "$ROOT" && mkdir elsewhere && cd elsewhere && git init -q .
run "grrp init"
run "grrp continue $ROOT/trust.zip"

# Several positions are live, so name the one being continued.
run "grrp transform $(live trust) -m 'Continued on another machine, from what was obtained.'"
run "grrp check"

say "Done"
printf 'Everything is under %s\n' "$ROOT"
printf 'Try the page:  cd %s && grrp ui\n' "$ROOT"
