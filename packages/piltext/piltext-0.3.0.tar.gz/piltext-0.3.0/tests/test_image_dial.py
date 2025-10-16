import io

import pytest
from PIL import Image

from piltext.font_manager import FontManager
from piltext.image_dial import ImageDial


def test_image_dial_basic():
    font_manager = FontManager()
    dial = ImageDial(percentage=0.75, font_manager=font_manager, size=200)
    img = dial.render()
    assert isinstance(img, Image.Image)
    assert img.size == (200, 200)
    # Save to bytes to ensure image is valid
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    assert buf.tell() > 0


def test_image_dial_zero_and_full():
    font_manager = FontManager()
    dial0 = ImageDial(percentage=0.0, font_manager=font_manager, size=100)
    img0 = dial0.render()
    dial1 = ImageDial(percentage=1.0, font_manager=font_manager, size=100)
    img1 = dial1.render()
    assert img0.size == (100, 100)
    assert img1.size == (100, 100)


@pytest.mark.parametrize("pct", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_image_dial_various_percentages(pct):
    font_manager = FontManager()
    dial = ImageDial(percentage=pct, font_manager=font_manager, size=120)
    img = dial.render()
    assert isinstance(img, Image.Image)
    assert img.size == (120, 120)
