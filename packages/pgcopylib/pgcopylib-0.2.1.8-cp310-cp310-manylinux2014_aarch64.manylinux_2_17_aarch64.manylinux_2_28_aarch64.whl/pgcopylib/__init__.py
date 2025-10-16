"""PGCopy bynary dump parser."""

from .common import (
    PGCopyRecordError,
    PGCopySignatureError,
    PGOid,
)
from .reader import PGCopyReader
from .writer import PGCopyWriter


__all__ = (
    "PGCopyReader",
    "PGCopyRecordError",
    "PGCopySignatureError",
    "PGCopyWriter",
    "PGOid",
)
__author__ = "0xMihalich"
__version__ = "0.2.1.8"
