"""YAML configuration export for piltext objects.

This module provides the ConfigExporter class for exporting piltext objects
(TextGrid, ImageDrawer, FontManager, etc.) to YAML configuration files that
can be loaded by ConfigLoader.
"""

from typing import Any, Optional

import yaml


class ConfigExporter:
    """Exports piltext objects to YAML configuration format.

    ConfigExporter allows you to create and configure piltext objects
    programmatically and then export them to a YAML file that can be loaded
    by ConfigLoader.

    Examples
    --------
    >>> from piltext import TextGrid, ImageDrawer, FontManager, ConfigExporter
    >>> fm = FontManager(default_font_size=40, default_font_name="Arial")
    >>> drawer = ImageDrawer(480, 280, fm)
    >>> grid = TextGrid(4, 4, drawer, margin_x=2, margin_y=2)
    >>> exporter = ConfigExporter()
    >>> exporter.export_grid(grid, "config.yaml")
    """

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}

    def add_fonts(
        self,
        fontdirs: Optional[list[str]] = None,
        default_size: int = 15,
        default_name: Optional[str] = None,
        downloads: Optional[list[dict[str, str]]] = None,
    ) -> None:
        """Add font configuration to the export.

        Parameters
        ----------
        fontdirs : list of str, optional
            List of font directories to search.
        default_size : int, default=15
            Default font size in points.
        default_name : str, optional
            Default font name.
        downloads : list of dict, optional
            List of font downloads. Each dict should contain either:
            - {"url": "https://..."} for direct URL downloads
            - {"part1": "ofl", "part2": "roboto", "font_name": "Roboto-Regular.ttf"}
              for Google Fonts downloads
        """
        font_config: dict[str, Any] = {}

        if fontdirs is not None:
            font_config["directories"] = fontdirs

        font_config["default_size"] = default_size

        if default_name is not None:
            font_config["default_name"] = default_name

        if downloads:
            font_config["download"] = downloads

        self.config["fonts"] = font_config

    def add_image(
        self,
        width: int = 480,
        height: int = 280,
        mode: str = "RGB",
        background: str = "white",
        inverted: bool = False,
        mirror: bool = False,
        orientation: int = 0,
    ) -> None:
        """Add image configuration to the export.

        Parameters
        ----------
        width : int, default=480
            Image width in pixels.
        height : int, default=280
            Image height in pixels.
        mode : str, default="RGB"
            PIL image mode (e.g., "RGB", "L", "1").
        background : str, default="white"
            Background color (name, hex, or tuple).
        inverted : bool, default=False
            Whether to invert the image colors.
        mirror : bool, default=False
            Whether to mirror the image horizontally.
        orientation : int, default=0
            Rotation angle in degrees (0, 90, 180, 270).
        """
        image_config: dict[str, Any] = {
            "width": width,
            "height": height,
        }

        if mode != "RGB":
            image_config["mode"] = mode

        if background != "white":
            image_config["background"] = background

        if inverted:
            image_config["inverted"] = inverted

        if mirror:
            image_config["mirror"] = mirror

        if orientation != 0:
            image_config["orientation"] = orientation

        self.config["image"] = image_config

    def add_grid(
        self,
        rows: int,
        columns: int,
        margin_x: int = 0,
        margin_y: int = 0,
        merges: Optional[list[tuple[tuple[int, int], tuple[int, int]]]] = None,
        texts: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Add grid configuration to the export.

        Parameters
        ----------
        rows : int
            Number of grid rows.
        columns : int
            Number of grid columns.
        margin_x : int, default=0
            Horizontal margin in pixels.
        margin_y : int, default=0
            Vertical margin in pixels.
        merges : list of tuples, optional
            List of cell merges. Each tuple is
            ((start_row, start_col), (end_row, end_col)).
        texts : list of dict, optional
            List of text items to add to cells. Each dict should contain:
            - "start": [row, col] or index
            - "text": str
            - Optional: "font_name", "font_size", "font_variation",
              "fill", "anchor", etc.
        """
        grid_config: dict[str, Any] = {
            "rows": rows,
            "columns": columns,
        }

        if margin_x != 0:
            grid_config["margin_x"] = margin_x

        if margin_y != 0:
            grid_config["margin_y"] = margin_y

        if merges:
            grid_config["merge"] = [
                [[start[0], start[1]], [end[0], end[1]]] for start, end in merges
            ]

        if texts:
            formatted_texts = []
            for text_item in texts:
                formatted_item = text_item.copy()
                if "start" in formatted_item and isinstance(
                    formatted_item["start"], tuple
                ):
                    formatted_item["start"] = list(formatted_item["start"])
                if "end" in formatted_item and isinstance(formatted_item["end"], tuple):
                    formatted_item["end"] = list(formatted_item["end"])
                formatted_texts.append(formatted_item)
            grid_config["texts"] = formatted_texts

        self.config["grid"] = grid_config

    def add_squares(
        self,
        percentage: float = 0.0,
        max_squares: int = 100,
        size: int = 200,
        bg_color: str = "white",
        fg_color: str = "#4CAF50",
        empty_color: str = "#e0e0e0",
        gap: int = 2,
        rows: Optional[int] = None,
        columns: Optional[int] = None,
        border_width: int = 1,
        border_color: str = "#cccccc",
        show_partial: bool = True,
    ) -> None:
        """Add squares (waffle chart) configuration to the export.

        Parameters
        ----------
        percentage : float, default=0.0
            Percentage to display (0.0 to 1.0).
        max_squares : int, default=100
            Maximum number of squares in the grid.
        size : int, default=200
            Size of the image in pixels (width and height).
        bg_color : str, default="white"
            Background color.
        fg_color : str, default="#4CAF50"
            Filled square color.
        empty_color : str, default="#e0e0e0"
            Empty square color.
        gap : int, default=2
            Gap between squares in pixels.
        rows : int, optional
            Number of rows. If None, calculated automatically.
        columns : int, optional
            Number of columns. If None, calculated automatically.
        border_width : int, default=1
            Border width around each square.
        border_color : str, default="#cccccc"
            Border color.
        show_partial : bool, default=True
            Whether to show partial squares.
        """
        squares_config: dict[str, Any] = {
            "percentage": percentage,
            "max_squares": max_squares,
            "size": size,
            "bg_color": bg_color,
            "fg_color": fg_color,
            "empty_color": empty_color,
            "gap": gap,
            "border_width": border_width,
            "border_color": border_color,
            "show_partial": show_partial,
        }

        if rows is not None:
            squares_config["rows"] = rows

        if columns is not None:
            squares_config["columns"] = columns

        self.config["squares"] = squares_config

    def add_dial(
        self,
        percentage: float = 0.0,
        size: int = 200,
        radius: Optional[int] = None,
        bg_color: str = "white",
        fg_color: str = "#4CAF50",
        track_color: str = "#e0e0e0",
        thickness: int = 20,
        font_name: Optional[str] = None,
        font_size: Optional[int] = None,
        font_variation: Optional[str] = None,
        show_needle: bool = True,
        show_ticks: bool = True,
        show_value: bool = True,
        start_angle: int = -135,
        end_angle: int = 135,
    ) -> None:
        """Add dial (gauge) configuration to the export.

        Parameters
        ----------
        percentage : float, default=0.0
            Percentage to display (0.0 to 1.0).
        size : int, default=200
            Size of the image in pixels (width and height).
        radius : int, optional
            Radius of the dial. If None, calculated from size.
        bg_color : str, default="white"
            Background color.
        fg_color : str, default="#4CAF50"
            Filled arc color.
        track_color : str, default="#e0e0e0"
            Track (background arc) color.
        thickness : int, default=20
            Thickness of the arc.
        font_name : str, optional
            Font name for percentage text.
        font_size : int, optional
            Font size for percentage text.
        font_variation : str, optional
            Font variation (e.g., "Bold").
        show_needle : bool, default=True
            Whether to show the needle indicator.
        show_ticks : bool, default=True
            Whether to show tick marks.
        show_value : bool, default=True
            Whether to show the percentage value.
        start_angle : int, default=-135
            Start angle in degrees.
        end_angle : int, default=135
            End angle in degrees.
        """
        dial_config: dict[str, Any] = {
            "percentage": percentage,
            "size": size,
            "bg_color": bg_color,
            "fg_color": fg_color,
            "track_color": track_color,
            "thickness": thickness,
            "show_needle": show_needle,
            "show_ticks": show_ticks,
            "show_value": show_value,
            "start_angle": start_angle,
            "end_angle": end_angle,
        }

        if radius is not None:
            dial_config["radius"] = radius

        if font_name is not None:
            dial_config["font_name"] = font_name

        if font_size is not None:
            dial_config["font_size"] = font_size

        if font_variation is not None:
            dial_config["font_variation"] = font_variation

        self.config["dial"] = dial_config

    def export(self, output_path: str) -> None:
        """Export the configuration to a YAML file.

        Parameters
        ----------
        output_path : str
            Path to save the YAML configuration file.
        """

        class CustomDumper(yaml.SafeDumper):
            pass

        def represent_list(dumper, data):
            if isinstance(data, list) and len(data) == 2:
                if all(isinstance(item, list) and len(item) == 2 for item in data):
                    return dumper.represent_sequence(
                        "tag:yaml.org,2002:seq", data, flow_style=True
                    )
                elif all(isinstance(item, int) for item in data):
                    return dumper.represent_sequence(
                        "tag:yaml.org,2002:seq", data, flow_style=True
                    )
            return dumper.represent_sequence(
                "tag:yaml.org,2002:seq", data, flow_style=False
            )

        CustomDumper.add_representer(list, represent_list)

        with open(output_path, "w") as f:
            yaml.dump(
                self.config,
                f,
                Dumper=CustomDumper,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )

    def _process_config_for_export(self, config: dict[str, Any]) -> dict[str, Any]:
        """Process configuration to use flow style for merge arrays."""
        return config

    def export_grid(
        self,
        grid: Any,
        output_path: str,
        include_fonts: bool = True,
        include_image: bool = True,
    ) -> None:
        """Export a TextGrid object to YAML configuration.

        Parameters
        ----------
        grid : TextGrid
            TextGrid object to export.
        output_path : str
            Path to save the YAML configuration file.
        include_fonts : bool, default=True
            Whether to include font configuration.
        include_image : bool, default=True
            Whether to include image configuration.

        Notes
        -----
        Text content is automatically exported from the grid's content_items.
        Only text items are exported to the grid configuration.
        """
        if include_fonts:
            fm = grid.image_drawer.font_manager
            self.add_fonts(
                fontdirs=fm.fontdirs if fm.fontdirs else None,
                default_size=fm.default_font_size,
                default_name=fm.default_font_name,
            )

        if include_image:
            img = grid.image_drawer.image_handler.image
            width, height = img.size
            self.add_image(
                width=width,
                height=height,
                mode=grid.image_drawer.image_handler.mode,
                background=grid.image_drawer.image_handler.background,
            )

        merges = []
        seen_merges = set()
        for _cell_coord, (start, end) in grid.merged_cells.items():
            merge_key = (start, end)
            if merge_key not in seen_merges:
                seen_merges.add(merge_key)
                merges.append((start, end))

        texts = None
        if hasattr(grid, "content_items") and grid.content_items:
            text_items = [
                item for item in grid.content_items if item.get("type") == "text"
            ]
            if text_items:
                texts = []
                for item in text_items:
                    text_config = item.copy()
                    text_config.pop("type", None)
                    texts.append(text_config)

        self.add_grid(
            rows=grid.rows,
            columns=grid.cols,
            margin_x=grid.margin_x,
            margin_y=grid.margin_y,
            merges=merges if merges else None,
            texts=texts,
        )

        self.export(output_path)

    def get_config(self) -> dict[str, Any]:
        """Get the current configuration dictionary.

        Returns
        -------
        dict
            The configuration dictionary.
        """
        return self.config
