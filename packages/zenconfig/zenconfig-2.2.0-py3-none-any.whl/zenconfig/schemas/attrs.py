from typing import Any, Dict, Type, TypeVar

import attrs
from typing_extensions import TypeGuard

from zenconfig.base import BaseConfig, Schema
from zenconfig.encoder import Encoder

C = TypeVar("C", bound=attrs.AttrsInstance)


class AttrsSchema(Schema[C]):
    def handles(self, cls: type) -> TypeGuard[Type[attrs.AttrsInstance]]:
        return attrs.has(cls)

    def from_dict(self, cls: Type[C], cfg: Dict[str, Any]) -> C:
        return _load_nested(cls, cfg)

    def to_dict(self, config: C, encoder: Encoder) -> Dict[str, Any]:
        return encoder(attrs.asdict(config))


BaseConfig.register_schema(AttrsSchema())


def _load_nested(cls: Type[C], cfg: Dict[str, Any]) -> C:
    """Load nested attrs."""
    kwargs: Dict[str, Any] = {}
    for field in attrs.fields(cls):
        if field.name not in cfg:
            continue
        value = cfg[field.name]
        if attrs.has(field.type):
            value = _load_nested(field.type, value)
        kwargs[field.name] = value
    return cls(**kwargs)
