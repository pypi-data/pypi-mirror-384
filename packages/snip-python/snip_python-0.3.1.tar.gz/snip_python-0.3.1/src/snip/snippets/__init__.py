"""Snippets allow you to create reusable components for your labbooks.

We provide you with a set of predefined snippets that you may just use or extend
to create your own snippets.
"""

from .array import ArraySnip
from .image import ImageSnip
from .link import LinkSnip
from .text import TextSnip

__all__ = [
    "ImageSnip",
    "TextSnip",
    "ArraySnip",
    "LinkSnip",
]
