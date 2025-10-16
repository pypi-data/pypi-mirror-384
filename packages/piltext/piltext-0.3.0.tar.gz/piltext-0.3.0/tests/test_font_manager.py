import os
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image, ImageDraw

from piltext import (
    FontManager,  # Assuming the class is in a file called font_manager.py
)


class TestFontManager(unittest.TestCase):
    def setUp(self):
        # Create a FontManager instance with a mock directory
        self.fontdirs = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
        ]
        self.font_manager = FontManager(
            fontdirs=self.fontdirs,
            default_font_size=20,
            default_font_name="Roboto-Bold",
        )

    @patch("os.path.exists")
    def test_get_full_path_font_found(self, mock_exists):
        # Simulate font file found
        mock_exists.side_effect = lambda path: path.endswith("Roboto-Bold.ttf")
        font_path = self.font_manager.get_full_path("Roboto-Bold")
        self.assertTrue(font_path.endswith("Roboto-Bold.ttf"))

    @patch("os.path.exists")
    def test_get_full_path_font_not_found(self, mock_exists):
        # Simulate font file not found
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.font_manager.get_full_path("NonExistentFont")

    @patch("PIL.ImageFont.truetype")
    @patch("os.path.exists")
    def test_build_font_creates_font(self, mock_exists, mock_truetype):
        # Simulate font file found
        mock_exists.side_effect = lambda path: path.endswith("Roboto-Bold.ttf")
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font

        font = self.font_manager.build_font("Roboto-Bold", 20)

        # Normalize the path to make the test cross-platform
        expected_path = f"{self.fontdirs[0]}{os.path.sep}Roboto-Bold.ttf"
        mock_truetype.assert_called_once_with(expected_path, 20)
        self.assertEqual(font, mock_font)

    @patch("PIL.ImageFont.truetype")
    @patch("os.path.exists")
    def test_build_font_caching(self, mock_exists, mock_truetype):
        # Simulate font file found and cache behavior
        mock_exists.side_effect = lambda path: path.endswith("Roboto-Bold.ttf")
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font

        # Build font the first time
        font = self.font_manager.build_font("Roboto-Bold", 20)
        self.assertEqual(
            self.font_manager._font_cache[("Roboto-Bold", 20, "none")], font
        )

        # Build font the second time (should use cache, not call truetype again)
        font_cached = self.font_manager.build_font("Roboto-Bold", 20)
        self.assertEqual(font, font_cached)
        mock_truetype.assert_called_once()  # Ensure truetype is only called once

    def test_add_font_directory(self):
        self.font_manager.add_font_directory("./new_font_dir")
        self.assertIn(
            os.path.realpath("./new_font_dir"),
            self.font_manager.list_font_directories(),
        )

    def test_add_existing_font_directory(self):
        with patch("builtins.print") as mocked_print:
            self.font_manager.add_font_directory(self.fontdirs[0])
            mocked_print.assert_called_once_with(
                f"Font directory '{self.fontdirs[0]}' already exists."
            )

    def test_remove_font_directory(self):
        self.font_manager.add_font_directory("./new_font_dir")
        self.font_manager.remove_font_directory("./new_font_dir")
        self.assertNotIn("./new_font_dir", self.font_manager.list_font_directories())

    def test_remove_nonexistent_font_directory(self):
        with patch("builtins.print") as mocked_print:
            self.font_manager.remove_font_directory("./nonexistent_dir")
            mocked_print.assert_called_once_with(
                "Font directory './nonexistent_dir' not found in the list."
            )

    def test_list_available_fonts(self):
        # Simulate a directory with font files

        available_fonts = self.font_manager.list_available_fonts()
        self.assertIn("Roboto-Bold", available_fonts)
        self.assertIn("PixelSplitter-Bold", available_fonts)
        self.assertNotIn("README", available_fonts)

    def test_calculate_text_size(self):
        # Create a dummy image and draw object
        image = Image.new("RGB", (100, 100))
        draw = ImageDraw.Draw(image)

        # Build a font and calculate text size
        font = self.font_manager.build_font("Roboto-Bold", 20)
        size = self.font_manager.calculate_text_size(draw, "Hello", font)

        # Since this involves PIL rendering, we'll
        # simply check it's a tuple with width and height
        self.assertIsInstance(size, tuple)
        self.assertEqual(len(size), 2)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_get_full_path_rejects_directory(self, mock_isfile, mock_exists):
        # Simulate a path that exists but is a directory, not a file
        mock_exists.return_value = True
        mock_isfile.return_value = False
        with self.assertRaises(FileNotFoundError) as context:
            self.font_manager.get_full_path("SomeDirectory")
        self.assertIn("not found", str(context.exception))

    @patch("os.path.isfile")
    @patch("os.path.exists")
    def test_build_font_validates_file(self, mock_exists, mock_isfile):
        # First call: get_full_path checks - return True for exists, False for isfile
        # This will cause get_full_path to fail
        def isfile_side_effect(path):
            # Return False to simulate a directory instead of file
            return False

        def exists_side_effect(path):
            # Return True to simulate the path exists
            return path.endswith("Roboto-Bold.ttf") or path.endswith("Roboto-Bold")

        mock_exists.side_effect = exists_side_effect
        mock_isfile.side_effect = isfile_side_effect

        with self.assertRaises(FileNotFoundError) as context:
            self.font_manager.build_font("Roboto-Bold", 20)
        # get_full_path will raise because isfile returns False
        self.assertIn("not found", str(context.exception))

    @patch("os.access")
    @patch("os.path.getsize")
    @patch("PIL.ImageFont.truetype")
    @patch("os.path.isfile")
    @patch("os.path.exists")
    def test_build_font_handles_invalid_format(
        self, mock_exists, mock_isfile, mock_truetype, mock_getsize, mock_access
    ):
        # Simulate a file that exists but has invalid format
        mock_exists.side_effect = lambda path: path.endswith("BadFont.ttf")
        mock_isfile.side_effect = lambda path: path.endswith("BadFont.ttf")
        mock_getsize.return_value = 1024  # 1KB file
        mock_access.return_value = True  # Readable
        mock_truetype.side_effect = OSError("unknown file format")

        with self.assertRaises(OSError) as context:
            self.font_manager.build_font("BadFont", 20)
        # Should provide helpful error message
        self.assertIn("Failed to load font", str(context.exception))
        self.assertIn("corrupted", str(context.exception))
        self.assertIn("TrueType", str(context.exception))

    def test_validate_font_file_valid(self):
        # Test with a real valid font file
        font_path = os.path.join(self.fontdirs[0], "Roboto-Bold.ttf")
        info = self.font_manager.validate_font_file(font_path)
        self.assertTrue(info["valid"])
        self.assertTrue(info["exists"])
        self.assertTrue(info["is_file"])
        self.assertTrue(info["readable"])
        self.assertGreater(info["size"], 0)
        self.assertEqual(info["path"], os.path.abspath(font_path))

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.access")
    @patch("os.path.getsize")
    def test_validate_font_file_nonexistent(
        self, mock_getsize, mock_access, mock_isfile, mock_exists
    ):
        # Test with a non-existent file
        mock_exists.return_value = False
        mock_isfile.return_value = False
        mock_access.return_value = False
        mock_getsize.return_value = 0

        info = self.font_manager.validate_font_file("/fake/path/NonExistent.ttf")
        self.assertFalse(info["valid"])
        self.assertFalse(info["exists"])
        self.assertFalse(info["is_file"])
        self.assertFalse(info["readable"])
        self.assertEqual(info["size"], 0)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.access")
    @patch("os.path.getsize")
    def test_validate_font_file_directory(
        self, mock_getsize, mock_access, mock_isfile, mock_exists
    ):
        # Test with a directory instead of a file
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_access.return_value = True
        mock_getsize.return_value = 4096

        info = self.font_manager.validate_font_file("/some/directory")
        self.assertFalse(info["valid"])
        self.assertTrue(info["exists"])
        self.assertFalse(info["is_file"])
        self.assertTrue(info["readable"])
        self.assertEqual(info["size"], 4096)


if __name__ == "__main__":
    unittest.main()
