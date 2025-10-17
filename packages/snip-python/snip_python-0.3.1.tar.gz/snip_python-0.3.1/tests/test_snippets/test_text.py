import pytest
import json
import os


from snip.api.snippets import _parse_font
from snip.snippets.text import TextSnip

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def textbounds():
    # Load the textbounds.json file
    with open(dir_path + "/textbounds.json", "r") as f:
        return json.load(f)


class TestTextSnip:
    def test_init(self):
        snip = TextSnip(book_id=1, text="Hello World")
        assert snip.book_id == 1
        assert snip.text == "Hello World"

    def test_as_json(self):
        snip = TextSnip(book_id=1, text="Hello World")
        TextSnip._get_schema = lambda x: None  # type: ignore

        # Default values
        json_data = snip.as_json(validate=False)
        assert json_data["book_id"] == 1
        assert json_data["type"] == "text"

        assert isinstance(json_data["data"], dict)
        assert json_data["data"]["text"] == "Hello World"

        assert json_data.get("view") == None

        # Set values
        snip.font_size = 14
        snip.font_family = "Times"
        snip.font_color = "red"
        snip.line_height = 1.5
        snip.line_wrap = 60

        json_data = snip.as_json(validate=False)
        assert json_data["book_id"] == 1
        assert json_data["type"] == "text"
        assert json_data["data"]["text"] == "Hello World"
        assert json_data["view"]["size"] == 14
        assert json_data["view"]["font"] == "Times"
        assert json_data["view"]["colour"] == "red"
        assert json_data["view"]["lheight"] == 1.5
        assert json_data["view"]["wrap"] == 60

    def test_styles(self):
        snip = TextSnip(book_id=1, text="Hello World")

        # Check default values
        assert snip.font_size == 12
        assert snip.font_family == "Arial"
        assert snip.font_color == "black"
        assert snip.line_height == 1.25
        assert snip.line_wrap == 400

        # Check setting values
        snip.font_size = 14
        snip.font_family = "Times"
        snip.font_color = "red"
        snip.line_height = 1.5
        snip.line_wrap = 500

        assert snip.font_size == 14
        assert snip.font_family == "Times"
        assert snip.font_color == "red"
        assert snip.line_height == 1.5
        assert snip.line_wrap == 500

    def test_text_bounds(self, textbounds: list[dict], monkeypatch):
        """Test that the bounding box is consistent between the
        nodejs (skia) and python implementation.

        We basically just want the width and height to match!

        See textbounds.json for reference.

        """
        monkeypatch.setattr("snip.snippets.text.get_font_from_deployment", get_font)

        for tb in textbounds:
            text = tb["text"]
            font_family = tb["fontFamily"]
            font_size = tb["fontSize"]
            size_ref = tb["bounds"]

            # Create a new text snip
            snip = TextSnip(text=text)
            snip.font_size = font_size
            snip.font_family = font_family

            # Get the bounding box
            size = snip.size

            # Check the width and height within a tolerance
            tol = 1  # 1px
            assert abs(size[0] - size_ref[0]) < tol
            assert abs(size[1] - size_ref[1]) < tol

            # 180deg rotation
            snip.rotation = 180
            bounds = snip.bounding_box

            assert abs(size_ref[0] - bounds[2]) < tol
            assert abs(size_ref[1] - bounds[3]) < tol

            # 90deg rotation
            snip.rotation = 90
            bounds = snip.bounding_box

            assert abs(size_ref[0] - (bounds[3] - bounds[1])) < tol
            assert abs(size_ref[1] - (bounds[2] - bounds[0])) < tol


def get_font(font: str, **kwargs):
    """Get a PIL ImageFont object for the given font and size.

    Parameters
    ----------
    font : str
        The font to use.
    kwargs : Any
        Additional keyword arguments to pass to the ImageFont.truetype function.

    Returns
    -------
    ImageFont
        The PIL ImageFont object.
    """
    import io

    # Load from file

    font = _parse_font(font)

    font_dir = dir_path + "../../../../../assets/fonts"

    print(os.path.abspath(font_dir))

    with open(os.path.abspath(font_dir + "/" + font), "rb") as f:
        return io.BytesIO(f.read())
