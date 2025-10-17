from __future__ import annotations

from typing import Generic, Literal, TypedDict, TypeVar

from snip.snippets.base import BaseSnip

S = TypeVar("S", bound=BaseSnip)


class LinkSnip(BaseSnip[dict, dict], Generic[S]):
    """Test link snip."""

    type = "link"

    def __init__(self, snip: S, href: str, **kwargs):
        super().__init__(**kwargs)
        self.snip = snip
        self.href = href

    snip: S
    href: str

    def _data(self) -> dict:
        return {"snip": self.snip.as_json(), "href": self.href}

    @property
    def size(self):
        """The size of the snip.

        Returns the size of the nested snip.
        """
        return self.snip.size

    @property
    def inner(self) -> S:
        """Get the inner snip."""
        return self.snip

    # ---------------------------------------------------------------------------- #
    #                              Overwrite defaults                              #
    # ---------------------------------------------------------------------------- #

    @property
    def x(self):
        """The x-coordinate of the snip.

        Returns the x-coordinate of the nested snip.
        """
        return self.snip.x

    @x.setter
    def x(self, value):
        """Set the x-coordinate of the snip.

        Sets the x-coordinate of the nested snip.
        """
        self.snip.x = value

    @property
    def y(self):
        """The y-coordinate of the snip.

        Returns the y-coordinate of the nested snip.
        """
        return self.snip.y

    @y.setter
    def y(self, value):
        """Set the y-coordinate of the snip.

        Sets the y-coordinate of the nested snip.
        """
        self.snip.y = value

    @property
    def width(self):
        """The width of the snip.

        Returns the width of the nested snip.
        """
        return self.snip.width

    @property
    def height(self):
        """The height of the snip.

        Returns the height of the nested snip.
        """
        return self.snip.height

    @property
    def rotation(self):
        """The rotation of the snip.

        Returns the rotation of the nested snip.
        """
        return self.snip.rotation

    @rotation.setter
    def rotation(self, value):
        """Set the rotation of the snip.

        Sets the rotation of the nested snip.
        """
        self.snip.rotation = value

    @property
    def mirror(self):
        """The mirror of the snip.

        Returns the mirror of the nested snip.
        """
        return self.snip.mirror

    @mirror.setter
    def mirror(self, value):
        """Set the mirror of the snip.

        Sets the mirror of the nested snip.
        """
        self.snip.mirror = value

    @property
    def bounding_box(self):
        """The bounding box of the snip.

        Returns the bounding box of the nested snip.
        """
        return self.snip.bounding_box

    def __getattribute__(self, name: str):
        """Get an attribute of the snip.

        If it is not defined try to get it from the nested snip.
        """
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            # Handle the case where the attribute is not defined
            try:
                nested_snip = object.__getattribute__(self, "snip")
                return nested_snip.__getattribute__(name)
            except AttributeError:
                raise AttributeError(
                    f"'{self.__class__.__name__}' & '{self.snip.__class__.__name__}' object has no attribute '{name}'"
                )

    # ---------------------------------------------------------------------------- #
    #                                  Icon styles                                 #
    # ---------------------------------------------------------------------------- #

    icon_style: IconStyle = {"pos_x": "right", "pos_y": "top"}

    def _view(self):
        ret = super()._view() or {}

        if self.icon_style:
            ret["icon_pos_x"] = self.icon_style["pos_x"]
            ret["icon_pos_y"] = self.icon_style["pos_y"]

        return ret if ret != {} else None


class IconStyle(TypedDict):
    """Icon style.

    Defines the position of the icon.
    """

    pos_x: float | Literal["right", "left", "center"]
    pos_y: float | Literal["top", "bottom", "center"]
