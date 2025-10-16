# Agent Instructions for piltext

This document provides guidelines for AI agents working on this repository.

## Project Overview

Piltext is a Python library that creates PNG images from text using Pillow (PIL). It
provides tools for:

- Text rendering with customizable fonts, sizes, and styles
- Font management including Google Fonts integration
- Text layout with grids and anchoring
- Image creation and manipulation

Piltext is designed to make it easy to create text-based images programmatically with
precise control over text positioning, font selection, and styling.

Instructions:

- Never use git commands, you must not commit code

## Installation

### For Development

```bash
pre-commit run --all-files
```

## Documentation

### Building Documentation

The project documentation is built using Sphinx and hosted on ReadTheDocs.

To build the documentation locally:

```bash
python doc/make
```

The generated documentation will be available in the `docs/_build/html` directory.

### API Documentation

When working on the code, please follow these documentation guidelines:

- Use docstrings for all public classes, methods, and functions
- Follow the NumPy docstring format
- Include type hints in function signatures
- Document parameters, return values, and raised exceptions

## Development

### Running Tests

Run all tests using `pytest`.

To run a specific test file: `pytest tests/test_text_box.py`

To run a single test function: `pytest tests/test_text_box.py::test_function_name`

To run tests with coverage: `pytest --cov=piltext --cov-report=term`

### Linting and Formatting

This project uses `ruff` for linting and formatting, and `prettier` for other file
types. These are enforced by pre-commit hooks.

Run linting and formatting:
`ruff check --fix --exit-non-zero-on-fix --config=.ruff.toml`

## Project Structure

The project is organized as follows:

```
piltext/                # Main package
  ├── __init__.py       # Package initialization
  ├── font_manager.py   # Font handling and management
  ├── image_dial.py     # Dial image creation
  ├── image_drawer.py   # Core image drawing functionality
  ├── image_handler.py  # Image processing utilities
  ├── image_squares.py  # Square/grid image creation
  ├── text_box.py       # Text box handling
  └── text_grid.py      # Grid-based text layout

tests/                  # Test directory
  ├── fonts/            # Test font resources
  ├── __init__.py
  ├── test_font_manager.py
  ├── test_image_dial.py
  ├── test_image_drawer.py
  ├── test_image_handler.py
  ├── test_image_squares.py
  ├── test_text_box.py
  └── test_text_grid.py

docs/                   # Documentation
  ├── apidocs.rst       # API documentation
  ├── conf.py           # Sphinx configuration
  ├── index.rst         # Main documentation index
  └── ...               # Other documentation files
```

### Key Modules

- `font_manager.py`: Handles font loading, management, and Google Fonts integration
- `image_drawer.py`: Core functionality for drawing text on images
- `text_grid.py`: Provides grid-based text layout capabilities
- `text_box.py`: Handles single text box creation and manipulation
- `image_handler.py`: Basic image creation and manipulation utilities

## Code Style

- **Formatting**: Adhere to the `ruff` and `prettier` configurations. Maximum line
  length is 88 characters.
- **Imports**: Follow the `isort` configuration in `.ruff.toml`. Imports are grouped
  into `future`, `standard-library`, `third-party`, `first-party`, and `local-folder`.
- **Naming**: Use `snake_case` for functions and variables, and `PascalCase` for
  classes.
- **Types**: Add type hints for all new functions and methods.
- **Error Handling**: Use standard `try...except` blocks for error handling.

## Contribution Guidelines

### Common Issues

When working on the code, be aware of these common issues:

1. PIL/Pillow version compatibility: Check that your code works with the minimum
   supported Pillow version
2. Font handling across platforms: Font loading behavior can differ between operating
   systems
3. Type hints: Ensure proper typing for all functions, especially when working with PIL
   objects
