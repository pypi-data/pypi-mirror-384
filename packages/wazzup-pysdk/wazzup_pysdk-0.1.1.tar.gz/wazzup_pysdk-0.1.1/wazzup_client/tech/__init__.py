"""Tech partner API entry points."""

from .client import WazzupTechClient
from . import schemas

__all__ = ("WazzupTechClient", "schemas")
