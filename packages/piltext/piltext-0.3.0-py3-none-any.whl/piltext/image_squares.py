"""
Grid-of-squares visualization for percentage representation.

This module provides the ImageSquares class for creating visualizations that
represent percentage values using grids of filled and empty squares. This is
useful for creating waffle charts or similar percentage indicators.

Examples
--------
Create a basic squares visualization showing 65%:

>>> from piltext import FontManager, ImageSquares
>>> fm = FontManager()
>>> squares = ImageSquares(0.65, fm, max_squares=100)
>>> img = squares.render()
>>> img.save("squares.png")

Create a custom 10x10 grid:

>>> squares = ImageSquares(
...     percentage=0.42,
...     font_manager=fm,
...     max_squares=100,
...     rows=10,
...     columns=10,
...     fg_color="#FF5722",
...     gap=3
... )
>>> img = squares.render()
"""

import math
from typing import Optional

from PIL import Image

from .font_manager import FontManager
from .image_drawer import ImageDrawer


class ImageSquares:
    """
    Create a grid of squares representing a percentage value.

    ImageSquares creates waffle chart-style visualizations where a grid of
    squares is filled proportionally to represent a percentage. Supports
    partial filling of the last square and customizable grid dimensions.

    Parameters
    ----------
    percentage : float
        Value to display, ranging from 0.0 to 1.0. Values outside this range
        are clamped.
    font_manager : FontManager
        Font manager for text rendering (if needed).
    max_squares : int, optional
        Total number of squares in the grid. Default is 100.
    size : int, optional
        Approximate size of the output image in pixels. Default is 200.
    bg_color : str, optional
        Background color. Default is 'white'.
    fg_color : str, optional
        Color for filled squares. Default is '#4CAF50'.
    empty_color : str, optional
        Color for empty squares. Default is '#e0e0e0'.
    gap : int, optional
        Gap between squares in pixels. Default is 2.
    rows : int, optional
        Number of rows. If None, calculated to make grid as square as possible.
    columns : int, optional
        Number of columns. If None, calculated to make grid as square as possible.
    border_width : int, optional
        Border width for each square in pixels. Default is 1.
    border_color : str, optional
        Border color for squares. Default is '#cccccc'.
    show_partial : bool, optional
        Whether to partially fill the last square. Default is True.

    Attributes
    ----------
    percentage : float
        Clamped percentage value (0.0 to 1.0).
    max_squares : int
        Total number of squares.
    rows : int
        Number of rows in the grid.
    columns : int
        Number of columns in the grid.
    square_size : int
        Size of each square in pixels.

    Examples
    --------
    Create a 10x10 grid showing 75%:

    >>> from piltext import FontManager, ImageSquares
    >>> fm = FontManager()
    >>> squares = ImageSquares(0.75, fm, max_squares=100, rows=10, columns=10)
    >>> img = squares.render()

    Create a custom styled grid:

    >>> squares = ImageSquares(
    ...     percentage=0.5,
    ...     font_manager=fm,
    ...     max_squares=50,
    ...     fg_color='blue',
    ...     empty_color='lightblue',
    ...     gap=5,
    ...     show_partial=False
    ... )
    """

    def __init__(
        self,
        percentage: float,
        font_manager: FontManager,
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
    ):
        self.percentage = max(0.0, min(1.0, percentage))
        self.font_manager = font_manager
        self.max_squares = max_squares
        self.size = size
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.empty_color = empty_color
        self.gap = gap
        self.border_width = border_width
        self.border_color = border_color
        self.show_partial = show_partial

        # Calculate the number of rows and columns based on max_squares
        # If not specified, try to make it as square as possible
        if rows is not None and columns is not None:
            self.rows = rows
            self.columns = columns
        elif rows is not None:
            self.rows = rows
            self.columns = math.ceil(max_squares / rows)
        elif columns is not None:
            self.columns = columns
            self.rows = math.ceil(max_squares / columns)
        else:
            # Make it as square as possible
            self.columns = math.ceil(math.sqrt(max_squares))
            self.rows = math.ceil(max_squares / self.columns)

        # Calculate the square size based on the overall size and grid dimensions
        self.square_size = (self.size - ((self.columns + 1) * self.gap)) // self.columns

    def render(self) -> Image.Image:
        """
        Render the squares visualization as a PIL Image.

        Returns
        -------
        PIL.Image.Image
            The rendered grid of squares image.

        Examples
        --------
        >>> squares = ImageSquares(0.6, font_manager)
        >>> img = squares.render()
        >>> img.save("output.png")
        """
        # Calculate the actual width and height needed based on number of squares
        # and their size with gaps
        actual_width = (self.square_size * self.columns) + (
            (self.columns + 1) * self.gap
        )
        actual_height = (self.square_size * self.rows) + ((self.rows + 1) * self.gap)

        # Add space at bottom for percentage value if showing
        value_height = 0
        total_height = actual_height + value_height

        # Create an image drawer with the calculated dimensions
        drawer = ImageDrawer(actual_width, total_height, font_manager=self.font_manager)

        # Fill background
        drawer.draw.rectangle([0, 0, actual_width, total_height], fill=self.bg_color)

        # Draw the squares
        self._draw_squares(drawer)

        # Return the final image
        return drawer.get_image()

    def _draw_squares(self, drawer: ImageDrawer) -> None:
        """
        Draw the grid of squares on the image.

        Parameters
        ----------
        drawer : ImageDrawer
            The image drawer to use for rendering.

        Notes
        -----
        Calculates how many squares to fill based on the percentage,
        including partial filling of the last square if enabled.
        Squares are filled left-to-right, top-to-bottom.
        """
        # Calculate how many squares should be filled based on percentage
        filled_squares = self.percentage * self.max_squares
        full_squares = math.floor(filled_squares)
        partial_square_value = filled_squares - full_squares

        # Draw all the squares
        for i in range(self.rows):
            for j in range(self.columns):
                # Calculate the square index
                index = i * self.columns + j

                # Skip if we've exceeded max_squares
                if index >= self.max_squares:
                    break

                # Calculate position
                x = self.gap + j * (self.square_size + self.gap)
                y = self.gap + i * (self.square_size + self.gap)

                # Determine fill color
                if index < full_squares:
                    fill_color = self.fg_color
                    fill_percentage = 1.0
                elif (
                    index == full_squares
                    and partial_square_value > 0
                    and self.show_partial
                ):
                    fill_color = self.fg_color
                    fill_percentage = partial_square_value
                else:
                    fill_color = self.empty_color
                    fill_percentage = 0.0

                # Draw the square
                if fill_percentage == 1.0:
                    # Draw a complete square
                    drawer.draw.rectangle(
                        [x, y, x + self.square_size, y + self.square_size],
                        fill=fill_color,
                        outline=self.border_color if self.border_width > 0 else None,
                        width=self.border_width,
                    )
                elif fill_percentage > 0:
                    # Draw empty square
                    drawer.draw.rectangle(
                        [x, y, x + self.square_size, y + self.square_size],
                        fill=self.empty_color,
                        outline=self.border_color if self.border_width > 0 else None,
                        width=self.border_width,
                    )

                    # Draw partial filled square (fill from left to right)
                    filled_width = int(self.square_size * fill_percentage)
                    drawer.draw.rectangle(
                        [
                            x + self.border_width,
                            y,
                            x + filled_width,
                            y + self.square_size - self.border_width,
                        ],
                        fill=fill_color,
                        outline=None,
                    )
                else:
                    # Draw an empty square
                    drawer.draw.rectangle(
                        [x, y, x + self.square_size, y + self.square_size],
                        fill=self.empty_color,
                        outline=self.border_color if self.border_width > 0 else None,
                        width=self.border_width,
                    )
