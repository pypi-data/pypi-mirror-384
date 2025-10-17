import logging
from abc import ABC
from enum import IntEnum
from typing import Any, ClassVar, Dict, Type, TypeVar

from zenconfig.base import BaseConfig, ZenConfigError

logger = logging.getLogger(__name__)


class MergeStrategy(IntEnum):
    """Available merge strategies when handling multiple config files."""

    SHALLOW = 1
    DEEP = 2
    REPLACE = 3


C = TypeVar("C", bound="ReadOnlyConfig")


class ReadOnlyConfig(BaseConfig, ABC):
    """Abstract base class for supporting read only operations."""

    # Merge strategy chosen when handling multiple config files.
    MERGE_STRATEGY: ClassVar[MergeStrategy] = MergeStrategy.DEEP

    @classmethod
    def load(cls: Type[C]) -> C:
        """Load the configuration class from file(s)."""
        dict_config: Dict[str, Any] = {}
        for path in cls._paths():
            if not path.exists():
                continue
            fmt = cls._format(path)
            logger.debug(
                "using %s to load %s from %s",
                fmt.__class__.__name__,
                cls.__name__,
                path,
            )
            config = fmt.load(path)
            if not dict_config or cls.MERGE_STRATEGY is MergeStrategy.REPLACE:
                dict_config = config
            elif cls.MERGE_STRATEGY is MergeStrategy.SHALLOW:
                dict_config.update(config)
            elif cls.MERGE_STRATEGY is MergeStrategy.DEEP:
                _deep_merge(dict_config, config)
            else:
                raise ZenConfigError(f"unsupported merge strategy {cls.MERGE_STRATEGY}")
        return cls._schema().from_dict(cls, dict_config)


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> None:
    """Deep merge dictionaries."""
    for k, v in b.items():
        if k not in a or not isinstance(a[k], dict) or not isinstance(v, dict):
            a[k] = v
        else:
            _deep_merge(a[k], v)
