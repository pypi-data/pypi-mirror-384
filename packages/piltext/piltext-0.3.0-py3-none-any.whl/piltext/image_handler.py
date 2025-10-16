"""Basic image creation and manipulation utilities.

This module provides the ImageHandler class for creating PIL images with
specified dimensions, modes, and backgrounds, along with basic transformation
operations like mirroring, rotation, and color inversion.
"""

from typing import Any, Optional

from PIL import Image, ImageOps


class ImageHandler:
    """Handles image creation and basic transformations.

    ImageHandler provides a simple interface for creating PIL images with
    configurable dimensions, color modes, and backgrounds. It supports common
    transformations including rotation, mirroring, and color inversion.

    Parameters
    ----------
    width : int
        Width of the image in pixels.
    height : int
        Height of the image in pixels.
    mode : str, default="RGB"
        PIL image mode. Common modes:
        - "RGB": 24-bit true color (supports colors)
        - "RGBA": 24-bit true color with alpha channel
        - "L": 8-bit grayscale (black and white)
        - "1": 1-bit binary (black and white only)
    background : Any, default="white"
        Background color of the image. Can be:
        - Color name (e.g., "white", "black", "red")
        - Hex color code (e.g., "#FFFFFF", "#000000")
        - RGB tuple for RGB/RGBA modes (e.g., (255, 255, 255))
        - Integer value for grayscale mode (0-255)

    Attributes
    ----------
    width : int
        Current width of the image in pixels.
    height : int
        Current height of the image in pixels.
    mode : str
        Current PIL image mode.
    background : Any
        Current background color.
    image : PIL.Image.Image
        The PIL Image object.

    Examples
    --------
    >>> handler = ImageHandler(800, 600, mode="RGB", background="white")
    >>> handler.apply_transformations(mirror=True, orientation=90)
    >>> handler.show()
    """

    def __init__(
        self, width: int, height: int, mode: str = "RGB", background: Any = "white"
    ) -> None:
        self.width = width
        self.height = height
        self.mode = mode
        self.background = background
        self.image: Image.Image
        self.initialize()

    def initialize(self) -> None:
        """Create a new blank image with current settings.

        Initializes a new PIL Image with the configured width, height, mode,
        and background color. Any existing image content is replaced.
        """
        self.image = Image.new(self.mode, (self.width, self.height), self.background)

    def change_size(self, width: int, height: int) -> None:
        """Change the image dimensions and reinitialize.

        Updates the width and height properties and creates a new blank image
        with the new dimensions. All existing image content is lost.

        Parameters
        ----------
        width : int
            New width in pixels.
        height : int
            New height in pixels.
        """
        self.width = width
        self.height = height
        self.initialize()  # Reinitialize the image with the new size

    def apply_transformations(
        self, mirror: bool = False, orientation: int = 0, inverted: bool = False
    ) -> None:
        """Apply geometric and color transformations to the image.

        Applies one or more transformations to the image in the following order:
        rotation, mirroring, then color inversion.

        Parameters
        ----------
        mirror : bool, default=False
            If True, mirrors the image horizontally (left-right flip).
        orientation : int, default=0
            Rotation angle in degrees counter-clockwise. Common values are
            0, 90, 180, 270. The image is expanded to fit the rotated content.
        inverted : bool, default=False
            If True, inverts all pixel colors (negative image).
        """
        if orientation:
            self.image = self.image.rotate(orientation, expand=True)
        if mirror:
            self.image = ImageOps.mirror(self.image)
        if inverted:
            self.image = ImageOps.invert(self.image)

    def show(self, title: Optional[str] = None) -> None:
        """Display the image in the default image viewer.

        Opens the image in the system's default image viewing application.

        Parameters
        ----------
        title : str, optional
            Window title for the image viewer. Note that not all PIL versions
            or platforms support setting the window title.
        """
        # PIL.Image.show() does not accept 'title' in all versions
        if title is not None:
            try:
                self.image.show(title=title)
            except TypeError:
                self.image.show()
        else:
            self.image.show()

    def paste(
        self, im: Any, box: Optional[tuple] = None, mask: Optional[Any] = None
    ) -> None:
        """Paste another image onto the current image.

        Composites another image onto this image at the specified position,
        optionally using a mask for transparency.

        Parameters
        ----------
        im : PIL.Image.Image or Any
            Source image to paste.
        box : tuple of (int, int) or tuple of (int, int, int, int), optional
            Position to paste the image. Can be:
            - (x, y): Top-left corner position
            - (x1, y1, x2, y2): Bounding box for the pasted region
            If None, defaults to (0, 0).
        mask : PIL.Image.Image or Any, optional
            Mask image for transparency. Must be mode '1', 'L', or 'RGBA'.
            If None, the entire source image is pasted opaquely.
        """
        self.image.paste(im, box=box, mask=mask)
