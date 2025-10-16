"""
Dial (gauge) image creation.

This module provides the ImageDial class for creating circular gauge/dial
images that display percentage values. Dials can include needles, tick marks,
and customizable styling.

Examples
--------
Create a simple dial showing 75%:

>>> from piltext import FontManager, ImageDial
>>> fm = FontManager()
>>> dial = ImageDial(0.75, fm, size=300)
>>> img = dial.render()
>>> img.save("dial.png")

Create a custom styled dial:

>>> dial = ImageDial(
...     percentage=0.85,
...     font_manager=fm,
...     size=400,
...     fg_color="#FF5722",
...     track_color="#CCCCCC",
...     thickness=30,
...     show_needle=True,
...     show_ticks=True
... )
>>> img = dial.render()
"""

import math
from typing import Optional

from PIL import Image

from .font_manager import FontManager
from .image_drawer import ImageDrawer


class ImageDial:
    """
    Create a circular dial (gauge) image representing a percentage value.

    ImageDial creates customizable gauge visualizations with optional needles,
    tick marks, and labels. The dial shows a percentage value as a filled arc
    around a circle.

    Parameters
    ----------
    percentage : float
        Value to display, ranging from 0.0 to 1.0. Values outside this range
        are clamped.
    font_manager : FontManager
        Font manager for text rendering.
    size : int, optional
        Size of the output image in pixels (width and height). Default is 200.
    radius : int, optional
        Radius of the dial arc. If None, calculated automatically based on size.
    bg_color : str, optional
        Background color. Default is 'white'.
    fg_color : str, optional
        Foreground arc color indicating the filled portion. Default is '#4CAF50'.
    track_color : str, optional
        Track (background arc) color. Default is '#e0e0e0'.
    thickness : int, optional
        Thickness of the dial arc in pixels. Default is 20.
    font_name : str, optional
        Font name for text labels. Uses FontManager default if None.
    font_size : int, optional
        Font size for text labels. If None, calculated based on image size.
    font_variation : str, optional
        Font variation (e.g., 'Bold', 'Italic').
    show_needle : bool, optional
        Whether to show a needle pointing to the current value. Default is True.
    show_ticks : bool, optional
        Whether to show tick marks and labels. Default is True.
    show_value : bool, optional
        Whether to show the percentage value in the center. Default is True.
    start_angle : int, optional
        Starting angle of the dial in degrees. Default is -135 (lower left).
    end_angle : int, optional
        Ending angle of the dial in degrees. Default is 135 (lower right).

    Attributes
    ----------
    percentage : float
        Clamped percentage value (0.0 to 1.0).
    size : int
        Image size in pixels.
    radius : int or None
        Dial radius.

    Examples
    --------
    Create a basic dial:

    >>> from piltext import FontManager, ImageDial
    >>> fm = FontManager()
    >>> dial = ImageDial(0.65, fm)
    >>> img = dial.render()

    Create a half-circle dial:

    >>> dial = ImageDial(
    ...     percentage=0.5,
    ...     font_manager=fm,
    ...     start_angle=-180,
    ...     end_angle=0,
    ...     fg_color='blue'
    ... )
    """

    def __init__(
        self,
        percentage: float,
        font_manager: FontManager,
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
    ):
        self.percentage = max(0.0, min(1.0, percentage))
        self.font_manager = font_manager
        self.size = size
        self.radius = radius
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.track_color = track_color
        self.thickness = thickness
        self.font_name = font_name
        self.font_size = font_size
        self.font_variation = font_variation
        self.show_needle = show_needle
        self.show_ticks = show_ticks
        self.show_value = show_value
        self.start_angle = start_angle
        self.end_angle = end_angle

    def render(self) -> Image.Image:
        """
        Render the dial as a PIL Image.

        Returns
        -------
        PIL.Image.Image
            The rendered dial image.

        Examples
        --------
        >>> dial = ImageDial(0.8, font_manager)
        >>> img = dial.render()
        >>> img.save("output.png")
        """
        # Create an image drawer with the specified size
        drawer = ImageDrawer(self.size, self.size, font_manager=self.font_manager)

        # Fill background
        drawer.draw.rectangle([0, 0, self.size, self.size], fill=self.bg_color)

        # Draw the dial elements
        self._draw_dial(drawer)

        # Return the final image
        return drawer.get_image()

    def _draw_dial(self, drawer: ImageDrawer) -> None:
        """
        Draw the dial components on the image.

        Parameters
        ----------
        drawer : ImageDrawer
            The image drawer to use for rendering.

        Notes
        -----
        Draws the track arc, foreground arc, needle (if enabled),
        tick marks (if enabled), and center value (if enabled).
        """
        # Calculate dimensions
        margin = self.thickness // 2 + 5
        center_x = self.size // 2
        center_y = self.size // 2

        # Use custom radius if provided, otherwise calculate based on size
        if self.radius is not None:
            radius = self.radius
        else:
            radius = (self.size - 2 * margin) // 2

        # Calculate bounding box for the dial based on radius
        bbox = [
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ]

        # Angle definitions
        start_angle = self.start_angle
        end_angle = self.end_angle
        sweep = end_angle - start_angle

        # Draw track (background arc)
        drawer.draw.arc(
            bbox,
            start=start_angle,
            end=end_angle,
            fill=self.track_color,
            width=self.thickness,
        )

        # Draw foreground arc (percentage)
        if self.percentage > 0:
            arc_end = start_angle + self.percentage * sweep
            drawer.draw.arc(
                bbox,
                start=start_angle,
                end=arc_end,
                fill=self.fg_color,
                width=self.thickness,
            )

        # Draw needle
        if self.show_needle:
            needle_angle = start_angle + self.percentage * sweep
            self._draw_needle(drawer, center_x, center_y, radius, needle_angle)

        # Draw tick marks
        if self.show_ticks:
            self._draw_ticks(drawer, center_x, center_y, radius, start_angle, end_angle)

        # Draw percentage value in the center
        if self.show_value:
            value_text = f"{int(self.percentage * 100)}%"
            font_size = self.font_size or max(10, self.size // 10)
            try:
                drawer.draw_text(
                    value_text,
                    (center_x, center_y),
                    font_size=font_size,
                    font_name=self.font_name,
                    font_variation=self.font_variation,
                    fill="black",
                    anchor="mm",  # Center the text
                )
            except Exception:
                # If text drawing fails, continue without text
                pass

    def _draw_ticks(
        self,
        drawer: ImageDrawer,
        cx: int,
        cy: int,
        radius: int,
        start_angle: int,
        end_angle: int,
    ) -> None:
        """
        Draw tick marks and labels around the dial.

        Parameters
        ----------
        drawer : ImageDrawer
            The image drawer to use.
        cx : int
            Center x coordinate.
        cy : int
            Center y coordinate.
        radius : int
            Dial radius.
        start_angle : int
            Starting angle in degrees.
        end_angle : int
            Ending angle in degrees.

        Notes
        -----
        Draws 5 major ticks with labels (0, 25, 50, 75, 100) and
        minor ticks between them.
        """
        # Draw major and minor ticks
        major_ticks = 5  # Number of major ticks (including start and end)
        minor_per_major = 4  # Number of minor ticks between major ticks

        sweep = end_angle - start_angle

        # Draw major ticks and labels
        for i in range(major_ticks):
            angle_rad = math.radians(start_angle + (i / (major_ticks - 1)) * sweep)

            # Tick coordinates - outer end
            outer_x = cx + int((radius + 5) * math.cos(angle_rad))
            outer_y = cy + int((radius + 5) * math.sin(angle_rad))

            # Tick coordinates - inner end
            inner_x = cx + int((radius - 10) * math.cos(angle_rad))
            inner_y = cy + int((radius - 10) * math.sin(angle_rad))

            # Draw major tick
            drawer.draw.line(
                [(outer_x, outer_y), (inner_x, inner_y)], fill="black", width=2
            )

            # Draw label
            label_value = int((i / (major_ticks - 1)) * 100)
            label_x = cx + int((radius + 20) * math.cos(angle_rad))
            label_y = cy + int((radius + 20) * math.sin(angle_rad))

            font_size = self.font_size or max(8, self.size // 20)
            try:
                drawer.draw_text(
                    str(label_value),
                    (label_x, label_y),
                    font_size=font_size,
                    font_name=self.font_name,
                    font_variation=self.font_variation,
                    fill="black",
                    anchor="mm",
                )
            except Exception:
                # If text drawing fails, continue without labels
                pass

        # Draw minor ticks
        total_segments = (major_ticks - 1) * minor_per_major
        for i in range(1, total_segments):
            if i % minor_per_major == 0:
                continue  # Skip positions where major ticks are

            angle_rad = math.radians(start_angle + (i / total_segments) * sweep)

            # Tick coordinates
            outer_x = cx + int((radius + 2) * math.cos(angle_rad))
            outer_y = cy + int((radius + 2) * math.sin(angle_rad))

            inner_x = cx + int((radius - 5) * math.cos(angle_rad))
            inner_y = cy + int((radius - 5) * math.sin(angle_rad))

            # Draw minor tick
            drawer.draw.line(
                [(outer_x, outer_y), (inner_x, inner_y)], fill="gray", width=1
            )

    def _draw_needle(
        self, drawer: ImageDrawer, cx: int, cy: int, radius: int, angle: float
    ) -> None:
        """
        Draw a needle pointing to the current percentage value.

        Parameters
        ----------
        drawer : ImageDrawer
            The image drawer to use.
        cx : int
            Center x coordinate.
        cy : int
            Center y coordinate.
        radius : int
            Dial radius.
        angle : float
            Angle in degrees where the needle should point.

        Notes
        -----
        The needle is drawn as a red line from the center to a point
        on the dial, with a black circular pivot at the center.
        """
        angle_rad = math.radians(angle)

        # Calculate needle coordinates
        needle_length = radius - self.thickness // 2 - 10
        needle_x = cx + int(needle_length * math.cos(angle_rad))
        needle_y = cy + int(needle_length * math.sin(angle_rad))

        # Draw needle line
        drawer.draw.line([(cx, cy), (needle_x, needle_y)], fill="red", width=3)

        # Draw needle pivot (center circle)
        pivot_radius = max(4, self.size // 30)
        drawer.draw.ellipse(
            [
                (cx - pivot_radius, cy - pivot_radius),
                (cx + pivot_radius, cy + pivot_radius),
            ],
            fill="black",
            outline="gray",
        )
