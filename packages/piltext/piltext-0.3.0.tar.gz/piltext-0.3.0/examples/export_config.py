"""Example: Export piltext configuration to YAML.

This example demonstrates how to use ConfigExporter to create piltext
objects programmatically and export them to a YAML configuration file.
"""

from piltext import ConfigExporter, FontManager, ImageDrawer, TextGrid


def main():
    fm = FontManager(default_font_size=24, default_font_name="Jersey10-Regular")
    drawer = ImageDrawer(400, 200, mode="RGB", background="white", font_manager=fm)
    grid = TextGrid(2, 2, drawer, margin_x=5, margin_y=5)

    grid.set_text((0, 0), "Hello", anchor="mm")
    grid.set_text((0, 1), "World", anchor="mm")
    grid.set_text((1, 0), "Piltext", anchor="mm", fill=128)
    grid.set_text((1, 1), "Export", anchor="mm", fill=200)

    exporter = ConfigExporter()
    exporter.export_grid(grid, "exported_config.yaml")

    print("Configuration exported to exported_config.yaml")


def create_custom_config():
    exporter = ConfigExporter()

    exporter.add_fonts(
        fontdirs=["/usr/share/fonts/truetype/dejavu"],
        default_size=32,
        default_name="DejaVuSans.ttf",
    )

    exporter.add_image(width=600, height=400, background="black", inverted=True)

    exporter.add_grid(
        rows=3,
        columns=3,
        margin_x=10,
        margin_y=10,
        merges=[((0, 0), (0, 2))],
        texts=[
            {"start": [0, 0], "text": "Header", "anchor": "mm", "fill": "white"},
            {"start": [1, 0], "text": "Cell 1", "anchor": "mm"},
            {"start": [1, 1], "text": "Cell 2", "anchor": "mm"},
            {"start": [1, 2], "text": "Cell 3", "anchor": "mm"},
            {"start": [2, 0], "text": "Footer", "anchor": "mm"},
        ],
    )

    exporter.export("custom_config.yaml")
    print("Custom configuration exported to custom_config.yaml")


def create_dial_config():
    exporter = ConfigExporter()

    exporter.add_fonts(default_size=48)
    exporter.add_dial(
        percentage=0.75,
        size=300,
        bg_color="white",
        fg_color="#4CAF50",
        track_color="#e0e0e0",
        thickness=30,
        show_needle=True,
        show_ticks=True,
        show_value=True,
    )

    exporter.export("dial_config.yaml")
    print("Dial configuration exported to dial_config.yaml")


def create_squares_config():
    exporter = ConfigExporter()

    exporter.add_fonts(default_size=20)
    exporter.add_squares(
        percentage=0.68,
        max_squares=100,
        size=250,
        bg_color="white",
        fg_color="#2196F3",
        empty_color="#e0e0e0",
        gap=3,
        rows=10,
        columns=10,
        border_width=1,
        border_color="#cccccc",
        show_partial=True,
    )

    exporter.export("squares_config.yaml")
    print("Squares configuration exported to squares_config.yaml")


if __name__ == "__main__":
    main()
    create_custom_config()
    create_dial_config()
    create_squares_config()
