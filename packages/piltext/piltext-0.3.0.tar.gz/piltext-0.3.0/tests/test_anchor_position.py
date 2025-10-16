"""Unit tests for anchor position calculation in TextGrid.

This test suite verifies that the _calculate_anchor_position method
correctly interprets PIL's anchor format where:
- First character is horizontal: l=left, m=middle, r=right
- Second character is vertical: t=top, m=middle, b=bottom, s=baseline
"""

import unittest

from piltext import TextGrid


class MockFontManager:
    """Mock FontManager for testing."""

    def __init__(self, *args, **kwargs):
        pass

    def build_font(self, font_name=None):
        return None


class MockImageHandler:
    """Mock ImageHandler for testing."""

    def __init__(self, width, height):
        from PIL import Image

        self.image = Image.new("RGB", (width, height), color="white")


class MockImageDrawer:
    """Mock ImageDrawer for testing."""

    def __init__(self, width, height, font_manager=None):
        self.image_handler = MockImageHandler(width, height)
        self.font_manager = font_manager or MockFontManager()


class TestAnchorPosition(unittest.TestCase):
    """Test anchor position calculations in TextGrid."""

    def setUp(self):
        """Set up test fixtures."""
        font_manager = MockFontManager()
        self.image_drawer = MockImageDrawer(480, 280, font_manager)
        self.grid = TextGrid(4, 4, self.image_drawer)

    def test_anchor_left_top(self):
        """Test anchor='lt' (left-top) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "lt")
        self.assertEqual(result, (10, 20))

    def test_anchor_left_middle(self):
        """Test anchor='lm' (left-middle) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "lm")
        self.assertEqual(result, (10, 50.0))

    def test_anchor_left_bottom(self):
        """Test anchor='lb' (left-bottom) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "lb")
        self.assertEqual(result, (10, 80))

    def test_anchor_left_baseline(self):
        """Test anchor='ls' (left-baseline) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "ls")
        self.assertEqual(result, (10, 80))

    def test_anchor_middle_top(self):
        """Test anchor='mt' (middle-top) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "mt")
        self.assertEqual(result, (55.0, 20))

    def test_anchor_middle_middle(self):
        """Test anchor='mm' (middle-middle) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "mm")
        self.assertEqual(result, (55.0, 50.0))

    def test_anchor_middle_bottom(self):
        """Test anchor='mb' (middle-bottom) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "mb")
        self.assertEqual(result, (55.0, 80))

    def test_anchor_middle_baseline(self):
        """Test anchor='ms' (middle-baseline) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "ms")
        self.assertEqual(result, (55.0, 80))

    def test_anchor_right_top(self):
        """Test anchor='rt' (right-top) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "rt")
        self.assertEqual(result, (100, 20))

    def test_anchor_right_middle(self):
        """Test anchor='rm' (right-middle) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "rm")
        self.assertEqual(result, (100, 50.0))

    def test_anchor_right_bottom(self):
        """Test anchor='rb' (right-bottom) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "rb")
        self.assertEqual(result, (100, 80))

    def test_anchor_right_baseline(self):
        """Test anchor='rs' (right-baseline) positioning."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "rs")
        self.assertEqual(result, (100, 80))

    def test_anchor_default_invalid(self):
        """Test that invalid anchor defaults to 'lt'."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "invalid")
        self.assertEqual(result, (10, 20))

    def test_anchor_too_short(self):
        """Test that anchor strings shorter than 2 chars default to 'lt'."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "l")
        self.assertEqual(result, (10, 20))

    def test_anchor_empty_string(self):
        """Test that empty anchor string defaults to 'lt'."""
        x1, y1, x2, y2 = 10, 20, 100, 80
        result = self.grid._calculate_anchor_position(x1, y1, x2, y2, "")
        self.assertEqual(result, (10, 20))

    def test_anchor_with_grid_cells(self):
        """Test anchor positioning with actual grid cell coordinates."""
        # Grid is 4x4, image is 480x280
        # Each cell is 120x70 pixels
        # Cell (1, 1) spans from (120, 70) to (240, 140)

        # Get cell bounds
        (x1, y1), (x2, y2) = self.grid._grid_to_pixels((1, 1), (1, 1))
        self.assertEqual((x1, y1), (120, 70))
        self.assertEqual((x2, y2), (240, 140))

        # Test various anchors with this cell
        result_lt = self.grid._calculate_anchor_position(x1, y1, x2, y2, "lt")
        self.assertEqual(result_lt, (120, 70))

        result_mm = self.grid._calculate_anchor_position(x1, y1, x2, y2, "mm")
        self.assertEqual(result_mm, (180.0, 105.0))

        result_rb = self.grid._calculate_anchor_position(x1, y1, x2, y2, "rb")
        self.assertEqual(result_rb, (240, 140))

    def test_anchor_with_merged_cells(self):
        """Test anchor positioning with merged cell ranges."""
        # Merge cells (0, 0) to (1, 2) - spans 2 rows, 3 columns
        self.grid.merge((0, 0), (1, 2))

        # Get merged cell bounds
        (x1, y1), (x2, y2) = self.grid._grid_to_pixels((0, 0), (1, 2))
        self.assertEqual((x1, y1), (0, 0))
        self.assertEqual((x2, y2), (360, 140))

        # Test various anchors
        result_lt = self.grid._calculate_anchor_position(x1, y1, x2, y2, "lt")
        self.assertEqual(result_lt, (0, 0))

        result_mm = self.grid._calculate_anchor_position(x1, y1, x2, y2, "mm")
        self.assertEqual(result_mm, (180.0, 70.0))

        result_rb = self.grid._calculate_anchor_position(x1, y1, x2, y2, "rb")
        self.assertEqual(result_rb, (360, 140))

    def test_ticker_yaml_scenario(self):
        """Test the specific scenario from ticker.yaml.

        This tests the bug that was discovered where text with anchor='rb'
        at cell [13,0] in a merge [[13,0], [19,5]] was not rendering.
        The merge should span from row 13-19, columns 0-5.
        """
        # Create a grid matching ticker.yaml: 21 rows x 6 columns, 264x176 image
        font_manager = MockFontManager()
        image_drawer = MockImageDrawer(264, 176, font_manager)
        grid = TextGrid(21, 6, image_drawer, margin_x=1, margin_y=1)

        # Merge cells [13,0] to [19,5]
        grid.merge((13, 0), (19, 5))

        # Get the pixel bounds for this merge
        (x1, y1), (x2, y2) = grid.get_grid((13, 0), convert_to_pixel=True)

        # With anchor='rb', the position should be at the bottom-right
        result = grid._calculate_anchor_position(x1, y1, x2, y2, "rb")

        # The result should be (x2, y2), not (x1, y1)
        self.assertEqual(result, (x2, y2))
        self.assertNotEqual(result, (x1, y1))

    def test_all_anchors_comprehensive(self):
        """Comprehensive test of all valid PIL anchor combinations."""
        x1, y1, x2, y2 = 0, 0, 100, 100

        # Define all valid anchor combinations and their expected positions
        test_cases = {
            # Left column
            "lt": (0, 0),  # left-top
            "lm": (0, 50.0),  # left-middle
            "lb": (0, 100),  # left-bottom
            "ls": (0, 100),  # left-baseline
            # Middle column
            "mt": (50.0, 0),  # middle-top
            "mm": (50.0, 50.0),  # middle-middle
            "mb": (50.0, 100),  # middle-bottom
            "ms": (50.0, 100),  # middle-baseline
            # Right column
            "rt": (100, 0),  # right-top
            "rm": (100, 50.0),  # right-middle
            "rb": (100, 100),  # right-bottom
            "rs": (100, 100),  # right-baseline
        }

        for anchor, expected in test_cases.items():
            with self.subTest(anchor=anchor):
                result = self.grid._calculate_anchor_position(x1, y1, x2, y2, anchor)
                self.assertEqual(
                    result,
                    expected,
                    f"Anchor '{anchor}' failed: expected {expected}, got {result}",
                )


if __name__ == "__main__":
    unittest.main()
