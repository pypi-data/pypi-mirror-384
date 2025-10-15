from abc import ABC, abstractmethod
from typing import Any, Generator, Union


from telegram import Update

from .replicas.base import EmptyReplica, Replica, StopReplica


Phrase = Generator[
    Replica,
    Update,
    Any,
]

Polemic = Generator[
    Union[
        Replica,
        StopReplica,
    ],
    Update,
    None,
]


class Dialogue(ABC):
    @abstractmethod
    def dialogue(self, *args, **kwargs) -> Polemic:
        """Method `dialogue()` contains yielded-sequence of `Replicas` which ended by `StopReplica`."""
        ...

    def replicas_flow(self, *args, **kwargs) -> Polemic:
        """Method `replicas_flow()` is internal and help init `Replica`-iterator by default first dialogue step."""
        _ = yield EmptyReplica()
        return (yield from self.dialogue(*args, **kwargs))
