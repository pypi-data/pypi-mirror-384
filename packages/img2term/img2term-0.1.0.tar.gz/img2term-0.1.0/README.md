# img2term
A simple Python program that displays images in your terminal.
![Peacock](screenshot.png)

## Requirements
 - Python 3.13 or higher (older versions down to 3.8 might still work)
 - A terminal with 24-bit true color support. Some examples include:
    - [Ptyxis](https://gitlab.gnome.org/chergert/ptyxis/) (used in the screenshot above)
    - [Konsole](https://konsole.kde.org/)
    - [Alacritty](https://alacritty.org/)
    - [Windows Terminal](https://github.com/microsoft/terminal)
 - **OPTIONAL:** The images may render more smoothly if the terminal supports GPU acceleration.

## Getting Started
1. Clone this repository and `cd` into it.
2. Install the [Pillow](https://pypi.org/project/pillow/) image processing library.
3. To display a single image (i.e. `peacock.png`), you can run the program like so:

```
python img2term.py peacock.png
```

## Options
The program will try to resize the image to fit within the terminal window. If you want the image to display in a smaller size, you can do so by setting `--max_width` and `--max_height`, which constrain the size of the image in terms of rows/columns.

For example, if you want the image to take up no more than 24 rows:

```
python img2term.py peacock.png --max_height 24
```

## Supported File Formats
Any format that the Pillow library supports, including common formats like JPEG, PNG, and WEBP should work. You can check out supported image formats [here](https://hugovk-pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).


