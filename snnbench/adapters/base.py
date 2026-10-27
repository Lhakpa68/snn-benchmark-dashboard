"""Adapter contract.

Every simulator is reached through an adapter implementing this interface, so
the network specification in config.py is written once and translated per
simulator rather than re-specified.

Two rules are enforced here rather than left to each adapter:

1.  Setup and simulation are timed separately. NEST's fixed initialisation cost
    is a real and well-documented property, and a benchmark that folds it into
    the simulation time cannot say whether a simulator is slow to build or slow
    to run. Both numbers are stored.

2.  An adapter that cannot honour a request raises. It never silently
    substitutes a different execution path and returns a plausible number.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Backend:
    key: str
    label: str
    available: bool = True
    reason: str = ""
    note: str = ""


class Unsupported(RuntimeError):
    """Raised when a backend cannot run here. Recorded as an explicit skip
    with a reason, never as a missing or zero value."""


class TrainingIncomplete(RuntimeError):
    """Raised by a checkpointed train() when its time budget ran out before
    training finished. Distinct from a real failure: state was saved and
    calling train() again with the same arguments picks up where it left off.
    The runner reports this as 'in progress', not as a skip or an error, and
    writes nothing to the database for it."""


class Adapter(ABC):
    key: str = ""
    label: str = ""
    caveat: str = ""

    @abstractmethod
    def probe(self) -> tuple[bool, str]:
        """Return (importable, version_or_reason). Must not raise."""

    def backends(self) -> list[Backend]:
        return [Backend("default", self.label)]

    @abstractmethod
    def setup(self, n: int, backend: str):
        """Construct the network. Returns an opaque handle."""

    @abstractmethod
    def simulate(self, handle) -> int:
        """Run the constructed network once. Returns the output spike count."""

    def teardown(self, handle) -> None:
        return None

    # -- Experiment 2 ------------------------------------------------------
    def supports_training(self) -> bool:
        return False

    # Set by train() to {cpu_s, wall_s, cpu_pct, peak_rss_mb} measured over
    # the same region whose duration it reports. None means the adapter did
    # not measure them, and the runner then stores NULL rather than a value.
    last_train_metrics = None

    def train(self, hidden, train_n, test_n, epochs, backend):
        """Return (seconds_per_epoch, test_accuracy_pct, method_note).

        An adapter that measures its own utilisation and peak memory sets
        self.last_train_metrics before returning."""
        raise Unsupported(f"{self.label} has no training implementation")
