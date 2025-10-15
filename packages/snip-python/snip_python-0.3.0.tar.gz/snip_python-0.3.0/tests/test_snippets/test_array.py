from PIL import Image
import pytest
from snip.snippets.array import ArraySnip
from snip.snippets.image import ImageSnip
from snip.snippets.text import TextSnip

from test_text import get_font


class TestArraySnip:
    text = TextSnip(text="Hello World", book_id=1)
    image = ImageSnip.from_pil(Image.new("RGB", (200, 1000)), book_id=1)

    def test_create(self):
        array = ArraySnip([self.text, self.image])

        assert array.snippets == [self.text, self.image]

    def test_as_json(self):
        array = ArraySnip(book_id=1, snippets=[self.text, self.image])
        json_data = array.as_json(validate=False)

        assert json_data["book_id"] == 1
        assert json_data["type"] == "array"
        assert isinstance(json_data["data"], dict)
        assert json_data["data"]["snips"] == [self.text.as_json(), self.image.as_json()]
        assert json_data.get("view") == None

    def test_size(self):
        array = ArraySnip(book_id=1, snippets=[self.text, self.image])
        with pytest.raises(NotImplementedError):
            array.size

    def test_boundings(self, monkeypatch):
        monkeypatch.setattr("snip.snippets.text.get_font_from_deployment", get_font)

        array = ArraySnip(book_id=1, snippets=[self.text, self.image])
        assert array.bounding_box == (0, 0, 200, 1000)
