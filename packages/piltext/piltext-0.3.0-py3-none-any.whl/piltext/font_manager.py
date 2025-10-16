"""Font management utilities for text rendering with PIL.

This module provides the FontManager class for handling font loading, caching,
directory management, and Google Fonts integration.
"""

import logging
import os
from functools import lru_cache
from typing import Any, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote
from urllib.request import urlopen

from PIL import ImageFont

_logger = logging.getLogger(__name__)


class FontManager:
    """Manages font loading, caching, and directory handling for text rendering.

    The FontManager handles font file discovery, Google Fonts downloads, font object
    creation with caching, and text size calculations. It supports multiple font
    directories and automatically resolves font paths with common extensions.

    Parameters
    ----------
    fontdirs : str or list of str, optional
        Directory or list of directories to search for fonts. If None, uses the
        platform-specific user font directory.
    default_font_size : int, default=15
        Default font size in points for font rendering.
    default_font_name : str, optional
        Default font name to use when none is specified.

    Attributes
    ----------
    fontdirs : list of str
        List of absolute paths to font directories.
    default_font_name : str or None
        Default font name.
    default_font_size : int
        Default font size in points.

    Examples
    --------
    >>> fm = FontManager(fontdirs="/path/to/fonts", default_font_size=20)
    >>> font = fm.build_font("Arial", font_size=24)
    >>> available = fm.list_available_fonts()

    """

    def __init__(
        self,
        fontdirs: Optional[Union[str, list[str]]] = None,
        default_font_size: int = 15,
        default_font_name: Optional[str] = None,
    ) -> None:
        # Use the default font directory if none provided
        if fontdirs is None:
            default_fontdir = self.get_user_font_dir()
            fontdirs = [default_fontdir]
        elif isinstance(
            fontdirs,
            str,
        ):  # Allow single directory as a string for backward compatibility
            fontdirs = [fontdirs]

        self.fontdirs = [os.path.realpath(fontdir) for fontdir in fontdirs]
        self.default_font_name = default_font_name
        self.default_font_size = default_font_size

        @lru_cache(maxsize=128)
        def _cached_load_font(
            font_path: str, font_size: int, variation_name: str
        ) -> Any:
            font = ImageFont.truetype(font_path, font_size)
            if variation_name != "none":
                font.set_variation_by_name(variation_name)
            return font

        self._cached_load_font = _cached_load_font
        self._cache_lookup: dict[
            tuple[Optional[str], int, str], tuple[str, int, str]
        ] = {}

    @property
    def _font_cache(self) -> dict[tuple[Optional[str], int, str], Any]:
        """Access the font cache for backward compatibility with tests.

        Returns
        -------
        dict
            Dictionary representation of the LRU cache.
        """
        result = {}
        for key, cache_key in self._cache_lookup.items():
            try:
                result[key] = self._cached_load_font(*cache_key)
            except Exception:
                pass
        return result

    def get_user_font_dir(self) -> str:
        """Get the platform-specific user font directory.

        Returns the default font directory for the current operating system and
        creates it if it doesn't exist. On Windows, uses APPDATA/piltext. On
        POSIX systems (macOS/Linux), uses ~/.config/piltext.

        Returns
        -------
        str
            Absolute path to the user font directory.

        Raises
        ------
        OSError
            If the operating system is not supported.

        """
        if os.name == "nt":  # Windows
            font_dir = os.path.join(os.getenv("APPDATA", ""), "piltext")
        elif os.name == "posix":  # macOS and Linux
            font_dir = os.path.join(os.path.expanduser("~"), ".config", "piltext")
        else:
            raise OSError("Unsupported operating system")
        # Create the directory if it doesn't exist
        if not os.path.exists(font_dir):
            os.makedirs(font_dir)
        return str(font_dir)

    def get_full_path(self, font_name: str) -> str:
        """Get the full path of a font file by searching all font directories.

        Searches for the font file in all configured font directories, trying
        common extensions (.ttf, .otf) if the exact name is not found.

        Parameters
        ----------
        font_name : str
            Name of the font file (with or without extension).

        Returns
        -------
        str
            Absolute path to the font file.

        Raises
        ------
        FileNotFoundError
            If the font file is not found in any configured directory.

        """
        for fontdir in self.fontdirs:
            font_path = os.path.join(fontdir, font_name)
            for ext in ["", ".ttf", ".otf"]:
                full_path = font_path + ext
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    return full_path
        raise FileNotFoundError(
            f"Font '{font_name}' not found in directories: {self.fontdirs}",
        )

    def download_google_font(self, part1: str, part2: str, font_name: str) -> str:
        """Download a font from the Google Fonts GitHub repository.

        Downloads a font from the Google Fonts repository on GitHub and stores it
        in the first configured font directory.

        Parameters
        ----------
        part1 : str
            Font category (e.g., 'ofl', 'apache', 'ufl').
        part2 : str
            Font family directory name.
        font_name : str
            Font file name including extension.

        Returns
        -------
        str
            Path to the downloaded font file without extension.

        Raises
        ------
        Exception
            If the font URL returns a 404 error or network connection fails.

        """
        google_font_url = (
            "https://github.com/google/fonts/blob/"
            f"main/{part1}/{quote(part2)}/{quote(font_name)}?raw=true"
        )
        return self.download_font(google_font_url)

    def download_font(self, font_url: str) -> str:
        """Download a font from a URL and store it in the user font directory.

        Downloads a font file from the specified URL and saves it to the first
        configured font directory. Skips download if the font already exists.

        Parameters
        ----------
        font_url : str
            URL of the font file to download.

        Returns
        -------
        str
            Path to the downloaded font file without extension.

        Raises
        ------
        Exception
            If the URL returns a 404 error (font not found) or if there's a
            network connection failure.

        """
        font_dir = self.fontdirs[0]

        font_name = unquote(
            font_url.split("/")[-1].split("?")[0],
        )  # Extract font filename
        font_path = os.path.join(font_dir, font_name)

        if not os.path.exists(font_path):
            try:
                response = urlopen(font_url)
                with open(font_path, "wb") as font_file:
                    font_file.write(response.read())
            except HTTPError as e:
                if e.code == 404:
                    raise Exception(
                        "404 error. The url passed does not exist: "
                        "font file not found.",
                    ) from e

            except URLError as e:
                raise Exception(
                    "Failed to load font. This may be due "
                    "to a lack of internet connection.",
                ) from e
        return os.path.splitext(font_path)[0]

    def calculate_text_size(self, draw: Any, text: str, font: Any) -> tuple[int, int]:
        """Calculate the bounding box size of text.

        Computes the width and height of the text when rendered with the specified
        font using PIL's textbbox method.

        Parameters
        ----------
        draw : PIL.ImageDraw.ImageDraw
            ImageDraw object to use for text measurement.
        text : str
            Text string to measure.
        font : PIL.ImageFont.FreeTypeFont
            Font object to use for rendering.

        Returns
        -------
        tuple of (int, int)
            Width and height of the text in pixels.
        """
        _, _, width, height = draw.textbbox((0, 0), text=text, font=font)
        return width, height

    def get_variation_names(self, font_name: Optional[str] = None) -> list[Any]:
        """Get available font variation names for a variable font.

        Retrieves the list of named variations available for a variable font,
        such as 'Bold', 'Italic', etc.

        Parameters
        ----------
        font_name : str, optional
            Name of the font. If None, uses the default font.

        Returns
        -------
        list of str
            List of variation names available for the font.
        """
        font = self.build_font(font_name=font_name)
        return font.get_variation_names()  # type: ignore[no-any-return]

    def validate_font_file(self, font_path: str) -> dict[str, Any]:
        """Validate a font file and return diagnostic information.

        Checks if a font file exists, is readable, and provides diagnostic
        information useful for troubleshooting font loading issues.

        Parameters
        ----------
        font_path : str
            Full path to the font file to validate.

        Returns
        -------
        dict
            Dictionary containing validation results with keys:
            - 'exists': bool - Whether the file exists
            - 'is_file': bool - Whether the path points to a file (not directory)
            - 'readable': bool - Whether the file has read permissions
            - 'size': int - File size in bytes (0 if file doesn't exist)
            - 'path': str - Absolute path to the file
            - 'valid': bool - Overall validity (exists, is_file, readable, size > 0)

        Examples
        --------
        >>> fm = FontManager()
        >>> info = fm.validate_font_file("/path/to/font.ttf")
        >>> if not info['valid']:
        ...     print(f"Font validation failed: {info}")
        """
        info: dict[str, Any] = {
            "exists": os.path.exists(font_path),
            "is_file": os.path.isfile(font_path),
            "readable": os.access(font_path, os.R_OK)
            if os.path.exists(font_path)
            else False,
            "size": os.path.getsize(font_path) if os.path.exists(font_path) else 0,
            "path": os.path.abspath(font_path),
        }
        info["valid"] = (
            info["exists"] and info["is_file"] and info["readable"] and info["size"] > 0
        )
        return info

    def build_font(
        self,
        font_name: Optional[str] = None,
        font_size: Optional[int] = None,
        variation_name: Optional[str] = None,
    ) -> Any:
        """Create and cache a font object.

        Builds a PIL ImageFont object with the specified parameters. Caches font
        objects to avoid repeated file I/O for the same font configuration.

        Parameters
        ----------
        font_name : str, optional
            Name of the font file. If None, uses the default font name.
        font_size : int, optional
            Font size in points. If None, uses the default font size.
        variation_name : str, optional
            Named variation for variable fonts (e.g., 'Bold', 'Italic').

        Returns
        -------
        PIL.ImageFont.FreeTypeFont
            Loaded font object ready for rendering.

        Raises
        ------
        FileNotFoundError
            If the font file is not found in any configured directory.
        OSError
            If the font file exists but cannot be loaded (corrupted, invalid format,
            or unsupported font type). PIL supports TrueType (.ttf) and OpenType (.otf).
        """
        font_size = font_size or self.default_font_size
        font_name = font_name or self.default_font_name
        if font_name is None:
            raise ValueError("No font name specified and no default font available")
        variation_name = variation_name or "none"

        if not isinstance(font_size, int):
            font_size = int(font_size)

        if font_size <= 0:
            raise ValueError(f"Font size must be positive, got {font_size}")

        if font_size > 10000:
            raise ValueError(f"Font size too large (max 10000), got {font_size}")

        font_path = self.get_full_path(font_name)

        # Validate that the path is actually a file to prevent PIL from
        # walking large directory trees which can cause MemoryError
        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Font path '{font_path}' is not a valid file")

        # Get file information for diagnostic purposes
        file_size = os.path.getsize(font_path)
        file_readable = os.access(font_path, os.R_OK)

        try:
            font = self._cached_load_font(font_path, font_size, variation_name)
            self._cache_lookup[(font_name, font_size, variation_name)] = (
                font_path,
                font_size,
                variation_name,
            )
        except OSError as e:
            # PIL raises OSError for various font loading issues
            error_msg = str(e).lower()
            if "invalid pixel size" in error_msg:
                raise ValueError(
                    f"Invalid font size: {font_size}. "
                    f"Font size must be a positive integer. "
                    f"Original error: {e}"
                ) from e
            elif (
                "unknown file format" in error_msg
                or "cannot open resource" in error_msg
            ):
                diagnostic_info = (
                    f"File size: {file_size} bytes, "
                    f"Readable: {file_readable}, "
                    f"Path: {font_path}"
                )
                raise OSError(
                    f"Failed to load font '{font_name}' from '{font_path}'. "
                    f"The file may be corrupted, not a valid font file, "
                    f"or an unsupported format. "
                    f"Supported formats: TrueType (.ttf), OpenType (.otf). "
                    f"{diagnostic_info}. "
                    f"Original error: {e}"
                ) from e
            # Re-raise other OSErrors as-is
            raise

        return font

    def add_font_directory(self, fontdir: str) -> None:
        """Add a new font directory to the search path.

        Adds a directory to the list of directories searched for font files.
        The directory path is converted to an absolute path. If the directory
        is already in the list, a message is printed and no changes are made.

        Parameters
        ----------
        fontdir : str
            Path to the font directory to add.
        """
        if fontdir not in self.fontdirs:
            self.fontdirs.append(os.path.realpath(fontdir))
        else:
            print(f"Font directory '{fontdir}' already exists.")

    def remove_font_directory(self, fontdir: str) -> None:
        """Remove a font directory from the search path.

        Removes a directory from the list of directories searched for font files.
        If the directory is not in the list, a message is printed and no changes
        are made.

        Parameters
        ----------
        fontdir : str
            Path to the font directory to remove.
        """
        if fontdir in self.fontdirs:
            self.fontdirs.remove(os.path.realpath(fontdir))
        else:
            print(f"Font directory '{fontdir}' not found in the list.")

    def list_font_directories(self) -> list[str]:
        """List all configured font directories.

        Returns
        -------
        list of str
            List of absolute paths to all font directories in the search path.
        """
        return self.fontdirs

    def list_available_fonts(self, fullpath: bool = False) -> list[str]:
        """List all available font files in the configured directories.

        Scans all configured font directories and returns the names of available
        .ttf and .otf font files, optionally with full paths.

        Parameters
        ----------
        fullpath : bool, default=False
            If True, returns full paths to font files. If False, returns only
            font names without extensions.

        Returns
        -------
        list of str
            List of font names or full paths to font files.
        """
        available_fonts = set()
        for fontdir in self.fontdirs:
            if os.path.exists(fontdir) and os.path.isdir(fontdir):
                for file in os.listdir(fontdir):
                    if file.endswith((".ttf", ".otf")):
                        # Add the font name without extension to the set
                        if fullpath:
                            available_fonts.add(os.path.join(fontdir, file))
                        else:
                            available_fonts.add(os.path.splitext(file)[0])
        return list(available_fonts)

    def delete_all_fonts(self) -> list[str]:
        """Delete all font files from configured font directories.

        Removes all .ttf and .otf font files from all configured font directories.
        Use with caution as this operation cannot be undone.

        Returns
        -------
        list of str
            List of font file names that were deleted.
        """
        deleted_fonts = []
        for font_dir in self.fontdirs:
            for font_file_name in os.listdir(font_dir):
                if not font_file_name.endswith((".ttf", ".otf")):
                    continue
                font_file_path = os.path.join(font_dir, font_file_name)
                if os.path.isfile(font_file_path):
                    os.remove(font_file_path)
                    deleted_fonts.append(font_file_name)
        return deleted_fonts
