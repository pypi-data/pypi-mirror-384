"""YAML configuration loading for piltext image creation.

This module provides the ConfigLoader class for loading image, font, and grid
configurations from YAML files and creating corresponding piltext objects.
"""

from typing import Any, Optional

import yaml

from .font_manager import FontManager
from .image_dial import ImageDial
from .image_drawer import ImageDrawer
from .image_squares import ImageSquares
from .text_grid import TextGrid


class ConfigLoader:
    """Loads and processes YAML configuration files for image creation.

    ConfigLoader reads YAML configuration files and creates configured FontManager,
    ImageDrawer, and TextGrid objects. It supports font downloads, grid layouts,
    and image transformations defined in the configuration.

    Parameters
    ----------
    config_path : str
        Path to the YAML configuration file.

    Attributes
    ----------
    config : dict
        Parsed YAML configuration dictionary.

    Examples
    --------
    >>> loader = ConfigLoader("config.yaml")
    >>> image = loader.render(output_path="output.png")

    Notes
    -----
    The YAML configuration file should contain sections for:
    - fonts: Font directories, default font, and downloads
    - image: Image dimensions, mode, background, and transformations
    - grid: Grid layout, margins, merges, and text content
    - squares: Square grid visualization for percentage representation
    - dial: Circular gauge/dial visualization for percentage display
    """

    def __init__(self, config_path: str) -> None:
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def create_font_manager(self) -> FontManager:
        """Create a FontManager from the configuration.

        Reads the 'fonts' section of the configuration and creates a FontManager
        with the specified directories, default font, and font downloads.

        Returns
        -------
        FontManager
            Configured FontManager instance with downloaded fonts.

        Notes
        -----
        Font downloads support two formats:

        - Direct URL: {"url": "https://..."}
        - Google Fonts: {"part1": "ofl", "part2": "roboto",
          "font_name": "Roboto-Regular.ttf"}
        """
        font_config = self.config.get("fonts", {})
        fontdirs = font_config.get("directories")
        default_font_size = font_config.get("default_size", 15)
        default_font_name = font_config.get("default_name")

        fm = FontManager(
            fontdirs=fontdirs,
            default_font_size=default_font_size,
            default_font_name=default_font_name,
        )

        downloads = font_config.get("download", [])
        for download in downloads:
            if "url" in download:
                fm.download_font(download["url"])
            elif all(k in download for k in ["part1", "part2", "font_name"]):
                fm.download_google_font(
                    download["part1"], download["part2"], download["font_name"]
                )

        return fm

    def create_image_drawer(
        self, font_manager: Optional[FontManager] = None
    ) -> ImageDrawer:
        """Create an ImageDrawer from the configuration.

        Reads the 'image' section of the configuration and creates an ImageDrawer
        with the specified dimensions, mode, and background color.

        Parameters
        ----------
        font_manager : FontManager, optional
            FontManager to use. If None, creates a new one from the configuration.

        Returns
        -------
        ImageDrawer
            Configured ImageDrawer instance ready for drawing.
        """
        image_config = self.config.get("image", {})
        width = image_config.get("width", 480)
        height = image_config.get("height", 280)
        mode = image_config.get("mode", "RGB")
        background = image_config.get("background", "white")

        if font_manager is None:
            font_manager = self.create_font_manager()

        image_drawer = ImageDrawer(width, height, mode, background, font_manager)

        return image_drawer

    def create_grid(
        self,
        image_drawer: Optional[ImageDrawer] = None,
        font_manager: Optional[FontManager] = None,
    ) -> Optional[TextGrid]:
        """Create a TextGrid from the configuration.

        Reads the 'grid' section of the configuration and creates a TextGrid
        with the specified layout, margins, and cell merges.

        Parameters
        ----------
        image_drawer : ImageDrawer, optional
            ImageDrawer to use for the grid. If None, creates a new one.
        font_manager : FontManager, optional
            FontManager to use. If None and image_drawer is None, creates a new one.

        Returns
        -------
        TextGrid or None
            Configured TextGrid instance, or None if no grid configuration exists.

        Notes
        -----
        Cell merges should be specified as a list of
        [[start_row, start_col], [end_row, end_col]] pairs.
        """
        grid_config = self.config.get("grid")
        if not grid_config:
            return None

        if image_drawer is None:
            image_drawer = self.create_image_drawer(font_manager)

        rows = grid_config.get("rows", 1)
        columns = grid_config.get("columns", 1)
        margin_x = grid_config.get("margin_x", 0)
        margin_y = grid_config.get("margin_y", 0)

        grid = TextGrid(rows, columns, image_drawer, margin_x, margin_y)

        merge_list = grid_config.get("merge", [])
        if merge_list:
            formatted_merge = []
            for merge_item in merge_list:
                if isinstance(merge_item, list) and len(merge_item) == 2:
                    start = tuple(merge_item[0])
                    end = tuple(merge_item[1])
                    formatted_merge.append((start, end))
            if formatted_merge:
                grid.merge_bulk(formatted_merge)

        return grid

    def create_squares(
        self, font_manager: Optional[FontManager] = None
    ) -> Optional[ImageSquares]:
        """Create an ImageSquares from the configuration.

        Reads the 'squares' section of the configuration and creates an ImageSquares
        instance for waffle chart-style percentage visualization.

        Parameters
        ----------
        font_manager : FontManager, optional
            FontManager to use. If None, creates a new one from the configuration.

        Returns
        -------
        ImageSquares or None
            Configured ImageSquares instance, or None if no squares configuration
            exists.
        """
        squares_config = self.config.get("squares")
        if not squares_config:
            return None

        if font_manager is None:
            font_manager = self.create_font_manager()

        percentage = squares_config.get("percentage", 0.0)
        max_squares = squares_config.get("max_squares", 100)
        size = squares_config.get("size", 200)
        bg_color = squares_config.get("bg_color", "white")
        fg_color = squares_config.get("fg_color", "#4CAF50")
        empty_color = squares_config.get("empty_color", "#e0e0e0")
        gap = squares_config.get("gap", 2)
        rows = squares_config.get("rows")
        columns = squares_config.get("columns")
        border_width = squares_config.get("border_width", 1)
        border_color = squares_config.get("border_color", "#cccccc")
        show_partial = squares_config.get("show_partial", True)

        squares = ImageSquares(
            percentage=percentage,
            font_manager=font_manager,
            max_squares=max_squares,
            size=size,
            bg_color=bg_color,
            fg_color=fg_color,
            empty_color=empty_color,
            gap=gap,
            rows=rows,
            columns=columns,
            border_width=border_width,
            border_color=border_color,
            show_partial=show_partial,
        )

        return squares

    def create_dial(
        self, font_manager: Optional[FontManager] = None
    ) -> Optional[ImageDial]:
        """Create an ImageDial from the configuration.

        Reads the 'dial' section of the configuration and creates an ImageDial
        instance for circular gauge-style percentage visualization.

        Parameters
        ----------
        font_manager : FontManager, optional
            FontManager to use. If None, creates a new one from the configuration.

        Returns
        -------
        ImageDial or None
            Configured ImageDial instance, or None if no dial configuration exists.
        """
        dial_config = self.config.get("dial")
        if not dial_config:
            return None

        if font_manager is None:
            font_manager = self.create_font_manager()

        percentage = dial_config.get("percentage", 0.0)
        size = dial_config.get("size", 200)
        radius = dial_config.get("radius")
        bg_color = dial_config.get("bg_color", "white")
        fg_color = dial_config.get("fg_color", "#4CAF50")
        track_color = dial_config.get("track_color", "#e0e0e0")
        thickness = dial_config.get("thickness", 20)
        font_name = dial_config.get("font_name")
        font_size = dial_config.get("font_size")
        font_variation = dial_config.get("font_variation")
        show_needle = dial_config.get("show_needle", True)
        show_ticks = dial_config.get("show_ticks", True)
        show_value = dial_config.get("show_value", True)
        start_angle = dial_config.get("start_angle", -135)
        end_angle = dial_config.get("end_angle", 135)

        dial = ImageDial(
            percentage=percentage,
            font_manager=font_manager,
            size=size,
            radius=radius,
            bg_color=bg_color,
            fg_color=fg_color,
            track_color=track_color,
            thickness=thickness,
            font_name=font_name,
            font_size=font_size,
            font_variation=font_variation,
            show_needle=show_needle,
            show_ticks=show_ticks,
            show_value=show_value,
            start_angle=start_angle,
            end_angle=end_angle,
        )

        return dial

    def render(self, output_path: Optional[str] = None) -> Any:
        """Render the complete image from the configuration.

        Creates all configured objects (FontManager, ImageDrawer, TextGrid,
        ImageSquares, or ImageDial), renders the content, applies transformations,
        and optionally saves the result to a file.

        Parameters
        ----------
        output_path : str, optional
            Path to save the rendered image. If None, the image is not saved
            to disk.

        Returns
        -------
        PIL.Image.Image
            The rendered image with all text and transformations applied.

        Notes
        -----
        Priority: dial > squares > grid > basic image
        """
        font_manager = self.create_font_manager()

        dial = self.create_dial(font_manager)
        if dial:
            img = dial.render()
            if output_path:
                img.save(output_path)
            return img

        squares = self.create_squares(font_manager)
        if squares:
            img = squares.render()
            if output_path:
                img.save(output_path)
            return img

        image_drawer = self.create_image_drawer(font_manager)

        grid = self.create_grid(image_drawer, font_manager)

        if grid:
            grid_config = self.config.get("grid", {})
            text_list = grid_config.get("texts", [])
            if text_list:
                for text_item in text_list:
                    if "start" in text_item and isinstance(text_item["start"], list):
                        text_item["start"] = tuple(text_item["start"])
                    if "end" in text_item and isinstance(text_item["end"], list):
                        text_item["end"] = tuple(text_item["end"])

                    if "dial" in text_item:
                        dial_spec = text_item.pop("dial")
                        start = text_item.pop("start")
                        end = text_item.pop("end", None)
                        anchor = text_item.pop("anchor", "mm")
                        grid.set_dial(start, end=end, anchor=anchor, **dial_spec)
                    elif "squares" in text_item:
                        squares_spec = text_item.pop("squares")
                        start = text_item.pop("start")
                        end = text_item.pop("end", None)
                        anchor = text_item.pop("anchor", "mm")
                        grid.set_squares(start, end=end, anchor=anchor, **squares_spec)
                    elif "text" in text_item:
                        start = text_item.pop("start")
                        text_str = text_item.pop("text")
                        grid.set_text(start, text_str, **text_item)

        image_config = self.config.get("image", {})
        mirror = image_config.get("mirror", False)
        orientation = image_config.get("orientation", 0)
        inverted = image_config.get("inverted", False)

        image_drawer.finalize(mirror=mirror, orientation=orientation, inverted=inverted)

        if output_path:
            image_drawer.image_handler.image.save(output_path)

        return image_drawer.get_image()
