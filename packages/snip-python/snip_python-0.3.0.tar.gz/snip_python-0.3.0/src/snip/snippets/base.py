"""To implement your own snippets, you can use the BaseSnip class.

This class provides a basic structure for snippets that can be used in the labbook, if you have already created a custom snippet in the (ts) snip package, or you want to extend the functionality of the already existing snippets, you can use the :py:class:`BaseSnip` class as a base class.
"""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from functools import cached_property
from typing import (
    Any,
    Generic,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import nest_asyncio
import numpy as np
from jsonschema import validate as validate_json
from PIL import Image

from ..api import DEFAULT_DEPLOYMENT_URL
from ..api.exceptions import AuthenticationException
from ..api.schemas import get_schema
from ..api.snippets import get_snip_preview, upload_snip
from ..logger import log
from ..token import BookToken, Token
from ..token.storage import get_token_by_deployment, get_tokens_by_book_and_deployment

try:
    from IPython.display import clear_output, display
except ImportError:  # pragma: no cover
    log.debug("IPython not found. Disabling IPython display.")
    get_ipython = lambda: None
    clear_output = lambda *args, **kwargs: None
    display = lambda *args, **kwargs: None


PREVIEW_IMAGE_WIDTH = int(os.getenv("SNIP_PREVIEW_IMAGE_WIDTH", 700))


Data = TypeVar("Data")
View = TypeVar("View")


class BaseSnip(ABC, Generic[Data, View]):
    """Basic Snip class.

    You may use this class to create new snippets that can be used in the labbook, they should
    have an associated schema that defines the structure of the snippet and
    a view that defines how the snippet is displayed. And every snip should mirror some
    of the functionality of the traditional snip classes in the (ts) snip package.
    """

    book_id: Optional[int]
    """ The identifier of the book the snippet belongs to"""

    deployment: Optional[str]
    """The deployment URL of the snippet"""

    type: str = "unknown"
    """ The type identifier of the snippet e.g. 'text', 'image' etc."""

    def __init__(self, book_id: Optional[int] = None, deployment: Optional[str] = None):
        """Create a new snippet.

        Parameters
        ----------
        book_id : int, optional
            The book_id of the snippet. Defaults to None. If None, the snippet book_id is derived
            from the token.
        deployment : str, optional
            The deployment URL of the snippet. Defaults to None. If None, the deployment is set to the default deployment.
        """
        if (self.type is None) or (self.type == ""):
            raise ValueError("The snippet type must be set and not empty!")

        self.book_id = book_id
        self.deployment = DEFAULT_DEPLOYMENT_URL if deployment is None else deployment

        self.__pos = None
        self.__rotation = None
        self.__mirror = None

    @abstractmethod
    def _data(self) -> Data:  # noqa
        """Content of the snippet, should be serializable to json and match the schema."""
        raise NotImplementedError

    def _view(self) -> Optional[View]:
        """Visual representation in dict format.

        The expected format is defined by the json schema.
        """
        # Parse all optional view parameters
        ret = {}
        if self.pos is not None:
            ret["x"] = self.pos[0]
            ret["y"] = self.pos[1]
        if self.rotation is not None and self.rotation != 0:
            ret["rot"] = self.rotation
        if self.mirror is not None and self.mirror:
            ret["mirror"] = True
        if ret and ret != {}:
            return ret  # type: ignore
        return None

    __pos: Optional[Tuple[float, float]]

    @property
    def pos(self) -> Optional[Tuple[float, float]]:
        """Position of the snippet on a page.

        Returns none if the position is not set yet.
        """
        return self.__pos

    @pos.setter
    def pos(self, value: Union[list[float], Tuple[float, float]]):
        if isinstance(value, list):
            self.__pos = (value[0], value[1])
        else:
            self.__pos = value

    @property
    def x(self):
        """Vertical position of the snippet.

        Returns none if the position is not set yet.
        """
        return self.__pos[0] if self.__pos is not None else None

    @x.setter
    def x(self, value: float):
        if self.__pos is None:
            self.__pos = (value, 0)
        else:
            self.__pos = (value, self.__pos[1])

    @property
    def y(self):
        """Horizontal position of the snippet.

        Returns none if the position is not set yet.
        """
        return self.__pos[1] if self.__pos is not None else None

    @y.setter
    def y(self, value: float):
        if self.__pos is None:
            self.__pos = (0, value)
        else:
            self.__pos = (self.__pos[0], value)

    @property
    def width(self):
        """Width of the snippet.

        Ignoring rotation and mirroring. For the actual size of the snippet on the page, use the :py:attr:`bounding_box` property.
        """
        return self.size[0]

    @property
    def height(self):
        """Height of the snippet.

        Ignoring rotation and mirroring. For the actual size of the snippet on the page, use the :py:attr:`bounding_box` property.
        """
        return self.size[1]

    @property
    @abstractmethod
    def size(self) -> Tuple[float, float]:
        """Size of the snippet.

        The width and height of the snippet, ignoring rotation and mirroring. For
        the actual size of the snippet on the page, use the :py:attr:`bounding_box` property.

        Returns
        -------
        Tuple[float, float]
            The width and height of the snippet.
        """
        raise NotImplementedError

    __rotation: Optional[float]

    @property
    def rotation(self):
        """Rotation of the snippet on a page in degrees.

        The rotation origin is the center of the snippet and is
        defined in degrees.
        """
        return self.__rotation

    @rotation.setter
    def rotation(self, value: float):
        self.__rotation = value % 360

    __mirror: Optional[bool]

    @property
    def mirror(self):
        """Mirror the snippet on the x axis."""
        return self.__mirror

    @mirror.setter
    def mirror(self, value: bool):
        self.__mirror = value

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """Bounding box of the snippet on a page.

        This is the actual size of the snippet on the page, including potential rotation and mirroring.

        Returns
        -------
        Tuple[float, float, float, float]
            The left, top, right, bottom coordinates of the snippet.
        """
        (width, height) = self.size
        (x, y) = self.pos if self.pos is not None else (0, 0)

        # Check if no need to apply transformation
        if (self.rotation is None or self.rotation % 360 == 0) and (
            self.mirror is None or not self.mirror
        ):
            return (x, y, x + width, y + height)

        # Create transformation matrix
        transformation_matrix = np.eye(2)
        if self.rotation is not None and self.rotation % 180 != 0:
            theta = np.radians(self.rotation)
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)
            transformation_matrix = np.array(
                [
                    [cos_theta, -sin_theta],
                    [sin_theta, cos_theta],
                ]
            )

        if self.mirror is not None and self.mirror:
            transformation_matrix = (
                np.array(
                    [
                        [-1, 0],
                        [0, 1],
                    ]
                )
                @ transformation_matrix
            )

        # Apply transform to center of snippet
        corners = np.array(
            [
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height],
            ]
        )
        center = np.array([x + width / 2, y + height / 2])
        corners_origin = corners - center  # center of snippet

        corners_transformed = corners_origin @ transformation_matrix.T + center

        # Find the new bounding box
        min_x = min(corners_transformed[:, 0])
        max_x = max(corners_transformed[:, 0])
        min_y = min(corners_transformed[:, 1])
        max_y = max(corners_transformed[:, 1])
        return (min_x, min_y, max_x, max_y)

    @cached_property
    def schema(self) -> Optional[dict]:
        """Schema to validate the snippet.

        The schema is used to validate the snippet and should be
        a valid :py:class:`jsonschema.Draft202012Validator` schema.

        Returns
        -------
        schema
            The schema for this snippet class if available. If none is available, None is returned and the schema functionality is disabled.
        """
        return self._get_schema()

    def as_json(self, validate=True) -> dict:
        """Return the snippet as a dictionary in basic snippet json format.

        Returns a dict in the basic snippet structure.

        .. code-block:: json

            {
                "book_id": 123
                "type": "text"
                "data": {}
                "view": {}
            }


        If the schema is set in the class it is used
        to validate the snippet data before returning it.

        Parameters
        ----------
        validate : bool, optional
            If True, the snippet is validated against the schema.
            Defaults to True.

        Raises
        ------
        :py:class:`jsonschema.ValidationError`
            If the snippet does not match the schema.
        """
        data = {
            "book_id": self.book_id if self.book_id is not None else -1,
            "type": self.type,
            "data": self._data(),
        }
        view = self._view()
        if view is not None:
            data["view"] = view

        if self.schema is not None and validate:
            validate_json(data, self.schema)

        return data

    def upload(
        self,
        book_id: Optional[int] = None,
        token: Optional[BookToken] = None,
        validate=True,
        **kwargs,
    ):
        """
        Upload the snippet to the labbook.

        This method uploads this snippet to a labbok given the snippets
        book_id and deployment url.

        If no token is provided, the token is inferred from the book_id and deployment.

        Parameters
        ----------
        book_id : int, optional
            The book_id of the snippet. Defaults to None. If None, the snippet book_id is derived
        token : Token
            The token to use for the request. If None, the token gets inferred if possible.
        validate : bool, optional
            Weather to validate the snippet before uploading. Defaults to True.
        **kwargs: Any
            Additional keyword arguments to pass to the requests function.
        """
        book_id = self.book_id if book_id is None else book_id

        if token is None and book_id is None:
            raise ValueError(
                "No book_id or token provided! Please provide one or set the book_id on the snippet."
            )
        if token is None and book_id is not None:
            tokens, sources = get_tokens_by_book_and_deployment(
                book_id, self.deployment
            )
            if len(tokens) > 1:
                log.info(
                    f"Found {len(tokens)} tokens! Using {tokens[0].name} from {sources[0]}"
                )
            token = tokens[0] if len(tokens) > 0 else None

        if token is None:
            raise AuthenticationException(
                "No token provided and no token found for this snip using its book_id. Please provide a token manually, add one in an .sniprc file or use your keyring."
            )

        json = self.as_json(validate=validate)
        res = upload_snip(json, token, **kwargs)

        if "ids" in res or "id" in res:
            log.info("Snippet uploaded successfully!")

        return res

    def preview(self, token: Optional[Token] = None, **kwargs) -> Optional[Image.Image]:
        """Generate a snippet preview.

        This requests a server side rendering of the snippet and returns the preview image.

        Returns
        -------
        token : Token
            The token to use for the request. If None, the token gets inferred if possible.
        **kwargs: Any
            Additional keyword arguments to pass to the requests function.

        """
        if token is None:
            tokens, sources = get_token_by_deployment(self.deployment)
            if len(tokens) > 1:
                log.debug(
                    f"Found {len(tokens)} tokens! Using {tokens[0].name} from {sources[0]}"
                )
                token = tokens[0]
            token = tokens[0] if len(tokens) > 0 else None

        if token is None:
            raise AuthenticationException(
                "No token provided and no token found for this snip using its deployment. Please provide a token manually, add one in an .sniprc file or use your keyring."
            )

        # Parse data
        data = self.as_json()

        nest_asyncio.apply()
        loop = asyncio.get_event_loop()

        req = loop.create_task(_snip_preview(data, token, **kwargs))
        indicator = loop.create_task(
            _loading_indicator_until(req),
        )

        # Show loading indicator until request is done
        a = loop.run_until_complete(asyncio.gather(req, indicator))

        img = a[0]
        if isinstance(img, Exception):
            raise img

        # Resize image
        if img.width > PREVIEW_IMAGE_WIDTH:
            img = img.resize(
                (PREVIEW_IMAGE_WIDTH, int(PREVIEW_IMAGE_WIDTH / img.width * img.height))
            )

        return img

    def _get_schema(self) -> Optional[dict]:
        """Get the schema for the snippet from the deployment."""
        try:
            schema = get_schema(self.type, deployment=self.deployment)
            return schema
        except Exception as e:
            log.debug(f"Could not get schema for image snip: {e}")
            return None

    def _ipython_display_(self):
        """Display the snippet in IPython."""
        try:
            img = self.preview()
        except AuthenticationException as e:
            log.warning(f"Cant display snip preview! {e}")
            return
        display(img)

    __slots__ = ["book_id", "deployment", "__pos", "__rotation", "__mirror"]


async def _snip_preview(
    data: dict, token: Token, **kwargs
) -> Union[Image.Image, Exception]:
    try:
        return await asyncio.to_thread(get_snip_preview, data, token, **kwargs)
    except Exception as e:
        return e


async def _loading_indicator_until(task: asyncio.Task[Any]):
    spinner = ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱", "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"]
    i = 0
    # Short initial delay to prevent flickering
    await asyncio.sleep(0.2)
    while not task.done():
        await asyncio.sleep(0.1)
        clear_output(wait=True)
        display("Loading " + spinner[i % len(spinner)])
        i += 1
    clear_output(wait=False)

    return
