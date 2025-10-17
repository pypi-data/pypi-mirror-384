from typing import Any, Dict, Type, TypeVar

from typing_extensions import TypeGuard

from zenconfig.base import BaseConfig, Schema
from zenconfig.encoder import Encoder

C = TypeVar("C", bound=dict)


class DictSchema(Schema[C]):
    def handles(self, cls: type) -> TypeGuard[Type[dict]]:
        return issubclass(cls, dict)

    def from_dict(self, cls: Type[C], cfg: Dict[str, Any]) -> C:
        return cls(cfg)

    def to_dict(self, config: C, encoder: Encoder) -> Dict[str, Any]:
        return encoder(config)


BaseConfig.register_schema(DictSchema())
