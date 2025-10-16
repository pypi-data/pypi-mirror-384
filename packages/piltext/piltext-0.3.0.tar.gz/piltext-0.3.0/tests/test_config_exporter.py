import os
import tempfile
import unittest

import yaml

from piltext import ConfigExporter, FontManager, ImageDrawer, TextGrid


class TestConfigExporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test_config.yaml")

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        os.rmdir(self.temp_dir)

    def test_add_fonts(self):
        exporter = ConfigExporter()
        exporter.add_fonts(
            fontdirs=["/usr/share/fonts"],
            default_size=20,
            default_name="Arial",
            downloads=[{"url": "https://example.com/font.ttf"}],
        )

        config = exporter.get_config()
        self.assertIn("fonts", config)
        self.assertEqual(config["fonts"]["directories"], ["/usr/share/fonts"])
        self.assertEqual(config["fonts"]["default_size"], 20)
        self.assertEqual(config["fonts"]["default_name"], "Arial")
        self.assertEqual(
            config["fonts"]["download"], [{"url": "https://example.com/font.ttf"}]
        )

    def test_add_image(self):
        exporter = ConfigExporter()
        exporter.add_image(width=640, height=480, mode="L", background="black")

        config = exporter.get_config()
        self.assertIn("image", config)
        self.assertEqual(config["image"]["width"], 640)
        self.assertEqual(config["image"]["height"], 480)
        self.assertEqual(config["image"]["mode"], "L")
        self.assertEqual(config["image"]["background"], "black")

    def test_add_grid(self):
        exporter = ConfigExporter()
        exporter.add_grid(rows=4, columns=3, margin_x=5, margin_y=10)

        config = exporter.get_config()
        self.assertIn("grid", config)
        self.assertEqual(config["grid"]["rows"], 4)
        self.assertEqual(config["grid"]["columns"], 3)
        self.assertEqual(config["grid"]["margin_x"], 5)
        self.assertEqual(config["grid"]["margin_y"], 10)

    def test_add_grid_with_merges(self):
        exporter = ConfigExporter()
        merges = [((0, 0), (0, 1)), ((1, 0), (2, 0))]
        exporter.add_grid(rows=3, columns=2, merges=merges)

        config = exporter.get_config()
        self.assertIn("grid", config)
        self.assertEqual(config["grid"]["merge"], [[[0, 0], [0, 1]], [[1, 0], [2, 0]]])

    def test_add_grid_with_texts(self):
        exporter = ConfigExporter()
        texts = [
            {"start": [0, 0], "text": "Hello", "font_size": 20},
            {"start": [1, 1], "text": "World", "fill": "blue"},
        ]
        exporter.add_grid(rows=2, columns=2, texts=texts)

        config = exporter.get_config()
        self.assertIn("grid", config)
        self.assertEqual(len(config["grid"]["texts"]), 2)
        self.assertEqual(config["grid"]["texts"][0]["text"], "Hello")
        self.assertEqual(config["grid"]["texts"][1]["text"], "World")

    def test_add_squares(self):
        exporter = ConfigExporter()
        exporter.add_squares(
            percentage=0.75,
            max_squares=50,
            size=300,
            bg_color="blue",
            fg_color="red",
        )

        config = exporter.get_config()
        self.assertIn("squares", config)
        self.assertEqual(config["squares"]["percentage"], 0.75)
        self.assertEqual(config["squares"]["max_squares"], 50)
        self.assertEqual(config["squares"]["size"], 300)
        self.assertEqual(config["squares"]["bg_color"], "blue")
        self.assertEqual(config["squares"]["fg_color"], "red")

    def test_add_dial(self):
        exporter = ConfigExporter()
        exporter.add_dial(
            percentage=0.85,
            size=250,
            radius=100,
            bg_color="white",
            fg_color="green",
            show_needle=False,
        )

        config = exporter.get_config()
        self.assertIn("dial", config)
        self.assertEqual(config["dial"]["percentage"], 0.85)
        self.assertEqual(config["dial"]["size"], 250)
        self.assertEqual(config["dial"]["radius"], 100)
        self.assertEqual(config["dial"]["fg_color"], "green")
        self.assertEqual(config["dial"]["show_needle"], False)

    def test_export_to_file(self):
        exporter = ConfigExporter()
        exporter.add_image(width=480, height=280)
        exporter.add_grid(rows=2, columns=2)
        exporter.export(self.temp_file)

        self.assertTrue(os.path.exists(self.temp_file))

        with open(self.temp_file) as f:
            loaded_config = yaml.safe_load(f)

        self.assertIn("image", loaded_config)
        self.assertIn("grid", loaded_config)
        self.assertEqual(loaded_config["image"]["width"], 480)
        self.assertEqual(loaded_config["grid"]["rows"], 2)

    def test_export_grid_object(self):
        fm = FontManager(default_font_size=15)
        drawer = ImageDrawer(400, 300, font_manager=fm)
        grid = TextGrid(3, 3, drawer, margin_x=5, margin_y=5)

        exporter = ConfigExporter()
        exporter.export_grid(grid, self.temp_file)

        self.assertTrue(os.path.exists(self.temp_file))

        with open(self.temp_file) as f:
            loaded_config = yaml.safe_load(f)

        self.assertIn("fonts", loaded_config)
        self.assertIn("image", loaded_config)
        self.assertIn("grid", loaded_config)

    def test_export_grid_with_content_items(self):
        """Test exporting grid with text content from content_items."""
        fm = FontManager(
            fontdirs="tests/fonts",
            default_font_size=20,
            default_font_name="Roboto-Bold",
        )
        drawer = ImageDrawer(600, 400, background="white", font_manager=fm)
        grid = TextGrid(3, 3, drawer, margin_x=10, margin_y=10)

        # Add text content
        grid.set_text((0, 0), "Header", font_name="Roboto-Bold", anchor="mm")
        grid.set_text((1, 0), "Row 1", font_name="Roboto-Bold")
        grid.set_text((2, 1), "Row 2", font_name="Roboto-Bold", anchor="rb")

        exporter = ConfigExporter()
        exporter.export_grid(grid, self.temp_file)

        self.assertTrue(os.path.exists(self.temp_file))

        with open(self.temp_file) as f:
            loaded_config = yaml.safe_load(f)

        # Verify texts are exported
        self.assertIn("grid", loaded_config)
        self.assertIn("texts", loaded_config["grid"])
        self.assertEqual(len(loaded_config["grid"]["texts"]), 3)

        # Verify text content
        texts = loaded_config["grid"]["texts"]
        self.assertEqual(texts[0]["start"], [0, 0])
        self.assertEqual(texts[0]["text"], "Header")
        self.assertEqual(texts[0]["font_name"], "Roboto-Bold")
        self.assertEqual(texts[0]["anchor"], "mm")

        self.assertEqual(texts[1]["start"], [1, 0])
        self.assertEqual(texts[1]["text"], "Row 1")

        self.assertEqual(texts[2]["start"], [2, 1])
        self.assertEqual(texts[2]["text"], "Row 2")
        self.assertEqual(texts[2]["anchor"], "rb")

    def test_export_grid_with_mixed_content(self):
        """Test that only text items are exported from mixed content."""
        fm = FontManager(
            fontdirs="tests/fonts",
            default_font_size=20,
            default_font_name="Roboto-Bold",
        )
        drawer = ImageDrawer(600, 400, background="white", font_manager=fm)
        grid = TextGrid(3, 3, drawer, margin_x=5, margin_y=5)

        # Add mixed content
        grid.set_text((0, 0), "Text Item", font_name="Roboto-Bold")
        grid.set_dial((1, 1), 0.75)
        grid.set_squares((2, 2), 0.5)

        exporter = ConfigExporter()
        exporter.export_grid(grid, self.temp_file)

        with open(self.temp_file) as f:
            loaded_config = yaml.safe_load(f)

        # Only text items should be exported
        texts = loaded_config["grid"]["texts"]
        self.assertEqual(len(texts), 1)
        self.assertEqual(texts[0]["text"], "Text Item")

        # Type field should not be in exported config
        self.assertNotIn("type", texts[0])

    def test_export_grid_no_content_items(self):
        """Test exporting grid with no content items."""
        fm = FontManager(default_font_size=15)
        drawer = ImageDrawer(400, 300, font_manager=fm)
        grid = TextGrid(3, 3, drawer)

        exporter = ConfigExporter()
        exporter.export_grid(grid, self.temp_file)

        with open(self.temp_file) as f:
            loaded_config = yaml.safe_load(f)

        # Texts should be empty or not present
        self.assertNotIn("texts", loaded_config["grid"])


if __name__ == "__main__":
    unittest.main()
