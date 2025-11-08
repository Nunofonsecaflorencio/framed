from exif import Image
from PIL import Image as PILImage
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from PIL import Image as PILImage, ImageDraw, ImageFont
from constants import MIN_FONTSIZE, MAX_FONTSIZE


def format_datetime(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    return dt.strftime("%A, %d/%m/%Y %H:%M")


def format_exposure(exposure) -> str:
    if isinstance(exposure, float):
        frac = Fraction(exposure).limit_denominator(1000)
        return f"{frac.numerator}/{frac.denominator}"
    return str(exposure)


def get_caption(image_path: Path) -> Image:
    with open(image_path, "rb") as f:
        metadata = Image(f)

    caption = str()
    dt_value = metadata.get("datetime_original")
    if dt_value:
        caption += format_datetime(dt_value) + "\n"

    iso = metadata.get("photographic_sensitivity")
    f_number = metadata.get("f_number") or metadata.get("aperture_value")
    exposure = metadata.get("exposure_time")
    if iso and f_number and exposure:
        caption += f"ISO {iso}, f{f_number}, {format_exposure(exposure)}"
    return caption


def fix_orientation(image: PILImage, orientation: int) -> Path:
    operations = {
        2: lambda img: img.transpose(PILImage.FLIP_LEFT_RIGHT),
        3: lambda img: img.rotate(180, expand=True),
        4: lambda img: img.transpose(PILImage.FLIP_TOP_BOTTOM),
        5: lambda img: img.transpose(PILImage.FLIP_LEFT_RIGHT).rotate(90, expand=True),
        6: lambda img: img.rotate(270, expand=True),
        7: lambda img: img.transpose(PILImage.FLIP_LEFT_RIGHT).rotate(270, expand=True),
        8: lambda img: img.rotate(90, expand=True),
    }
    return operations.get(orientation, lambda x: x)(image)


def load_image(image_path):
    with open(image_path, "rb") as f:
        metadata = Image(f)
    image = PILImage.open(image_path)
    if metadata.get("orientation"):
        return fix_orientation(image, metadata.get("orientation"))
    return image


def get_optimal_textbox(
    text: str,
    max_width: int,
    font_path: str,
    min_size: int = MIN_FONTSIZE,
    max_size: int = MAX_FONTSIZE,
):
    draw = ImageDraw.Draw(PILImage.new("RGB", (max_width, 100)))
    best_size = min_size
    for size in range(min_size, max_size + 1):
        font = ImageFont.truetype(font_path, size)
        _, _, text_width, text_height = draw.multiline_textbbox((0, 0), text, font=font)
        if text_width > max_width:
            break
        best_size = size

    # Get final text dimensions using the chosen font
    font = ImageFont.truetype(font_path, best_size)
    _, _, text_width, text_height = draw.multiline_textbbox((0, 0), text, font=font)

    return text_width, text_height, font


import os


def cleanup(*folders):
    """
    Safely removes all files inside the given folders,
    keeping the folder structure intact.
    """
    for folder in folders:
        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    # remove nested folders recursively
                    import shutil

                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"⚠️ Could not delete {file_path}: {e}")
