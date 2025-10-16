"""Text box handling and fitting for precise text rendering.

This module provides the TextBox class for managing individual text elements,
including automatic font size fitting and text wrapping.
"""

from typing import Any, Optional

from PIL import ImageDraw

from .font_manager import FontManager


class TextBox:
    """Handles single text box creation and manipulation.

    TextBox manages a single text element with automatic font sizing to fit
    within specified dimensions and text wrapping capabilities.

    Parameters
    ----------
    text : str
        Text content to render.
    font_manager : FontManager
        FontManager instance for font operations.

    Attributes
    ----------
    text : str
        The text content.
    font_manager : FontManager
        FontManager instance used for font operations.

    Examples
    --------
    >>> from PIL import Image, ImageDraw
    >>> fm = FontManager()
    >>> text_box = TextBox("Hello World", fm)
    >>> img = Image.new("RGB", (200, 100), "white")
    >>> draw = ImageDraw.Draw(img)
    >>> font = text_box.fit_text(draw, 180, 80, font_name="Arial")
    >>> text_box.draw_text(draw, (10, 10), font, fill="black")
    """

    def __init__(self, text: str, font_manager: FontManager) -> None:
        self.text = text
        self.font_manager = font_manager

    def fit_text(
        self,
        draw: ImageDraw.ImageDraw,
        max_width: int,
        max_height: int,
        font_name: Optional[str] = None,
        font_variation: Optional[str] = None,
        start_font_size: int = 1,
    ) -> Any:
        """Find the largest font size that fits within given dimensions.

        Incrementally tests font sizes to find the maximum size where the text
        fits within the specified width and height constraints.

        Parameters
        ----------
        draw : PIL.ImageDraw.ImageDraw
            ImageDraw object for text measurement.
        max_width : int
            Maximum width in pixels.
        max_height : int
            Maximum height in pixels.
        font_name : str, optional
            Name of the font to use. If None, uses the default font.
        font_variation : str, optional
            Named variation for variable fonts (e.g., 'Bold', 'Italic').
        start_font_size : int, default=1
            Initial font size to start testing from.

        Returns
        -------
        PIL.ImageFont.FreeTypeFont
            Font object at the largest size that fits within the constraints.
        """
        font_size = start_font_size
        font = self.font_manager.build_font(
            font_name, font_size, variation_name=font_variation
        )
        while True:
            width, height = self.font_manager.calculate_text_size(draw, self.text, font)
            if width > max_width or height > max_height:
                font_size -= 1
                if font_size < 1:
                    font_size = 1
                return self.font_manager.build_font(
                    font_name, font_size, variation_name=font_variation
                )
            font_size += 1
            font = self.font_manager.build_font(
                font_name, font_size, variation_name=font_variation
            )

    def draw_text(
        self, draw: ImageDraw.ImageDraw, xy: tuple[int, int], font: Any, **kwargs: Any
    ) -> None:
        """Draw the text on an image.

        Renders the text at the specified position using the provided font.

        Parameters
        ----------
        draw : PIL.ImageDraw.ImageDraw
            ImageDraw object to draw on.
        xy : tuple of (int, int)
            Position (x, y) for the text anchor point.
        font : PIL.ImageFont.FreeTypeFont
            Font object to use for rendering.
        **kwargs : dict
            Additional keyword arguments passed to PIL's text method
            (e.g., fill, stroke_width, stroke_fill, anchor, align).
        """
        draw.text(xy, self.text, font=font, **kwargs)

    def get_wrapped_text_lines(
        self, draw: ImageDraw.ImageDraw, text: str, font: Any, max_width: int
    ) -> list[str]:
        """Wrap text into multiple lines to fit within a maximum width.

        Splits text by words and creates lines that fit within the specified
        width constraint. Uses greedy wrapping (adds words until line is full).

        Parameters
        ----------
        draw : PIL.ImageDraw.ImageDraw
            ImageDraw object for text measurement.
        text : str
            Text string to wrap.
        font : PIL.ImageFont.FreeTypeFont
            Font object to use for measuring text width.
        max_width : int
            Maximum width in pixels for each line.

        Returns
        -------
        list of str
            List of text lines that fit within the maximum width.

        Notes
        -----
        Words that are longer than max_width will be placed on their own line
        and may exceed the width constraint.
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            w, _ = self.font_manager.calculate_text_size(draw, test_line, font)
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines
