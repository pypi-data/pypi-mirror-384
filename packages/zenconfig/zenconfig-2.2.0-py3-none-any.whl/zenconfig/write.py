import logging
from abc import ABC
from functools import partial
from typing import ClassVar, Optional

from zenconfig.base import ZenConfigError
from zenconfig.encoder import Encoder, Encoders, combine_encoders, encode
from zenconfig.read import ReadOnlyConfig

logger = logging.getLogger(__name__)


class Config(ReadOnlyConfig, ABC):
    """Abstract base class for handling read and write operations."""

    # File mode used if we need to create the config file.
    FILE_MODE: ClassVar[int] = 0o600
    # Add custom encoders.
    ENCODERS: ClassVar[Encoders] = {}
    # Cached encoder.
    __ENCODER: ClassVar[Optional[Encoder]] = None

    def save(self) -> None:
        """Save the current config to the file."""
        paths = self._paths()
        if len(paths) != 1:
            raise ZenConfigError(
                "cannot save when handling multiple configuration files"
            )
        path = paths[0]
        if not path.exists():
            logger.debug("creating file at path %s", path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(mode=self.FILE_MODE)
        fmt = self._format()
        logger.debug(
            "using %s to save %s to %s",
            fmt.__class__.__name__,
            self.__class__.__name__,
            path,
        )
        schema = self._schema()
        fmt.dump(path, schema.to_dict(self, self._encoder()))

    def clear(self) -> None:
        """Delete the config file(s)."""
        for path in self._paths():
            logger.debug("deleting file at path %s", path)
            path.unlink(missing_ok=True)

    @classmethod
    def _encoder(cls) -> Encoder:
        """Get the encoder, taking into account custom encoders."""
        if cls.__ENCODER:
            return cls.__ENCODER
        encoder = combine_encoders(cls.ENCODERS)
        cls.__ENCODER = partial(encode, encoder)
        return cls.__ENCODER
