import unittest
from unittest.mock import MagicMock

from PIL import Image

from piltext import TextGrid


# Mock classes for FontManager and ImageDrawer, assuming they are correctly implemented
class MockFontManager:
    def __init__(self, *args, **kwargs):
        pass

    def build_font(self, font_name=None):
        return MagicMock()

    def calculate_text_size(self, draw, text, font):
        # Mocked to return a fixed width and height for testing purposes
        return (100, 50)


class MockImageHandler:
    def __init__(self, width, height):
        self.image = Image.new("RGB", (width, height), color="white")

    def apply_transformations(self, *args, **kwargs):
        pass

    def show(self, *args, **kwargs):
        pass


class MockImageDrawer:
    def __init__(self, width, height, font_manager=None):
        self.image_handler = MockImageHandler(width, height)
        self.font_manager = font_manager or MockFontManager()
        self.draw = MagicMock()  # Mock drawing operations

    def draw_text(self, text, start, end=None, font_name=None, **kwargs):
        # Mock the draw_text method to check that
        # it's being called with correct parameters
        self.draw.text((start, text, font_name))
        return 0, 0, 0

    def paste(self, image, box=None, **kwargs):
        # Mock paste method for image pasting
        pass

    def finalize(self, inverted=False):
        pass

    def get_image(self):
        return self.image_handler.image


class TestGrid(unittest.TestCase):
    def setUp(self):
        font_manager = MockFontManager()
        self.image_drawer = MockImageDrawer(480, 280, font_manager)
        self.image_drawer.draw_text = MagicMock()

        self.grid = TextGrid(4, 4, self.image_drawer)  # 4x4 grid

    def test_grid_cell_size(self):
        """Test that the grid cells are the correct size."""
        self.assertEqual(self.grid.cell_width, 120)  # 480 / 4
        self.assertEqual(self.grid.cell_height, 70)  # 280 / 4

    def test_grid_to_pixels(self):
        """Test that grid coordinates are correctly converted to pixel coordinates."""
        start_pixel, end_pixel = self.grid._grid_to_pixels((0, 0), (0, 3))
        self.assertEqual(start_pixel, (0, 0))
        self.assertEqual(
            end_pixel, (480, 70)
        )  # Spans across 4 columns in the first row

        start_pixel, end_pixel = self.grid._grid_to_pixels((1, 1), (1, 2))
        self.assertEqual(start_pixel, (120, 70))  # 2nd row, 2nd column
        self.assertEqual(end_pixel, (360, 140))  # Spans across 2 columns

    def test_set_text_single_cell(self):
        """Test that text is correctly placed within a single grid cell."""
        self.grid.set_text((2, 1), "Test4", end=((2, 1)))

        # Check that draw_text was called with the correct pixel coordinates
        self.image_drawer.draw_text.assert_called_with(
            "Test4",
            (120, 140),
            end=(240, 210),
            font_name=None,
            font_variation=None,
            anchor="lt",
        )

    def test_set_text_multiple_cells(self):
        """Test that text is correctly placed spanning multiple grid cells."""
        self.grid.set_text(
            (0, 0), "Test1", end=(0, 3), font_name="PixelSplitter-Bold", anchor="lt"
        )

        # Check that draw_text was called with the correct pixel coordinates
        self.image_drawer.draw_text.assert_called_with(
            "Test1",
            (0, 0),
            end=(480, 70),
            font_name="PixelSplitter-Bold",
            font_variation=None,
            anchor="lt",
        )

    def test_set_text_different_rows(self):
        """Test text spanning across rows and columns."""
        self.grid.set_text(
            (1, 0),
            "TestMulticell",
            end=(2, 2),
            font_name="Roboto-Bold",
            font_variation=None,
            anchor="lt",
        )

        # Check that draw_text was called with the correct pixel coordinates
        self.image_drawer.draw_text.assert_called_with(
            "TestMulticell",
            (0, 70),
            end=(360, 210),
            font_name="Roboto-Bold",
            font_variation=None,
            anchor="lt",
        )

    def test_get_dimensions(self):
        """Test get_dimensions for single and merged cells."""
        # Single cell (0,0)
        dims = self.grid.get_dimensions((0, 0))
        self.assertEqual(dims["start"], (0, 0))
        self.assertEqual(dims["end"], (0, 0))
        self.assertEqual(dims["x"], 0)
        self.assertEqual(dims["y"], 0)
        self.assertEqual(dims["width"], 120)
        self.assertEqual(dims["height"], 70)

        # Multi-cell (merged) (1,1) to (2,2)
        dims_merged = self.grid.get_dimensions((1, 1), end=(2, 2))
        self.assertEqual(dims_merged["start"], (1, 1))
        self.assertEqual(dims_merged["end"], (2, 2))
        self.assertEqual(dims_merged["x"], 120)
        self.assertEqual(dims_merged["y"], 70)
        self.assertEqual(dims_merged["width"], 240)
        self.assertEqual(dims_merged["height"], 140)

    def test_modify_grid2pixel(self):
        """Test modifying a cell's pixel region."""
        # Modify a single cell
        self.grid.modify_grid2pixel((0, 0), d_x1=10, d_y1=5, d_x2=10, d_y2=5)
        (x1, y1), (x2, y2) = self.grid.get_grid((0, 0), convert_to_pixel=True)
        self.assertEqual(x1, -10)
        self.assertEqual(y1, -5)
        self.assertEqual(x2, 130)
        self.assertEqual(y2, 75)

        # Reset grid for next test
        self.setUp()

        # Modify a merged cell region
        self.grid.merge((1, 1), (2, 2))
        self.grid.modify_grid2pixel((1, 1), d_x1=20, d_y1=15, d_x2=20, d_y2=15)
        (x1, y1), (x2, y2) = self.grid.get_grid((1, 1), convert_to_pixel=True)
        self.assertEqual(x1, 100)  # 120 - 20
        self.assertEqual(y1, 55)  # 70 - 15
        self.assertEqual(x2, 380)  # 360 + 20
        self.assertEqual(y2, 225)  # 210 + 15

    def test_auto_render_default(self):
        """Test that auto_render is True by default."""
        self.assertTrue(self.grid.auto_render)

    def test_auto_render_stores_content(self):
        """Test that content is stored when using auto_render=True."""
        self.grid.set_text((0, 0), "Test")
        self.assertEqual(len(self.grid.content_items), 1)
        self.assertEqual(self.grid.content_items[0]["type"], "text")
        self.assertEqual(self.grid.content_items[0]["text"], "Test")
        self.assertEqual(self.grid.content_items[0]["start"], (0, 0))

    def test_manual_render_mode(self):
        """Test that auto_render=False defers rendering."""
        font_manager = MockFontManager()
        image_drawer = MockImageDrawer(480, 280, font_manager)
        image_drawer.draw_text = MagicMock()
        grid = TextGrid(4, 4, image_drawer, auto_render=False)

        grid.set_text((0, 0), "Test1")
        grid.set_text((1, 1), "Test2")

        # Should not have called draw_text yet
        image_drawer.draw_text.assert_not_called()

        # Content should be stored
        self.assertEqual(len(grid.content_items), 2)

        # Now render
        grid.render()

        # Should have called draw_text twice
        self.assertEqual(image_drawer.draw_text.call_count, 2)

    def test_content_items_structure_text(self):
        """Test that text content items have the correct structure."""
        self.grid.set_text(
            (0, 0),
            "Hello",
            end=(0, 1),
            font_name="Arial",
            font_variation="Bold",
            anchor="mm",
        )

        self.assertEqual(len(self.grid.content_items), 1)
        item = self.grid.content_items[0]

        self.assertEqual(item["type"], "text")
        self.assertEqual(item["start"], (0, 0))
        self.assertEqual(item["end"], (0, 1))
        self.assertEqual(item["text"], "Hello")
        self.assertEqual(item["font_name"], "Arial")
        self.assertEqual(item["font_variation"], "Bold")
        self.assertEqual(item["anchor"], "mm")

    def test_content_items_structure_image(self):
        """Test that image content items have the correct structure."""
        test_image = Image.new("RGB", (100, 100), color="red")
        self.grid.paste_image((1, 1), test_image, anchor="mm")

        self.assertEqual(len(self.grid.content_items), 1)
        item = self.grid.content_items[0]

        self.assertEqual(item["type"], "image")
        self.assertEqual(item["start"], (1, 1))
        self.assertEqual(item["image"], test_image)
        self.assertEqual(item["anchor"], "mm")

    def test_content_items_structure_dial(self):
        """Test that dial content items have the correct structure."""
        self.grid.set_dial((2, 2), 0.75, bg_color="blue", fg_color="red")

        self.assertEqual(len(self.grid.content_items), 1)
        item = self.grid.content_items[0]

        self.assertEqual(item["type"], "dial")
        self.assertEqual(item["start"], (2, 2))
        self.assertEqual(item["percentage"], 0.75)
        self.assertEqual(item["bg_color"], "blue")
        self.assertEqual(item["fg_color"], "red")

    def test_content_items_structure_squares(self):
        """Test that squares content items have the correct structure."""
        self.grid.set_squares((1, 0), 0.5, bg_color="white", fg_color="black")

        self.assertEqual(len(self.grid.content_items), 1)
        item = self.grid.content_items[0]

        self.assertEqual(item["type"], "squares")
        self.assertEqual(item["start"], (1, 0))
        self.assertEqual(item["percentage"], 0.5)
        self.assertEqual(item["bg_color"], "white")
        self.assertEqual(item["fg_color"], "black")

    def test_clear_content(self):
        """Test that clear_content removes all stored content."""
        self.grid.set_text((0, 0), "Test1")
        self.grid.set_text((1, 1), "Test2")
        test_image = Image.new("RGB", (100, 100), color="red")
        self.grid.paste_image((2, 2), test_image)

        self.assertEqual(len(self.grid.content_items), 3)

        self.grid.clear_content()

        self.assertEqual(len(self.grid.content_items), 0)

    def test_mixed_content_types(self):
        """Test storing different types of content together."""
        self.grid.set_text((0, 0), "Text")
        test_image = Image.new("RGB", (50, 50), color="blue")
        self.grid.paste_image((1, 1), test_image)
        self.grid.set_dial((2, 2), 0.8)
        self.grid.set_squares((3, 3), 0.6)

        self.assertEqual(len(self.grid.content_items), 4)

        types = [item["type"] for item in self.grid.content_items]
        self.assertEqual(types, ["text", "image", "dial", "squares"])

    def test_render_multiple_times(self):
        """Test that render() can be called multiple times."""
        font_manager = MockFontManager()
        image_drawer = MockImageDrawer(480, 280, font_manager)
        image_drawer.draw_text = MagicMock()
        grid = TextGrid(4, 4, image_drawer, auto_render=False)

        grid.set_text((0, 0), "Test")
        grid.render()
        first_call_count = image_drawer.draw_text.call_count

        grid.render()
        second_call_count = image_drawer.draw_text.call_count

        # Should render the same content again
        self.assertEqual(second_call_count, first_call_count * 2)

    def test_content_accumulation(self):
        """Test that content accumulates across multiple operations."""
        self.grid.set_text((0, 0), "First")
        self.assertEqual(len(self.grid.content_items), 1)

        self.grid.set_text((1, 1), "Second")
        self.assertEqual(len(self.grid.content_items), 2)

        self.grid.set_dial((2, 2), 0.5)
        self.assertEqual(len(self.grid.content_items), 3)

        # Verify order is preserved
        self.assertEqual(self.grid.content_items[0]["text"], "First")
        self.assertEqual(self.grid.content_items[1]["text"], "Second")
        self.assertEqual(self.grid.content_items[2]["percentage"], 0.5)


if __name__ == "__main__":
    unittest.main()
