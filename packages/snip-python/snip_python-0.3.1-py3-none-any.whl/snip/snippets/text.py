"""Text snip module allows to display text in the labbook."""

from functools import cache
from typing import Optional, TypedDict

from PIL import ImageFont
from typing_extensions import NotRequired

from ..api.snippets import get_font as get_font_from_deployment
from ..logger import log
from .base import BaseSnip


class TextStyles(TypedDict):
    """Text styles."""

    font_size: NotRequired[int]
    font_family: NotRequired[str]
    font_color: NotRequired[str]

    # percent of the font size
    # Defaults to 1.25
    line_height: NotRequired[float]

    """Wrap text after a certain number of pixels."""
    line_wrap: NotRequired[int]


class TextSnip(BaseSnip[dict, dict]):
    """Text snip class.

    Represents a text in the labbook.
    """

    type = "text"

    _styles: TextStyles

    def __init__(self, text: str, **kwargs):
        """Create a text snip from a string.

        Parameters
        ----------
        text : str
            The text to display.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.
        """
        super().__init__(**kwargs)
        self.text = text
        self._styles = TextStyles()

    def _data(self) -> dict:
        """Get the data representation of the text snip."""
        return {"text": self.text}

    def _view(self):
        """Get the view representation of the text snip."""
        ret = super()._view() or {}

        if self._styles and self._styles.get("font_size") is not None:
            ret["size"] = self._styles.get("font_size")

        if self._styles and self._styles.get("font_family") is not None:
            ret["font"] = self._styles.get("font_family")

        if self._styles and self._styles.get("font_color") is not None:
            ret["colour"] = self._styles.get("font_color")

        if self._styles and self._styles.get("line_height") is not None:
            ret["lheight"] = self._styles.get("line_height")

        if self._styles and self._styles.get("line_wrap") is not None:
            ret["wrap"] = self._styles.get("line_wrap")

        return ret if ret != {} else None

    @property
    def size(self) -> tuple[float, float]:
        """Get the bounding box of the text.

        Returns
        -------
        Bounds
            A tuple of floats [width, height]
        """
        return _get_text_size(
            self.text,
            self.font_family,
            self.font_size,
            self.line_wrap,
            self.line_height,
        )

    # ---------------------------------------------------------------------------- #
    #                          Some helpers for the styles                         #
    # ---------------------------------------------------------------------------- #

    @property
    def font_size(self) -> int:
        """Get the font size."""
        return self._styles.get("font_size", 12)

    @font_size.setter
    def font_size(self, value: int):
        """Set the font size."""
        self._styles["font_size"] = value

    @property
    def font_family(self) -> str:
        """Get the font family."""
        return self._styles.get("font_family", "Arial")

    @font_family.setter
    def font_family(self, value: str):
        """Set the font family."""
        self._styles["font_family"] = value

    @property
    def font_color(self) -> str:
        """Get the font color."""
        return self._styles.get("font_color", "black")

    @font_color.setter
    def font_color(self, value: str):
        """Set the font color."""
        self._styles["font_color"] = value

    @property
    def line_height(self) -> float:
        """Get the line height."""
        return self._styles.get("line_height", 1.25)

    @line_height.setter
    def line_height(self, value: float):
        """Set the line height."""
        self._styles["line_height"] = value

    @property
    def line_wrap(self) -> int:
        """Get the line wrap in pixels."""
        return self._styles.get("line_wrap", 400)

    @line_wrap.setter
    def line_wrap(self, value: int):
        """Set the line wrap in pixels.

        If -1, the text will not wrap.
        """
        self._styles["line_wrap"] = value


from PIL import Image, ImageDraw

""" The text bound calculation are mirrored from the typescript
implementation in the frontend. And they match pretty good
even thought the font rendering uses a different backend.

See test_text.py for the tests.
"""


def _get_text_size(
    text: str, font_family: str, font_size: int, wrap: float, line_height: float
) -> tuple:
    # Split text at newlines

    font = __load_font(font_family, font_size)

    img = Image.new("RGB", (1, 1), color="white")
    draw = ImageDraw.Draw(img)

    lines: list[str] = []
    for line in text.split("\n"):
        lines.extend(__wrap_text(line, wrap, font, draw))

    maxW: float = 0
    for line in lines:
        # Get the size of the text
        size = draw.textlength(
            line,
            font=font,
        )

        maxW = max(maxW, size)

    return (maxW, len(lines) * font.size * line_height)


@cache
def __load_font(font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
    """Load a font from the filesystem or deployment.

    Try to load the font from the filesystem first if it exists.
    If it does not exist, try to load the font from the deployment.

    Parameters
    ----------
    font_family : str
        The font family to load.
    font_size : int
        The font size to load.

    Returns
    -------
    ImageFont
        The PIL ImageFont object.

    """
    try:
        return ImageFont.truetype(
            font_family,
            font_size * 2.35,
        )
    except OSError as e:
        log.debug(f"Error loading font {font_family}: {e}")

    # Fallback to deployment
    try:
        font_bytes = get_font_from_deployment(font_family)
        return ImageFont.truetype(font_bytes, font_size * 2.35)
    except Exception as e:
        log.error(f"Error loading font {font_family}: {e}")

    raise ValueError(
        f"Error loading font {font_family}! Try another font or install the font locally."
    )


def __wrap_text(
    text: str,
    maxWidth: float,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    draw: Optional[ImageDraw.ImageDraw] = None,
) -> list[str]:
    """Wrap lines of text to fit within a certain width.

    Expects text without newlines !
    """
    if maxWidth == -1:
        return [text]

    text = text.replace("\t", "        ")

    if draw is None:
        img = Image.new("RGB", (1, 1), color="white")
        draw = ImageDraw.Draw(img)

    width: float = 0
    splits = []
    for i, char in enumerate(text):
        char_width = draw.textlength(char, font=font)
        width += char_width
        if width >= maxWidth:
            splits.append(i)
            width = char_width

    # Split the text
    lines = []
    start = 0
    for split in splits:
        lines.append(text[start:split])
        start = split

    if start < len(text):
        lines.append(text[start:])

    return lines
