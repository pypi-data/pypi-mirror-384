"""
Core protocol that every payload writer must implement.

A *writer* takes an iterable of :class:`DataSample` objects, serialises the
batch to **bytes**
"""

from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable


@runtime_checkable
class PayloadWriter(Protocol):
    """Convert a sequence of samples into a single binary payload."""

    def write(self, samples: Iterable["DataSample"]) -> bytes:  # noqa: D401
        """
        Serialise *samples* into a single ``bytes`` object.

        Implementations choose their own container/codec.  They must
        raise a sensible ``ValueError`` if *samples* is empty.
        """
        ...
