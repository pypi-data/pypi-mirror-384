import numpy as np

from .base import BaseSnip


class ArraySnip(BaseSnip[dict, dict]):
    """Array snip class.

    Allows to combine multiple snippets into an array.
    """

    type = "array"

    snippets: list[BaseSnip]

    def __init__(self, snippets: list[BaseSnip], **kwargs):
        """Create an array snip from a list of snippets.

        Parameters
        ----------
        snippets : list[BaseSnip]
            The snippets to combine into an array. Accepts any type of snippet.
        kwargs : Any
            Additional keyword arguments passed :class:`snip.snippets.base.BaseSnip.__init__`.
        """
        super().__init__(**kwargs)
        self.snippets = snippets

    def _data(self):
        return {"snips": [snip.as_json() for snip in self.snippets]}

    @property
    def size(self):
        """Get the size of the array.

        This is not implemented for ArraySnip. Use bounding_box instead!
        """
        raise NotImplementedError(
            "Size not implemented for ArraySnip. Use bounding_box instead!"
        )

    @property
    def bounding_box(self):
        """Get the bounding box of the array.

        At the moment rotation and other transformations are not considered.

        Returns
        -------
        Bounds
            A tuple of floats [left, top, right, bottom]
        """
        x0, y0, x1, y1 = np.inf, np.inf, -np.inf, -np.inf
        for snip in self.snippets:
            bb = snip.bounding_box
            x0 = min(x0, bb[0])
            y0 = min(y0, bb[1])
            x1 = max(x1, bb[2])
            y1 = max(y1, bb[3])

        return (x0, y0, x1, y1)
