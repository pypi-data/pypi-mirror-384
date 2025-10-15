import pytest
from snip.snippets.link import LinkSnip
from snip.snippets.base import BaseSnip


# Mock data for testing
class MockData:
    pass


class MockSnip(BaseSnip[MockData, None]):
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


class TestLinkSnip:
    @pytest.fixture
    def snip(self):
        return LinkSnip(
            snip=MockSnip(book_id=1, type="mock_type"), href="http://example.com"
        )

    def test_init(self, snip):
        assert snip.snip.book_id == 1
        assert snip.snip.type == "mock_type"
        assert snip.href == "http://example.com"

    def test_data(self, snip):
        data = snip._data()
        print(data)
        assert data["snip"]["book_id"] == 1
        assert data["snip"]["type"] == "mock_type"
        assert data["href"] == "http://example.com"

    def test_size(self, snip):
        assert snip.size == (10, 20)

    def test_inner(self, snip):
        assert isinstance(snip.inner, MockSnip)

    def test_x(self, snip):
        snip.x = 3
        assert snip.snip.x == 3
        assert snip.x == snip.snip.x

    def test_y(self, snip):
        snip.y = 4
        assert snip.snip.y == 4
        assert snip.y == snip.snip.y

    def test_width(self, snip):
        # See hardcoded above
        assert snip.width == 10

    def test_height(self, snip):
        # See hardcoded above
        assert snip.height == 20

    def test_rotation(self, snip):
        snip.rotation = 90
        assert snip.snip.rotation == 90

    def test_mirror(self, snip):
        snip.mirror = True
        assert snip.snip.mirror == True

    def test_bounding_box(self, snip):
        assert snip.bounding_box == (0, 0, 10, 20)

    def test_getattribute(self, snip):
        with pytest.raises(AttributeError):
            snip.non_existent_attribute

    def test_icon_style(self, snip):
        assert snip.icon_style == {"pos_x": "right", "pos_y": "top"}

    def test_view(self, snip):
        snip.icon_style = {"pos_x": "left", "pos_y": "bottom"}
        view = snip._view()
        assert view["icon_pos_x"] == "left"
        assert view["icon_pos_y"] == "bottom"
