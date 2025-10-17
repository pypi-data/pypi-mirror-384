import contextlib
from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, Type, TypeVar

from pydantic import VERSION, BaseModel
from typing_extensions import TypeGuard

from zenconfig.base import BaseConfig, Schema
from zenconfig.encoder import Encoder, encode

C = TypeVar("C", bound=BaseModel)

PYDANTIC_V1 = VERSION.startswith("1.")


@dataclass
class PydanticSchema(Schema[C]):
    exclude_unset: bool = False
    exclude_defaults: bool = True

    def handles(self, cls: type) -> TypeGuard[Type[BaseModel]]:
        return issubclass(cls, BaseModel)

    def from_dict(self, cls: Type[C], cfg: Dict[str, Any]) -> C:
        if PYDANTIC_V1:
            return cls.parse_obj(cfg)
        return cls.model_validate(cfg)

    def to_dict(self, config: C, encoder: Encoder) -> Dict[str, Any]:
        # Use pydantic encoders.
        if PYDANTIC_V1:
            return _encoder(config)(
                config.dict(
                    exclude_unset=self.exclude_unset,
                    exclude_defaults=self.exclude_defaults,
                )
            )
        else:
            return config.model_dump(
                exclude_unset=self.exclude_unset,
                exclude_defaults=self.exclude_defaults,
                mode="json",
            )


BaseConfig.register_schema(PydanticSchema())


def _encoder(config: BaseModel) -> Encoder:
    def _enc(obj: Any) -> Any:
        with contextlib.suppress(TypeError):
            return config.__json_encoder__(obj)  # type: ignore
        return obj

    return partial(encode, _enc)
