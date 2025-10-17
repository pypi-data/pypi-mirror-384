from dataclasses import Field, asdict, fields, is_dataclass
from typing import (
    Any,
    ClassVar,
    Dict,
    Protocol,
    Type,
    TypeVar,
)

from typing_extensions import TypeGuard

from zenconfig.base import BaseConfig, Schema
from zenconfig.encoder import Encoder


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[Dict[str, Field]]


C = TypeVar("C", bound=DataclassInstance)


class DataclassSchema(Schema[C]):
    def handles(self, cls: type) -> TypeGuard[Type[DataclassInstance]]:
        return is_dataclass(cls)

    def from_dict(self, cls: Type[C], cfg: Dict[str, Any]) -> C:
        return _load_nested(cls, cfg)

    def to_dict(self, config: C, encoder: Encoder) -> Dict[str, Any]:
        return encoder(asdict(config))


BaseConfig.register_schema(DataclassSchema())


def _load_nested(cls: Type[C], cfg: Dict[str, Any]) -> C:
    """Load nested dataclasses."""
    kwargs: Dict[str, Any] = {}
    for field in fields(cls):
        if field.name not in cfg:
            continue
        value = cfg[field.name]
        if is_dataclass(field.type) and isinstance(field.type, type):
            value = _load_nested(field.type, value)
        kwargs[field.name] = value
    return cls(**kwargs)
