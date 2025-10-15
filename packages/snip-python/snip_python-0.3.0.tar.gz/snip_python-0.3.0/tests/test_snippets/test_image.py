# Mock data for testing
import os
from snip.snippets.image import ImageSnip

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestImageSnip:
    def test_from_pil(self):
        from PIL import Image

        img = Image.new("RGB", (100, 100))

        snip = ImageSnip.from_pil(img, book_id=1)

        assert snip.book_id == 1
        assert snip.image == img

    def test_from_array(self):
        import numpy as np

        array = np.random.rand(100, 100, 3)
        snip = ImageSnip.from_array(array, mode="RGB", book_id=1)
        assert snip.book_id == 1

    def test_from_matplotlib(self):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3, 4])
        snip = ImageSnip.from_matplotlib(fig, book_id=1)
        assert snip.book_id == 1
        plt.close(fig)

    def test_from_path(self):
        snip = ImageSnip.from_path(dir_path + "/test.png", book_id=1)
        assert snip.book_id == 1

    def test_as_json(self):
        from PIL import Image

        img = Image.new("RGB", (100, 100))

        snip = ImageSnip(book_id=1, image=img)
        ImageSnip._get_schema = lambda x: None  # type: ignore

        json_data = snip.as_json(validate=False)
        assert json_data["book_id"] == 1
        assert json_data["type"] == "image"
        assert isinstance(json_data["data"], dict)
        assert json_data.get("view") is None
        assert json_data["data"]["blob"] is not None
        assert json_data["data"]["blob"]["mime"] == "image/png"
        assert json_data["data"]["blob"]["data"] is not None

    def test_width_height_scale(self):
        from PIL import Image

        img = Image.new("RGB", (100, 200))
        snip = ImageSnip(book_id=1, image=img)
        assert snip.size[0] == 100

        # Check bigg image
        img = Image.new("RGB", (2000, 2000))

        snip = ImageSnip(book_id=1, image=img)
        assert snip.size[0] == 1400
        assert snip.size[1] == 1400

        # Test set width height
        snip.set_width(200)
        assert snip.size[0] == 200
        assert snip.size[1] == 200

        snip.set_height(300)
        assert snip.size[0] == 300
        assert snip.size[1] == 300

        snip.set_width(200, keep_ratio=False)
        assert snip.size[0] == 200
        assert snip.size[1] == 300

        snip.set_height(400, keep_ratio=False)
        assert snip.size[0] == 200
        assert snip.size[1] == 400

        # Scale
        snip.scale(0.5)
        assert snip.size[0] == 100
        assert snip.size[1] == 200
