import argparse
import importlib.resources
import site
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def get_package_resource_path(resource_name):
    """
    Get the path to a resource file included in the package.

    Args:
        resource_name (str): Name of the resource file

    Returns:
        str: Path to the resource file, or None if not found
    """
    try:
        # Try to get the resource using importlib.resources
        if hasattr(importlib.resources, "files"):
            # Python 3.9+ way
            return str(importlib.resources.files("book_cover_maker") / resource_name)
        else:
            # Python 3.8 way
            with importlib.resources.path("book_cover_maker", resource_name) as path:
                return str(path)
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        # Fallback: look for the file in the package directory
        package_dir = Path(__file__).parent.parent.parent
        resource_path = package_dir / resource_name
        if resource_path.exists():
            return str(resource_path)
        return None


def get_default_background_path():
    """
    Resolve the path to the default background image (cover_background.png)
    included with the distribution or available in development.
    Search order:
      1) Project/package root (editable/development)
      2) site-packages root (wheel force-included at root)
      3) Package directory (if bundled inside the package dir)
      4) Current working directory
      5) Fallback to dummy background generation
    """
    candidates = []
    pkg_root = Path(__file__).parent.parent.parent
    candidates.append(pkg_root / "cover_background.png")

    try:
        for sp in site.getsitepackages():
            candidates.append(Path(sp) / "cover_background.png")
    except Exception:
        pass

    # If file is placed inside the package directory
    candidates.append(Path(__file__).parent / "cover_background.png")

    # CWD fallback
    candidates.append(Path.cwd() / "cover_background.png")

    for path in candidates:
        if path.exists():
            return str(path)

    # Fallback: create a dummy background
    print(
        "Warning: cover_background.png not found in package, creating dummy background..."
    )
    return create_dummy_background(1000, 1500)


def create_book_cover(
    background_image_path,
    title,
    author,
    edition_label,
    output_path="book_cover.png",
    title_font_path=None,
    author_font_path=None,
    edition_font_path=None,
):
    """
    Creates a book cover image with the given text elements, styled similarly to the example.

    Args:
        background_image_path (str): Path to the background image.
        title (str): The title of the book.
        author (str): The author(s) of the book.
        edition_label (str): The edition label (e.g., "1ST EDITION").
        output_path (str): Path to save the generated book cover.
        title_font_path (str, optional): Path to the title font file.
        author_font_path (str, optional): Path to the author font file.
        edition_font_path (str, optional): Path to the edition label font file.
    """
    try:
        img = Image.open(background_image_path).convert("RGB")
    except FileNotFoundError:
        print(f"Error: Background image not found at {background_image_path}")
        return

    draw = ImageDraw.Draw(img)
    width, height = img.size

    # --- Colors ---
    white_color = (255, 255, 255)
    light_gray_color = (200, 200, 200)
    dark_blue_color = (30, 40, 70)  # Approximation for the edition label box

    # --- Fonts ---
    # Load fonts with custom paths or fallback to defaults
    def load_font(font_path, size, fallback_paths=None):
        """Load font with fallback options"""
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except IOError:
                print(
                    f"Warning: Custom font not found at {font_path}, trying fallbacks..."
                )

        if fallback_paths:
            for fallback_path in fallback_paths:
                try:
                    return ImageFont.truetype(fallback_path, size)
                except IOError:
                    continue

        print("Warning: All font options failed, using default Pillow font.")
        return ImageFont.load_default()

    # Resolve fonts directory in multiple environments
    def get_fonts_dir() -> Path:
        """Return the most plausible fonts directory.
        Search order:
        1) Package root next to this module (editable installs)
        2) Installed distribution within site-packages root (force-included)
        3) Current working directory fallback
        """
        # 1) package root (project layout or wheel extracted into site-packages)
        pkg_root = Path(__file__).parent.parent.parent
        candidate = pkg_root / "fonts"
        if candidate.exists():
            return candidate

        # 2) site-packages root (some installers may place data at site root)
        try:
            for sp in site.getsitepackages():
                sp_path = Path(sp) / "fonts"
                if sp_path.exists():
                    return sp_path
        except Exception:
            pass

        # 3) CWD fallback
        cwd_fonts = Path.cwd() / "fonts"
        if cwd_fonts.exists():
            return cwd_fonts

        # default to pkg_root/fonts even if missing (load_font will fallback)
        return candidate

    fonts_dir = get_fonts_dir()

    # Default fallback font paths
    default_fonts = [
        str(fonts_dir / "NotoSansJP-VF.ttf"),
        str(fonts_dir / "NotoSansKR-Bold.ttf"),
        str(fonts_dir / "NotoSans-Bold.ttf"),
    ]

    default_regular_fonts = [
        str(fonts_dir / "NotoSansJP-VF.ttf"),
        str(fonts_dir / "NotoSansKR-Regular.ttf"),
        str(fonts_dir / "NotoSans-Regular.ttf"),
    ]

    # Load fonts
    title_font = load_font(title_font_path, int(height * 0.045), default_fonts)
    author_font = load_font(
        author_font_path, int(height * 0.025), default_regular_fonts
    )
    edition_font = load_font(
        edition_font_path, int(height * 0.015), default_regular_fonts
    )

    # --- Edition Label (Top Right) ---
    edition_padding_x = int(width * 0.03)
    edition_padding_y = int(height * 0.03)

    # Measure text to create a background box
    edition_text_bbox = draw.textbbox((0, 0), edition_label, font=edition_font)
    edition_text_width = edition_text_bbox[2] - edition_text_bbox[0]
    edition_text_height = edition_text_bbox[3] - edition_text_bbox[1]

    edition_box_width = edition_text_width + int(width * 0.03)
    edition_box_height = edition_text_height + int(height * 0.01)

    edition_box_x1 = width - edition_box_width
    edition_box_y1 = 0
    edition_box_x2 = width
    edition_box_y2 = edition_box_height

    # Draw a simple rectangle for the background (you can enhance this with a parallelogram shape if desired)
    draw.rectangle(
        [(edition_box_x1, edition_box_y1), (edition_box_x2, edition_box_y2)],
        fill=dark_blue_color,
    )
    draw.text(
        (width - edition_padding_x - edition_text_width, edition_padding_y),
        edition_label,
        font=edition_font,
        fill=white_color,
    )

    # --- Title (Bottom Left) ---
    # Split/wrap title to fit within the title area width while keeping equal left/right margins
    title_start_x = int(width * 0.07)
    title_start_y = int(height * 0.75)  # Adjust based on the example

    # Define the maximum width for the title area (equal left/right margins)
    title_area_max_width = width - (title_start_x * 2)

    def wrap_text(draw_ctx, text_value, font_obj, max_w):
        """Greedy wrap: prefers whitespace boundaries, falls back to per-character for long/ CJK sequences."""
        if not text_value:
            return [""]

        lines = []
        # Respect explicit newlines first
        raw_lines = text_value.split("\n")

        for raw in raw_lines:
            words = raw.split()
            # If there are no spaces (e.g., CJK), fall back to character-based wrap
            if len(words) == 0:
                current_line = ""
                for ch in raw:
                    test_line = current_line + ch
                    bbox = draw_ctx.textbbox((0, 0), test_line, font=font_obj)
                    test_w = bbox[2] - bbox[0]
                    if test_w <= max_w or current_line == "":
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = ch
                if current_line:
                    lines.append(current_line)
                continue

            current_line = ""
            for word in words:
                # If a single word is longer than max width, split by characters
                bbox_word = draw_ctx.textbbox((0, 0), word, font=font_obj)
                word_w = bbox_word[2] - bbox_word[0]
                if word_w > max_w:
                    # flush current_line first
                    if current_line:
                        lines.append(current_line)
                        current_line = ""
                    piece = ""
                    for ch in word:
                        test_piece = piece + ch
                        bbox_piece = draw_ctx.textbbox((0, 0), test_piece, font=font_obj)
                        piece_w = bbox_piece[2] - bbox_piece[0]
                        if piece_w <= max_w or piece == "":
                            piece = test_piece
                        else:
                            lines.append(piece)
                            piece = ch
                    if piece:
                        # start a new line with this piece or append to current if it fits
                        current_line = piece
                    continue

                tentative = word if current_line == "" else current_line + " " + word
                bbox = draw_ctx.textbbox((0, 0), tentative, font=font_obj)
                tw = bbox[2] - bbox[0]
                if tw <= max_w:
                    current_line = tentative
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

        return lines

    title_lines = wrap_text(draw, title, title_font, title_area_max_width)

    for i, line in enumerate(title_lines):
        draw.text(
            (
                title_start_x,
                title_start_y + i * int(title_font.size * 1.2),
            ),  # Line spacing
            line,
            font=title_font,
            fill=white_color,
        )

    # Draw horizontal line under the title, similar to the example
    line_y = (
        title_start_y
        + (len(title_lines) * int(title_font.size * 1.2))
        + int(height * 0.01)
    )
    # Draw line to match the title area's left margin and a reasonable length within the area
    available_line_length = min(int(width * 0.5), width - title_start_x * 2)
    line_length = available_line_length
    draw.line(
        [(title_start_x, line_y), (title_start_x + line_length, line_y)],
        fill=light_gray_color,
        width=3,
    )

    # --- Author (Below Title Line) ---
    author_start_y = line_y + int(height * 0.02)
    draw.text(
        (title_start_x, author_start_y), author, font=author_font, fill=light_gray_color
    )

    # --- Overlay elements from the original image (e.g., abstract shapes) ---
    # This part is more complex and usually involves separate image assets or
    # more advanced drawing routines to replicate the geometric shapes
    # in the top right and the vertical line.
    # For now, we'll keep it simple to focus on text placement.

    # Example of a simple abstract shape in the top right (similar to the original)
    # This is a very rough approximation. You might need to use polygons or load an SVG/PNG.
    shape_color = (30, 40, 70, 150)  # Dark blue with some transparency
    # draw.polygon([
    #     (width - int(width*0.2), 0),
    #     (width, 0),
    #     (width, int(height*0.15)),
    #     (width - int(width*0.25), int(height*0.08))
    # ], fill=shape_color)

    img.save(output_path)
    print(f"Book cover saved to {output_path}")


# --- Example Usage ---
# Ensure you have a background image named 'background.jpg' in the same directory
# or provide a full path. The original image's background is quite specific
# with clouds and glowing points, so a similar image would yield the best result.


# You can use a placeholder image for testing if you don't have the exact background.
# Let's create a simple gradient background for demonstration if no image is provided.
def create_dummy_background(width, height, path="dummy_background.jpg"):
    dummy_img = Image.new("RGB", (width, height), color="darkgrey")
    draw = ImageDraw.Draw(dummy_img)
    # Add a simple gradient to mimic some depth
    for y in range(height):
        r = int(30 + (100 - 30) * y / height)
        g = int(40 + (120 - 40) * y / height)
        b = int(70 + (150 - 70) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add some "glowing points" similar to the original for visual effect
    import random

    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(int(height * 0.5), height)
        radius = random.randint(1, 3)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius), fill=(255, 150, 0)
        )  # Orange glow

    dummy_img.save(path)
    return path


def get_fonts_by_language(lang):
    """
    Get appropriate font paths based on language.

    Args:
        lang (str): Language code ('kr', 'jp', 'en')

    Returns:
        tuple: (title_font_path, author_font_path, edition_font_path)
    """

    # Use the same fonts directory resolution as in create_book_cover
    def get_fonts_dir() -> Path:
        pkg_root = Path(__file__).parent.parent.parent
        candidate = pkg_root / "fonts"
        if candidate.exists():
            return candidate
        try:
            for sp in site.getsitepackages():
                sp_path = Path(sp) / "fonts"
                if sp_path.exists():
                    return sp_path
        except Exception:
            pass
        cwd_fonts = Path.cwd() / "fonts"
        if cwd_fonts.exists():
            return cwd_fonts
        return candidate

    fonts_dir = get_fonts_dir()

    if lang == "kr":
        return (
            str(fonts_dir / "NotoSansKR-Bold.ttf"),
            str(fonts_dir / "NotoSansKR-Regular.ttf"),
            str(fonts_dir / "NotoSansKR-Regular.ttf"),
        )
    elif lang == "jp":
        return (
            str(fonts_dir / "NotoSansJP-VF.ttf"),
            str(fonts_dir / "NotoSansJP-VF.ttf"),
            str(fonts_dir / "NotoSansJP-VF.ttf"),
        )
    elif lang == "en":
        return (
            str(fonts_dir / "NotoSans-Bold.ttf"),
            str(fonts_dir / "NotoSans-Regular.ttf"),
            str(fonts_dir / "NotoSans-Regular.ttf"),
        )
    else:
        # Default to Korean fonts
        return (
            str(fonts_dir / "NotoSansKR-Bold.ttf"),
            str(fonts_dir / "NotoSansKR-Regular.ttf"),
            str(fonts_dir / "NotoSansKR-Regular.ttf"),
        )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate book cover with specified parameters"
    )

    parser.add_argument(
        "bg_image_path",
        nargs="?",
        default=None,
        help="Path to the background image (optional, uses included default if not provided)",
    )
    parser.add_argument("title", help="Book title")
    parser.add_argument("author", help="Author name")
    parser.add_argument("edition", help='Edition label (e.g., "1ST EDITION")')
    parser.add_argument(
        "--lang",
        choices=["kr", "jp", "en"],
        default="kr",
        help="Language for font selection (default: kr)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output path for the generated book cover (optional, defaults to generated_book_cover_{lang}.png)",
    )

    return parser.parse_args()


def main():
    """Main entry point for the book cover maker."""
    # Parse command line arguments
    args = parse_arguments()

    # Use default background if not provided
    bg_image_path = args.bg_image_path
    if bg_image_path is None:
        bg_image_path = get_default_background_path()
        print(f"Using default background: {bg_image_path}")

    # Get appropriate fonts based on language
    title_font_path, author_font_path, edition_font_path = get_fonts_by_language(
        args.lang
    )

    # Determine output filename
    if args.output:
        output_filename = args.output
    else:
        output_filename = f"generated_book_cover_{args.lang}.png"

    # Create book cover with parsed arguments
    create_book_cover(
        background_image_path=bg_image_path,
        title=args.title,
        author=args.author,
        edition_label=args.edition,
        output_path=output_filename,
        title_font_path=title_font_path,
        author_font_path=author_font_path,
        edition_font_path=edition_font_path,
    )

    print(f"Book cover generated successfully!")
    print(f"Language: {args.lang}")
    print(f"Output file: {output_filename}")


if __name__ == "__main__":
    main()
