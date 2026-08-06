"""Errors that are the user's problem, and errors that are the protocol's."""

from __future__ import annotations


class GrrpError(Exception):
    """Base class.  Printed to the user without a traceback."""


class NotARepository(GrrpError):
    pass


class AlreadyInitialised(GrrpError):
    pass


class AmbiguousReference(GrrpError):
    pass


class UnknownReference(GrrpError):
    pass


class ConstraintViolation(GrrpError):
    """A refusal required by the protocol.

    The message names the constraint, because a refusal a user cannot account
    for reads as a bug.
    """

    def __init__(self, constraint: str, message: str) -> None:
        super().__init__(f"[{constraint}] {message}")
        self.constraint = constraint
