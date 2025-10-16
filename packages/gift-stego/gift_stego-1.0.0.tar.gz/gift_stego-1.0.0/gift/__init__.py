"""GIFT - GIF Analysis Steganography Library/Tool

A pure Python library for hiding and recovering data in GIF files using LSB steganography.

Features:
- LSB steganography in GIF files
- Password-based encryption (PBKDF2)
- Automatic capacity checking
- GIF format validation
- Zero external dependencies
"""

from gift.core import (
    Gif,
    Crypto,
    GifError,
    InvalidGifFormatError,
    InsufficientCapacityError,
    GifParsingError
)

__version__ = "1.0.0"
__author__ = "dtm"
__license__ = "MIT"
__all__ = [
    "Gif",
    "Crypto",
    "GifError",
    "InvalidGifFormatError",
    "InsufficientCapacityError",
    "GifParsingError",
]
