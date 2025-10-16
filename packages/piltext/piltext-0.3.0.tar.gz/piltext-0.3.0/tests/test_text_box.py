import os
import unittest

from piltext import FontManager, ImageDrawer, TextBox


class TestTextBox(unittest.TestCase):
    def setUp(self):
        self.fontdirs = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
        ]
        self.font_manager = FontManager(fontdirs=self.fontdirs)
        self.image_drawer = ImageDrawer(255, 127, font_manager=self.font_manager)
        self.text_box = TextBox("Test", font_manager=self.font_manager)

    def test_fit_text_box(self):
        # Mock text size calculation and drawing
        draw = self.image_drawer.draw
        self.text_box.text = "123456789 abcdef"
        max_width = 254
        max_height = 16.555
        font = self.text_box.fit_text(
            draw, max_width, max_height, font_name="Roboto-Bold", start_font_size=1
        )

        width, height = self.font_manager.calculate_text_size(
            draw, self.text_box.text, font
        )
        self.assertTrue(width <= max_width)
        self.assertTrue(height <= max_height)


if __name__ == "__main__":
    unittest.main()
