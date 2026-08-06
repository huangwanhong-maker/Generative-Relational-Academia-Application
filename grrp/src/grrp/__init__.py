"""grrp — the Generative Relational Research Protocol, v0.1.

Records the trajectory of an inquiry as typed transitions in an ordinary git
repository, in plain text, with no server, no account and no network.

The unit of record is a transition: an identified prior state became an
identified posterior state, through a typed act performed by a party and
registered by a party. A trajectory is the resulting directed acyclic graph,
and the current state is computed from it rather than stored.
"""

__version__ = "0.1.0"
PROTOCOL = "grrp/0.1"
