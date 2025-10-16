# piltext

[![codecov](https://codecov.io/gh/holgern/piltext/graph/badge.svg?token=VyIU0ZxwpD)](https://codecov.io/gh/holgern/piltext)
[![PyPi Version](https://img.shields.io/pypi/v/piltext.svg)](https://pypi.python.org/pypi/piltext/)

Creates PNG from text using Pillow

### Installation

PyPI

```bash
pip install piltext
```

or from source

```bash
git clone https://github.com/holgern/piltext.git
cd piltext
python3 setup.py install
```

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Usage

Import the import parts

```
from piltext import FontManager, ImageDrawer, TextGrid
```

Download fonts:

```
f = FontManager(default_font_size=20)
font1 = f.download_google_font("ofl", "roboto", "Roboto[wdth,wght].ttf")
font2 = f.download_google_font("ofl", "jersey10", "Jersey10-Regular.ttf")
f.default_font_name = font1
print(f.list_available_fonts())
```

Fonts with variations can be used

```
print(f.get_variation_names())
```

Create image with texts:

```
image = ImageDrawer(100, 100, f)
xy = (0, 0)
w, h, font_size = image.draw_text("Test", xy, font_variation="Bold")
xy = (xy[0], xy[1] + h)
w, h, font_size = image.draw_text("Test", xy)
xy = (xy[0] + w, xy[1])
w, h, font_size = image.draw_text("Test", xy)
xy = (xy[0], xy[1] + h)
w, h, font_size = image.draw_text("Test", xy, font_name=font2, fill=128)
xy = (0, xy[1] + h)
w, h, font_size = image.draw_text(
    "Test", xy, end=(100, 100), font_variation="Condensed Medium"
)
print(f"w: {w}, h:{h}, font_size: {font_size}")

image.finalize(inverted=False)
display(image.get_image())
```

Anchor can be used to position text within cells. When no `font_size` is specified, text automatically scales to fit the cell:

```python
image = ImageDrawer(480, 280, f)

# Auto-fit with anchor (text scales to fit the bounding box)
xy = (5, 3)
w, h, font_size = image.draw_text(
    "Long Text 1", xy, end=(480, (280 - 15) / 3), anchor="lt"
)

# Fixed font size with anchor (no auto-fit)
xy = (5, xy[1] + h)
w, h, font_size = image.draw_text(
    "Long Text 3", xy, font_size=font_size, font_variation="Thin", anchor="lt"
)

# Bottom-right anchor with auto-fit
w, h, font_size = image.draw_text(
    "Long Text 4", (480 - 5, 280 - 5), end=(5, 5), anchor="rb"
)

image.finalize(inverted=False)
display(image.get_image())
```

**Anchor Positioning:**

The anchor parameter uses a two-character code:
- First character (horizontal): `l` (left), `m` (middle), `r` (right)
- Second character (vertical): `t` (top), `m` (middle), `b` (bottom), `s` (baseline)

Examples: `lt` (left-top), `mm` (centered), `rb` (right-bottom)

TextGrid

```
image = ImageDrawer(480, 280, f)

grid = TextGrid(7, 4, image, margin_x=2, margin_y=2)
grid.print_grid()
merge_list = [
    ((0, 0), (0, 3)),
    ((1, 0), (2, 1)),
    ((1, 2), (2, 3)),
    ((3, 0), (6, 3)),
]
grid.merge_bulk(merge_list)
grid.print_grid()
```

can be used to improve text layout:

```
image.initialize()
grid.set_text(0, "Test1", font_name=font2)
grid.set_text(1, "Test2")
grid.set_text(2, "Test3")
grid.set_text(3, "Test4", anchor="lt")
image.finalize(inverted=False)
display(image.get_image())
```

The text can also be set as bulk using a list:

```
image.initialize()
text_list = [
    {"start": 0, "text": "Test1", "font_name": font2},
    {"start": 1, "text": "Test2"},
    {"start": 2, "text": "Test3"},
    {"start": 3, "text": "Test4", "anchor": "lt", "fill": 128},
]
grid.set_text_list(text_list)
image.finalize(inverted=False)
display(image.get_image())
```

## Pre-commit-config

### Installation

```
$ pip install pre-commit
```

### Using homebrew:

```
$ brew install pre-commit
```

```
$ pre-commit --version
pre-commit 2.10.0
```

### Install the git hook scripts

```
$ pre-commit install
```

### Run against all the files

```
pre-commit run --all-files
pre-commit run --show-diff-on-failure --color=always --all-files
```

### Update package rev in pre-commit yaml

```bash
pre-commit autoupdate
pre-commit run --show-diff-on-failure --color=always --all-files
```
