from abc import ABC
from ..config.config import ConfigProducteca
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class BaseService(ABC):
    config: ConfigProducteca
    endpoint: str
    _record: Optional[Any] = None
    
    def __repr__(self):
        return repr(self._record)

    def to_dict(self):
        return self._record.model_dump(by_alias=True)

    def to_json(self):
        return self._record.model_dump_json(by_alias=True)

    def __getattr__(self, key):
        return getattr(self._record, key)
