import dataclasses

from queuebie.messages import Event


@dataclasses.dataclass(kw_only=True)
class SomethingHappened(Event):
    other_var: int


@dataclasses.dataclass(kw_only=True)
class SomethingHappenedThatWantsToBePersisted(Event):
    any_var: int


@dataclasses.dataclass(kw_only=True)
class SomethingHappenedThatWantsToBePersistedViaEvent(Event):
    any_var: int
