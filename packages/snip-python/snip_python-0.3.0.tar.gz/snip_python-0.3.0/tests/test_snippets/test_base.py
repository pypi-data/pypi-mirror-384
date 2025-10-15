import pytest
from PIL import Image
from snip.api.exceptions import AuthenticationException
from snip.snippets.base import BaseSnip
from snip.token.token import BookToken


# Mock data for testing
class MockData:
    pass


class MockView:
    pass


class MockSnipMinimal(BaseSnip[MockData, None]):
    def __init__(self, book_id: int, type: str):
        self.type = type
        super().__init__(book_id)

    def _data(self) -> MockData:
        return MockData()

    def _get_schema(self):
        return None

    @property
    def size(self):
        return (10, 20)


class TestBaseSnip:
    @pytest.fixture
    def snip(self):
        return MockSnipMinimal(book_id=1, type="test_type")

    def test_init(self, snip):
        assert snip.book_id == 1
        assert snip.type == "test_type"

        # raise on empty type
        with pytest.raises(ValueError):
            MockSnipMinimal(book_id=1, type="")

    def test_data(self, snip):
        assert isinstance(snip._data(), MockData)

    def test_view(self, snip):
        assert snip._view() is None

        # Set pos
        snip.pos = (1, 2)
        expected = {"x": 1, "y": 2}
        assert snip._view() == expected

        # Set rotation
        snip.rotation = 90
        expected["rot"] = 90
        assert snip._view() == expected

        # Set mirroring
        snip.mirroring = False
        assert snip._view() == expected

        snip.mirror = True
        expected["mirror"] = True
        assert snip._view() == expected

    def test_pos(self, snip):
        assert snip.pos == None
        assert snip.x == None
        assert snip.y == None

        snip.pos = (1, 2)
        assert snip.pos == (1, 2)
        assert snip.x == 1
        assert snip.y == 2

        snip.pos = [1, 2]
        assert snip.pos == (1, 2)

        # Test setter
        snip.pos = None
        assert snip.pos == None

        snip.x = 1
        assert snip.pos == (1, 0)
        snip.y = 2
        assert snip.pos == (1, 2)

        snip.pos = None
        assert snip.pos == None

        snip.y = 2
        assert snip.pos == (0, 2)
        snip.x = 1
        assert snip.pos == (1, 2)

    def test_rotation(self, snip):
        assert snip.rotation == None

        snip.rotation = 90
        assert snip.rotation == 90

        snip.rotation = 480
        assert snip.rotation == 120

    def test_mirroring(self, snip):
        assert snip.mirror == None

        snip.mirror = False
        assert snip.mirror == False

        snip.mirror = True
        assert snip.mirror == True

    def test_size(self, snip):
        assert snip.size == (10, 20)
        assert snip.width == 10
        assert snip.height == 20

    def test_bounding_box(self, snip):
        assert snip.bounding_box == (0, 0, 10, 20)

        # With rotation
        snip.rotation = 90
        bb = snip.bounding_box
        assert bb[0] == pytest.approx(-5)
        assert bb[1] == pytest.approx(5)
        assert bb[2] == pytest.approx(15)
        assert bb[3] == pytest.approx(15)

        # With mirroring
        snip.mirror = True
        bb = snip.bounding_box
        assert bb[0] == pytest.approx(-5)
        assert bb[1] == pytest.approx(5)
        assert bb[2] == pytest.approx(15)
        assert bb[3] == pytest.approx(15)

    def test_schema(self, snip):
        assert snip.schema == None

    def test_as_json(self, snip):
        json_data = snip.as_json()
        assert json_data["book_id"] == 1
        assert json_data["type"] == "test_type"
        assert isinstance(json_data["data"], MockData)
        assert json_data.get("view") is None

    def test_upload(self, snip, monkeypatch):
        monkeypatch.setattr(
            "snip.snippets.base.get_tokens_by_book_and_deployment",
            lambda *args, **kwargs: (
                [
                    BookToken(
                        name="test",
                        book_id=1,
                        token="test",
                        deployment_url="https://test.de",
                    ),
                    BookToken(
                        name="test",
                        book_id=2,
                        token="test",
                        deployment_url="https://test.de",
                    ),
                ],
                ["foo", "bar"],
            ),
        )

        monkeypatch.setattr(
            "snip.snippets.base.upload_snip",
            lambda *args, **kwargs: {"ids": [1]},
        )

        snip.upload()

        # Without book_id raise
        snip.book_id = None
        with pytest.raises(ValueError):
            snip.upload()

        # Without available tokens
        snip.book_id = 3
        monkeypatch.setattr(
            "snip.snippets.base.get_tokens_by_book_and_deployment",
            lambda *args, **kwargs: ([], []),
        )
        with pytest.raises(AuthenticationException):
            snip.upload()

    def test_preview(self, snip, monkeypatch):
        monkeypatch.setattr(
            "snip.snippets.base.get_token_by_deployment",
            lambda *args, **kwargs: (
                [
                    BookToken(name="test", book_id=1, token="test"),
                    BookToken(name="test", book_id=2, token="test"),
                ],
                ["foo", "bar"],
            ),
        )

        monkeypatch.setattr(
            "snip.snippets.base.get_snip_preview",
            lambda *args, **kwargs: Image.new("RGB", (2000, 100)),
        )

        snip.preview()

        # Without available tokens
        snip.book_id = 3
        monkeypatch.setattr(
            "snip.snippets.base.get_token_by_deployment",
            lambda *args, **kwargs: ([], []),
        )
        with pytest.raises(AuthenticationException):
            snip.preview()


class MockSnipFull(BaseSnip[MockData, MockView]):
    def __init__(self, book_id: int, type: str):
        self.type = type
        super().__init__(book_id)

    def _data(self) -> MockData:
        return MockData()

    def _view(self) -> MockView:
        return MockView()

    def _get_schema(self):
        return {"type": "object"}

    @property
    def size(self):
        return (10, 10)


class TestBaseFullSnip:
    @pytest.fixture
    def snip(self):
        return MockSnipFull(book_id=1, type="test_type")

    def test_init(self, snip):
        assert snip.book_id == 1
        assert snip.type == "test_type"

        # raise on empty type
        with pytest.raises(ValueError):
            MockSnipFull(book_id=1, type="")

    def test_data(self, snip):
        assert isinstance(snip._data(), MockData)

    def test_view(self, snip):
        assert isinstance(snip._view(), MockView)

    def test_schema(self, snip):
        assert snip.schema == {"type": "object"}

    def test_as_json(self, snip):
        json_data = snip.as_json()
        assert json_data["book_id"] == 1
        assert json_data["type"] == "test_type"
        assert isinstance(json_data["data"], MockData)
        assert isinstance(json_data["view"], MockView)
