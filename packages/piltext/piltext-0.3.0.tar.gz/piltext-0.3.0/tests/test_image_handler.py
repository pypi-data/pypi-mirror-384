import unittest
from unittest.mock import patch

from PIL import Image

from piltext import ImageHandler


class TestImageHandler(unittest.TestCase):
    def setUp(self):
        self.image_handler = ImageHandler(100, 100)

    def test_initialize_image(self):
        self.assertIsInstance(self.image_handler.image, Image.Image)
        self.assertEqual(self.image_handler.image.size, (100, 100))

    def test_change_size(self):
        self.image_handler.change_size(200, 200)
        self.assertEqual(self.image_handler.image.size, (200, 200))

    @patch("PIL.Image.Image.rotate")
    @patch("PIL.ImageOps.mirror")
    def test_apply_transformations(self, mock_mirror, mock_rotate):
        # Test image transformations
        self.image_handler.apply_transformations(mirror=True, orientation=90)
        mock_rotate.assert_called_once()
        mock_mirror.assert_called_once()


if __name__ == "__main__":
    unittest.main()
