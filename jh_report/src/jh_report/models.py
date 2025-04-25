from dataclasses import dataclass,asdict
from decimal import Decimal
from typing import Any, Iterator

@dataclass
class JhCostNew(object):
    date: str = None
    channel: str = None
    sub_channel: str = None
    cost: Decimal = None
    school:str = None

    def get(self, key, default=None) -> Any | None:
        return getattr(self, key, default)

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        return iter(asdict(self).items())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
