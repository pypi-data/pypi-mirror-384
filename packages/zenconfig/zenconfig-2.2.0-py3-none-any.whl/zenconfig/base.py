import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from zenconfig.encoder import Encoder


class ZenConfigError(Exception):
    """Default error when Handling config files."""


class Format(ABC):
    """Abstract class for handling different file formats."""

    @abstractmethod
    def load(self, path: Path) -> Dict[str, Any]:
        """Load the configuration file into a dict."""

    @abstractmethod
    def dump(
        self,
        path: Path,
        config: Dict[str, Any],
    ) -> None:
        """Dump in the configuration file."""


C = TypeVar("C")


class Schema(ABC, Generic[C]):
    """Abstract class for handling different config class types."""

    @abstractmethod
    def handles(self, cls: type) -> bool:
        """Return if a type is handled by this schema."""

    @abstractmethod
    def from_dict(self, cls: Type[C], cfg: Dict[str, Any]) -> C:
        """Load the schema based on a dict configuration."""

    @abstractmethod
    def to_dict(self, config: Any, encoder: Encoder) -> Dict[str, Any]:
        """Dump the config to dict."""


class BaseConfig:
    """Abstract base class for handling config files."""

    # Environment variable name holding the config file path to load.
    # Override to disable.
    ENV_PATH: ClassVar[Optional[str]] = "CONFIG"
    # Hardcoded config file path to load.
    # Fallback when no path is found in the environment variable.
    PATH: ClassVar[Optional[str]] = None
    # Selected schema class instance.
    # Override to disable auto selection or control dump options.
    SCHEMA: ClassVar[Optional[Schema]] = None

    # Paths of all config files handled.
    __PATHS: ClassVar[Optional[Tuple[Path, ...]]] = None
    # All formats supported, by extension.
    __FORMATS: ClassVar[Dict[str, Format]] = {}
    # All schema classes supported.
    __SCHEMAS: ClassVar[List[Schema]] = []

    @classmethod
    def register_format(cls, fmt: Format, *extensions: str) -> None:
        """Add a format class to the list of supported ones."""
        for ext in extensions:
            cls.__FORMATS[ext] = fmt

    @classmethod
    def register_schema(cls, schema: Schema[C]) -> None:
        """Add a schema class to the list of supported ones."""
        cls.__SCHEMAS.append(schema)

    @classmethod
    def _paths(cls) -> Tuple[Path, ...]:
        """Cached method to get all handled file paths."""
        if cls.__PATHS:
            return cls.__PATHS
        found_path: Optional[str] = None
        if cls.ENV_PATH:
            found_path = os.environ.get(cls.ENV_PATH)
        if not found_path:
            found_path = cls.PATH
        if not found_path:
            raise ZenConfigError(
                f"could not find the config path for config {cls.__qualname__}, tried env variable {cls.ENV_PATH}"
            )
        cls.__PATHS = tuple(
            sorted(_handle_globbing(Path(found_path).expanduser().absolute()))
        )
        return cls.__PATHS

    @classmethod
    def _format(cls, path: Optional[Path] = None) -> Format:
        """Get the format instance for a path."""
        if path:
            suffix = path.suffix
        else:
            paths = cls._paths()
            if len(paths) != 1:
                raise ZenConfigError(
                    "multiple configuration files, use the path parameter"
                )
            suffix = paths[0].suffix
        if suffix not in cls.__FORMATS:
            raise ZenConfigError(
                f"unsupported extension {suffix} for config {cls.__qualname__}, maybe you are missing an extra"
            )
        return cls.__FORMATS[suffix]

    @classmethod
    def _schema(cls) -> Schema:
        """Get the schema instance for this config class."""
        if cls.SCHEMA:
            return cls.SCHEMA
        for schema in cls.__SCHEMAS:
            if not schema.handles(cls):
                continue
            cls.SCHEMA = schema
            return cls.SCHEMA
        raise ZenConfigError(
            f"could not infer config schema for config {cls.__qualname__}, maybe you are missing an extra"
        )


def _handle_globbing(original_path: Path) -> Iterator[Path]:
    """Convert a glob path to all matched paths."""
    directory = Path(original_path)
    glob = False
    while "*" in directory.name or "?" in directory.name or "[" in directory.name:
        directory = directory.parent
        glob = True
    if not glob:
        yield original_path
    else:
        pattern = str(original_path.relative_to(directory))
        for path in directory.rglob(pattern):
            if path.is_file():
                yield path
