"""Signing in, and what signing in is not.

The risk this file exists to guard against is not that the login is weak. It
is that the login starts to mean something: that having an account here comes
to look like membership, and that the server holding the accounts comes to
look like the authority. Most of what follows checks that it does not.
"""

from __future__ import annotations

import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from grrp import accounts, errors, identity, store, ui


@pytest.fixture()
def door(workspace):
    """A server with one account, and nobody signed in."""
    accounts.create(workspace.path, "ada", "a-good-enough-password")
    sessions = ui.Sessions()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), ui.make_handler(ui.Workspace(workspace.path), "secret", sessions)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield workspace, f"http://127.0.0.1:{server.server_port}", sessions
    server.shutdown()
    server.server_close()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def visit(base: str, path: str, cookie: str = ""):
    """GET without following the redirect, so the reply itself can be read."""
    request = urllib.request.Request(
        f"{base}{path}", headers={"Cookie": cookie} if cookie else {}
    )
    try:
        return urllib.request.build_opener(NoRedirect).open(request)
    except urllib.error.HTTPError as reply:
        return reply


def post(base: str, path: str, fields: dict, cookie: str = ""):
    """POST without following the redirect, so the reply can be read."""
    request = urllib.request.Request(
        f"{base}{path}",
        data=urllib.parse.urlencode(fields).encode(),
        method="POST",
        headers={"Cookie": cookie} if cookie else {},
    )
    try:
        return urllib.request.build_opener(NoRedirect).open(request)
    except urllib.error.HTTPError as reply:
        return reply


# --- the password does what a password does, and no more ---------------------

def test_a_password_is_stored_hashed_and_never_in_the_clear(workspace):
    accounts.create(workspace.path, "ada", "a-good-enough-password")
    written = (accounts.directory(workspace.path) / "ada.yaml").read_text(encoding="utf-8")

    assert "a-good-enough-password" not in written
    assert "scrypt$" in written


def test_the_wrong_password_is_refused_without_saying_which_half_was_wrong(workspace):
    accounts.create(workspace.path, "ada", "a-good-enough-password")

    with pytest.raises(errors.Refused) as wrong_password:
        accounts.authenticate(workspace.path, "ada", "something-else")
    with pytest.raises(errors.Refused) as no_such_account:
        accounts.authenticate(workspace.path, "nobody", "something-else")

    # The same sentence either way: otherwise the page discloses who has an
    # account here, which is a directory of participants by another route.
    assert str(wrong_password.value) == str(no_such_account.value)


def test_an_account_reaches_a_keypair_and_the_keypair_is_what_signs(workspace):
    account = accounts.create(workspace.path, "ada", "a-good-enough-password")
    who = identity.find(workspace.path, "ada")

    assert account.party == who.party
    assert who.party.startswith("key:ed25519:")
    # The private half exists, is hers, and is not in the account file.
    assert (identity.ring(workspace.path) / "ada.key").is_file()
    assert "PRIVATE" not in (accounts.directory(workspace.path) / "ada.yaml").read_text("utf-8")


def test_deleting_every_account_leaves_the_record_intact(workspace, trajectory):
    """The point of the whole arrangement: the host is not the authority."""
    _, traj_id = trajectory
    accounts.create(workspace.path, "ada", "a-good-enough-password")
    workspace.run("claim", traj_id, "-m", "A position.")

    for path in accounts.directory(workspace.path).iterdir():
        path.unlink()

    assert workspace.run("check").exit_code == 0
    assert workspace.run("log").exit_code == 0


# --- the door ----------------------------------------------------------------

def test_the_page_asks_who_is_signing_before_it_shows_anything(door):
    _, base, _ = door
    reply = visit(base, "/")

    assert reply.code == 303
    assert reply.headers["Location"].startswith("/sign-in")


def test_signing_in_opens_a_session_and_the_cookie_carries_no_name(door):
    _, base, sessions = door
    reply = post(base, "/sign-in", {
        "token": "secret", "name": "ada", "password": "a-good-enough-password", "back": "/",
    })

    assert reply.code == 303
    cookie = reply.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    ticket = cookie.split(";")[0].split("=", 1)[1]
    assert "ada" not in ticket, "the cookie is an opaque ticket, not an identity"
    assert sessions.name_for(ticket) == "ada"


def test_the_wrong_password_opens_nothing(door):
    _, base, sessions = door
    reply = post(base, "/sign-in", {
        "token": "secret", "name": "ada", "password": "guessing", "back": "/",
    })

    assert reply.headers["Location"].startswith("/sign-in")
    assert "Set-Cookie" not in reply.headers
    assert sessions._open == {}


def test_signing_out_ends_the_session_on_the_server_not_only_in_the_browser(door):
    _, base, sessions = door
    ticket = sessions.begin("ada")

    post(base, "/sign-out", {"token": "secret"}, cookie=f"{ui.COOKIE}={ticket}")

    assert sessions.name_for(ticket) is None


def test_a_session_that_is_not_open_is_not_signed_in(door):
    _, base, _ = door
    reply = visit(base, "/", cookie=f"{ui.COOKIE}=invented")

    assert reply.code == 303, "a made-up ticket is not a session"


def test_no_session_is_written_to_disk(door):
    """Who was here and when is a monitoring record, so it is not kept."""
    workspace, base, sessions = door
    sessions.begin("ada")
    urllib.request.urlopen(f"{base}/sign-in").read()

    for path in workspace.path.rglob("*"):
        if path.is_file() and "session" in path.name.lower():
            raise AssertionError(f"a session was written to {path}")


# --- registration is closed, and says why ------------------------------------

def test_registration_is_closed_and_the_page_says_what_that_does_not_mean(door):
    _, base, _ = door
    body = urllib.request.urlopen(f"{base}/sign-in").read().decode("utf-8")

    assert "Registration is closed" in body
    assert "grrp account add" in body
    # The point that stops a closed door from meaning exclusion: an account is
    # access to this server, not permission to take part.
    assert "without asking" in body


def test_a_stranger_cannot_register_while_it_is_closed(door):
    workspace, base, _ = door
    reply = post(base, "/register", {
        "token": "secret", "name": "mallory", "password": "a-good-enough-password",
    })

    assert reply.code == 303
    assert not accounts.exists(workspace.path, "mallory")


def test_the_sign_in_page_lists_nobody(door):
    """A page that showed who has an account would be a directory of people."""
    _, base, _ = door
    body = urllib.request.urlopen(f"{base}/sign-in").read().decode("utf-8")

    assert "ada" not in body.split("</style>")[1].lower()


# --- two parties, which is what attestation needs ----------------------------

def test_two_accounts_are_two_parties_and_that_is_what_makes_an_act_attested(workspace):
    accounts.create(workspace.path, "ada", "a-good-enough-password")
    accounts.create(workspace.path, "grace", "another-fine-password")

    ada = identity.find(workspace.path, "ada")
    grace = identity.find(workspace.path, "grace")

    assert ada.party != grace.party
    identity.adopt(workspace.path, workspace.repo, "ada")
    identity.adopt(workspace.path, workspace.repo, "grace")
    assert store.Repo(workspace.path, acting_as="ada").party() == ada.party
    assert store.Repo(workspace.path, acting_as="grace").party() == grace.party


def test_one_identity_carries_across_records(workspace, tmp_path):
    """Continuity is what attribution rests on, so the keyring is not per record."""
    accounts.create(workspace.path, "ada", "a-good-enough-password")
    second = store.Repo(workspace.path / "another")
    (second.root).mkdir()
    from grrp import actions

    actions.initialise(second.root)

    identity.adopt(workspace.path, workspace.repo, "ada")
    identity.adopt(workspace.path, second, "ada")

    assert (workspace.repo.keys_dir / "ada.pub").read_text("utf-8") == (
        (second.keys_dir / "ada.pub").read_text("utf-8")
    )


def test_adopting_a_name_another_record_knows_as_someone_else_is_refused(workspace, tmp_path):
    accounts.create(workspace.path, "ada", "a-good-enough-password")
    workspace.repo.keys_dir.mkdir(parents=True, exist_ok=True)
    (workspace.repo.keys_dir / "ada.pub").write_text("key:ed25519:somebodyelse\n", "utf-8")

    with pytest.raises(errors.Refused, match="somebody else"):
        identity.adopt(workspace.path, workspace.repo, "ada")


# --- keys and hashes stay out of git -----------------------------------------

def test_neither_private_keys_nor_password_hashes_are_committed(workspace):
    accounts.create(workspace.path, "ada", "a-good-enough-password")

    assert "*.key" in (identity.ring(workspace.path) / ".gitignore").read_text("utf-8")
    assert (accounts.directory(workspace.path) / ".gitignore").read_text("utf-8").strip() != ""
