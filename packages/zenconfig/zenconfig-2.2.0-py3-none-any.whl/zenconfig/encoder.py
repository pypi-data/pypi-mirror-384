import datetime
from collections import deque
from decimal import Decimal
from enum import Enum
from functools import partial
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)
from pathlib import Path
from re import Pattern
from typing import Any, Callable, Dict
from uuid import UUID

Encoder = Callable[[Any], Any]
Encoders = Dict[type, Encoder]
Data = Dict[str, Any]

BASE_ENCODERS: Encoders = {
    bytes: lambda o: o.decode(),
    datetime.date: lambda o: o.isoformat(),
    datetime.datetime: lambda o: o.isoformat(),
    datetime.time: lambda o: o.isoformat(),
    datetime.timedelta: lambda o: o.total_seconds(),
    Decimal: lambda o: int(o) if o.as_tuple().exponent >= 0 else float(o),
    Enum: lambda o: o.value,
    frozenset: list,
    deque: list,
    IPv4Address: str,
    IPv4Interface: str,
    IPv4Network: str,
    IPv6Address: str,
    IPv6Interface: str,
    IPv6Network: str,
    Path: str,
    Pattern: lambda o: o.pattern,
    set: list,
    tuple: list,
    UUID: str,
}


def _combine(encoders: Encoders, encoder: Encoder, obj: Any) -> Any:
    if encoders:
        for base in obj.__class__.__mro__[:-1]:
            if base not in encoders:
                continue
            return encoders[base](obj)
    return encoder(obj)


base_encoder: Encoder = partial(_combine, BASE_ENCODERS, lambda o: o)


def combine_encoders(encoders: Encoders, encoder: Encoder = base_encoder) -> Encoder:
    """Combine an encoder with additional encoders."""
    return partial(_combine, encoders, encoder)


def encode(encoder: Encoder, obj: Any) -> Any:
    """Recursively encode an object"""
    if isinstance(obj, dict):
        return {k: encode(encoder, v) for k, v in obj.items()}
    encoded = encoder(obj)
    if isinstance(encoded, list):
        return [encode(encoder, e) for e in encoded]
    return encoded
