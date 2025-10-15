import argparse
import os
from PIL import Image


def main():
    term_width, term_height = os.get_terminal_size()
    parser = argparse.ArgumentParser(prog="img2term", 
                                     description="Print an image to the terminal")
    parser.add_argument("filename")
    parser.add_argument("--max_width", 
                        type=int,
                        default=term_width,
                        help="Set the max width (in columns) of the displayed image")
    parser.add_argument("--max_height",
                        type=int, 
                        default=term_height,
                        help="Set the max height (in rows) of the displayed image")

    args = parser.parse_args()
    try:
        img = Image.open(args.filename).convert("RGBA")
    except FileNotFoundError:
        print(f"ERROR: Failed to load file {args.filename}")
        os._exit(1)

    term_width = args.max_width
    term_height = args.max_height

    if term_width <= 0 or term_height <= 0:
        print("Error: Specified width and height must be greater than 0")
        os._exit(1)

    img_width = img.width
    img_height = img.height // 2

    img_aspect = img_width / img_height
    term_aspect = term_width / term_height
    scale = 1.0

    if img_aspect > term_aspect:
        scale = term_width / img_width
    else:
        scale = term_height / img_height

    img_width = int(img_width * scale)
    img_height = int(img_height * scale)

    img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
    
    for y in range(img_height):
        line = []
        for x in range(img_width):
            r, g, b, a = img.getpixel((x, y))
            a /= 255.0
            r = int(r * a + 255 * (1 - a))
            g = int(g * a + 255 * (1 - a))
            b = int(b * a + 255 * (1 - a))
            line.append(f"\033[48;2;{r};{g};{b}m \033[0m")
        print("".join(line))


if __name__ == "__main__":
    main()
