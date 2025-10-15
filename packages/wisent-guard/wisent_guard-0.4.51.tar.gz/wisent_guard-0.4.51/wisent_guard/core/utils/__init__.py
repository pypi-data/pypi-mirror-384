"""
Utility modules for wisent_guard.core
"""
from .device import (
    empty_device_cache,
    preferred_dtype,
    resolve_default_device,
    resolve_device,
    resolve_torch_device,
)

__all__ = [
    "empty_device_cache",
    "preferred_dtype",
    "resolve_default_device",
    "resolve_device",
    "resolve_torch_device",
]
