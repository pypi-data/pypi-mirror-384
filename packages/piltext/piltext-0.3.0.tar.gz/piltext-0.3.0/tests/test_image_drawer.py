import os
import unittest

from piltext import FontManager, ImageDrawer


class TestImageDrawer(unittest.TestCase):
    def setUp(self):
        self.fontdirs = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
        ]
        self.font_manager = FontManager(fontdirs=self.fontdirs)
        self.image_drawer = ImageDrawer(264, 127, font_manager=self.font_manager)

    def test_draw_text_with_size_calculation(self):
        # Mock text size calculation and drawing
        xy = (5, 16)
        w, h, font_size = self.image_drawer.draw_text(
            "12345 abcdefg", xy, end=(254, 17), font_name="Roboto-Bold", anchor="lt"
        )
        self.assertIn(w, [7, 11])
        self.assertIn(h, [1, 2])
        self.assertEqual(font_size, 1)
        # Mock text size calculation and drawing
        xy = (5, 16)
        w, h, font_size = self.image_drawer.draw_text(
            "12345 abcdefg", xy, end=(254, 25), font_name="Roboto-Bold", anchor="lt"
        )
        self.assertIn(w, [47, 48])
        self.assertEqual(h, 9)
        self.assertEqual(font_size, 7)

    def test_default_mode_and_background(self):
        drawer = ImageDrawer(100, 100, font_manager=self.font_manager)
        self.assertEqual(drawer.image_handler.mode, "RGB")
        self.assertEqual(drawer.image_handler.background, "white")
        self.assertEqual(drawer.image_handler.width, 100)
        self.assertEqual(drawer.image_handler.height, 100)

    def test_grayscale_mode_with_int_background(self):
        drawer = ImageDrawer(
            100, 100, mode="L", background=255, font_manager=self.font_manager
        )
        self.assertEqual(drawer.image_handler.mode, "L")
        self.assertEqual(drawer.image_handler.background, 255)
        self.assertEqual(drawer.get_image().mode, "L")

    def test_grayscale_mode_with_black_background(self):
        drawer = ImageDrawer(
            100, 100, mode="L", background=0, font_manager=self.font_manager
        )
        self.assertEqual(drawer.image_handler.mode, "L")
        self.assertEqual(drawer.image_handler.background, 0)

    def test_rgba_mode_with_tuple_background(self):
        drawer = ImageDrawer(
            100,
            100,
            mode="RGBA",
            background=(255, 0, 0, 255),
            font_manager=self.font_manager,
        )
        self.assertEqual(drawer.image_handler.mode, "RGBA")
        self.assertEqual(drawer.image_handler.background, (255, 0, 0, 255))
        self.assertEqual(drawer.get_image().mode, "RGBA")

    def test_rgb_mode_with_hex_background(self):
        drawer = ImageDrawer(
            100, 100, mode="RGB", background="#FF0000", font_manager=self.font_manager
        )
        self.assertEqual(drawer.image_handler.mode, "RGB")
        self.assertEqual(drawer.image_handler.background, "#FF0000")

    def test_binary_mode(self):
        drawer = ImageDrawer(
            100, 100, mode="1", background=1, font_manager=self.font_manager
        )
        self.assertEqual(drawer.image_handler.mode, "1")
        self.assertEqual(drawer.image_handler.background, 1)
        self.assertEqual(drawer.get_image().mode, "1")

    def test_mode_background_with_color_name(self):
        drawer = ImageDrawer(
            100, 100, mode="RGB", background="black", font_manager=self.font_manager
        )
        self.assertEqual(drawer.image_handler.mode, "RGB")
        self.assertEqual(drawer.image_handler.background, "black")

    def test_initialize_preserves_mode_and_background(self):
        drawer = ImageDrawer(
            100, 100, mode="L", background=128, font_manager=self.font_manager
        )
        drawer.initialize()
        self.assertEqual(drawer.image_handler.mode, "L")
        self.assertEqual(drawer.image_handler.background, 128)
        self.assertEqual(drawer.get_image().mode, "L")

    def test_change_size_preserves_mode_and_background(self):
        drawer = ImageDrawer(
            100,
            100,
            mode="RGBA",
            background=(0, 255, 0, 128),
            font_manager=self.font_manager,
        )
        drawer.change_size(200, 200)
        self.assertEqual(drawer.image_handler.mode, "RGBA")
        self.assertEqual(drawer.image_handler.background, (0, 255, 0, 128))
        self.assertEqual(drawer.image_handler.width, 200)
        self.assertEqual(drawer.image_handler.height, 200)


if __name__ == "__main__":
    unittest.main()
