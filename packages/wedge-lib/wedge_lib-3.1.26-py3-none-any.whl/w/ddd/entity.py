from abc import ABC
from typing import Annotated, Dict, Any

from pydantic import BaseModel, ConfigDict, Field

IntId = Annotated[int, Field(gt=0, frozen=True)]
StrId = Annotated[str, Field(max_length=100, frozen=True)]
UlidId = Annotated[str, Field(max_length=26, min_length=26, frozen=True)]

EntityId = IntId | StrId | UlidId
RawItem = Dict[str, Any]


class ValueObject(BaseModel, ABC):
    model_config = ConfigDict(use_enum_values=True, validate_default=True, frozen=True)


class Entity(BaseModel, ABC):
    model_config = ConfigDict(use_enum_values=True, validate_default=True, frozen=True)
    id: EntityId

    @classmethod
    def short_classname(cls) -> str:
        return cls.__name__

    @classmethod
    def _entity_label(cls) -> str:
        return cls.short_classname()
