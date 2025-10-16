import io

import pytest
from PIL import Image

from piltext.font_manager import FontManager
from piltext.image_squares import ImageSquares


def test_image_squares_basic():
    font_manager = FontManager()
    squares = ImageSquares(
        percentage=0.75, font_manager=font_manager, size=200, max_squares=100
    )
    img = squares.render()
    assert isinstance(img, Image.Image)
    # Image dimensions should match our calculations
    # We can't assert exact size since it depends on calculations in the render method
    assert img.width > 0
    assert img.height > 0
    # Save to bytes to ensure image is valid
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    assert buf.tell() > 0


def test_image_squares_zero_and_full():
    font_manager = FontManager()
    squares0 = ImageSquares(
        percentage=0.0, font_manager=font_manager, size=100, max_squares=25
    )
    img0 = squares0.render()
    squares1 = ImageSquares(
        percentage=1.0, font_manager=font_manager, size=100, max_squares=25
    )
    img1 = squares1.render()
    assert img0.width > 0
    assert img0.height > 0
    assert img1.width > 0
    assert img1.height > 0


@pytest.mark.parametrize("pct", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_image_squares_various_percentages(pct):
    font_manager = FontManager()
    squares = ImageSquares(
        percentage=pct, font_manager=font_manager, size=120, max_squares=16
    )
    img = squares.render()
    assert isinstance(img, Image.Image)
    assert img.width > 0
    assert img.height > 0


def test_image_squares_partial():
    """Test that partial squares are rendered correctly."""
    font_manager = FontManager()
    # Test with partial square (20.5 squares out of 100)
    squares = ImageSquares(
        percentage=0.205,
        font_manager=font_manager,
        max_squares=100,
        size=200,
        show_partial=True,
    )
    img = squares.render()
    assert isinstance(img, Image.Image)

    # Test with partial squares disabled
    squares_no_partial = ImageSquares(
        percentage=0.205,
        font_manager=font_manager,
        max_squares=100,
        size=200,
        show_partial=False,
    )
    img_no_partial = squares_no_partial.render()
    assert isinstance(img_no_partial, Image.Image)


def test_image_squares_custom_rows_columns():
    """Test specifying custom rows and columns."""
    font_manager = FontManager()

    # Specified rows only
    squares_rows = ImageSquares(
        percentage=0.5,
        font_manager=font_manager,
        max_squares=20,
        rows=4,
        size=150,
    )
    img_rows = squares_rows.render()
    assert isinstance(img_rows, Image.Image)
    assert squares_rows.rows == 4
    assert squares_rows.columns == 5  # 20/4 = 5

    # Specified columns only
    squares_cols = ImageSquares(
        percentage=0.5,
        font_manager=font_manager,
        max_squares=20,
        columns=5,
        size=150,
    )
    img_cols = squares_cols.render()
    assert isinstance(img_cols, Image.Image)
    assert squares_cols.rows == 4  # 20/5 = 4
    assert squares_cols.columns == 5

    # Specified both rows and columns
    squares_both = ImageSquares(
        percentage=0.5,
        font_manager=font_manager,
        max_squares=20,
        rows=5,
        columns=5,
        size=150,
    )
    img_both = squares_both.render()
    assert isinstance(img_both, Image.Image)
    assert squares_both.rows == 5
    assert squares_both.columns == 5
