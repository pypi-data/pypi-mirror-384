"""Image snip module allows to display images in the labbook."""

from __future__ import annotations

import base64
import importlib.util
import io
from typing import TYPE_CHECKING, Optional, Tuple

from PIL import Image

from .base import BaseSnip

if TYPE_CHECKING:  # pragma: no cover
    try:
        from matplotlib.figure import Figure
    except ImportError:
        pass


class ImageSnip(BaseSnip[dict, dict]):
    """Image snip class.

    Represents an image in the labbook. You may construct an image from
    a matplotlib figure, a PIL image, or a numpy array.

    The default constructor is not meant to be used directly. Instead, use the
    `from_array`, `from_pil`, or `from_matplotlib` constructors.
    """

    type = "image"

    def __init__(self, image: Image.Image, **kwargs):
        """Create an image snip from a PIL image.

        Parameters
        ----------
        image : Image.Image
            The image to display.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.
        """
        super().__init__(**kwargs)
        self.image = image

    @classmethod
    def from_pil(
        cls,
        image: Image.Image,
        **kwargs,
    ) -> ImageSnip:
        """Create an image snip from a PIL image.

        Parameters
        ----------
        image : Image.Image
            The image to display.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.

        Returns
        -------
        ImageSnip
            The image snip.
        """
        return cls(image, **kwargs)

    @classmethod
    def from_path(
        cls,
        path: str,
        **kwargs,
    ) -> ImageSnip:
        """Create an image snip from a file path.

        Parameters
        ----------
        path : str
            The path to the image file.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.

        Returns
        -------
        ImageSnip
            The image snip.
        """
        return cls(Image.open(path), **kwargs)

    @classmethod
    def from_array(
        cls,
        array,
        mode: Optional[str] = None,
        **kwargs,
    ) -> ImageSnip:
        """Create an image snip from a numpy array.

        Parameters
        ----------
        array : Any
            The numpy 3d array to display. The array should be in the format
            (height, width, 3) or (height, width, 4). See `pillow.Image.fromarray`
            for more information on the supported array formats.
        mode: Optional[str]
            Optional mode to use when reading obj. Will be determined from type if None.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.

        Returns
        -------
        ImageSnip
            The image snip.
        """
        return cls(Image.fromarray(array, mode), **kwargs)

    @classmethod
    def from_matplotlib(
        cls,
        figure: Figure,
        savefig_kwargs: Optional[dict] = None,
        **kwargs,
    ) -> ImageSnip:
        """Create an image snip from a matplotlib figure.

        Parameters
        ----------
        figure : matplotlib.figure.Figure
            The figure to display.
        savefig_kwargs : Optional[dict]
            Optional keyword arguments to pass to `figure.savefig`.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.

        Returns
        -------
        ImageSnip
            The image snip.
        """
        available = importlib.util.find_spec("matplotlib")
        if available is None:  # pragma: no cover
            raise ImportError(
                "Matplotlib is required to use this function. Install it via `pip install matplotlib`."
            )

        buf = io.BytesIO()
        if savefig_kwargs is None:
            savefig_kwargs = {}
        figure.savefig(buf, format="png", **savefig_kwargs)
        buf.seek(0)
        return cls(Image.open(buf), **kwargs)

    def _data(self):
        """Return the image data."""
        return {
            "blob": {
                "mime": "image/png",
                "data": self._as_b64(),
                "size": self.image.__sizeof__(),
            }
        }

    __size: Optional[Tuple[float, float]] = None

    @property
    def size(self) -> Tuple[float, float]:
        """Return the width and height of the image."""
        size = self.__size
        if size is None:
            size = (self.image.width, self.image.height)
            if size[0] > 1400:
                size = (1400, int(1400 / size[0] * size[1]))
        return size

    @property
    def width(self):
        """Return the width of the image."""
        return self.size[0]

    @width.setter
    def width(self, width: int):
        self.set_width(width)

    @property
    def height(self):
        """Return the height of the image."""
        return self.size[1]

    @height.setter
    def height(self, height: int):
        self.set_height(height)

    def set_width(self, width: int, keep_ratio: bool = True):
        """Set the width of the image."""
        if keep_ratio:
            self.__size = (width, int(width / self.size[0] * self.size[1]))
        else:
            self.__size = (width, self.size[1])

    def set_height(self, height: int, keep_ratio: bool = True):
        """Set the height of the image."""
        if keep_ratio:
            self.__size = (int(height / self.size[1] * self.size[0]), height)
        else:
            self.__size = (self.size[0], height)

    def scale(self, ratio: float):
        """Scale the image by a given ratio."""
        self.__size = (int(self.size[0] * ratio), int(self.size[1] * ratio))

    def _view(self):
        """Return the image view."""
        ret = super()._view() or {}

        if self.__size is not None:
            ret["width"] = self.width
            ret["height"] = self.height
        return ret if ret != {} else None

    def _as_b64(self):
        buffered = io.BytesIO()
        self.image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
