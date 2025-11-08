import os
from PIL import Image as PILImage, ImageDraw
import rectpack
from rectpack import newPacker, PackingMode, PackingBin
from utils import *
from constants import *
from reportlab.pdfgen import canvas
import random


def get_image_data(images: list[str]):
    data = []
    for image_path in images:
        data.append(
            {
                "path": image_path,
                "image": load_image(image_path),
                "caption": get_caption(image_path),
            }
        )
    return data


def generate_frame(image_data, frame_size) -> PILImage.Image:
    picture: PILImage.Image = image_data["image"]

    if (picture.width < picture.height) != (frame_size[0] < frame_size[1]):
        frame_size = (frame_size[1], frame_size[0])

    text_width, text_height, font = get_optimal_textbox(
        image_data["caption"], picture.width, FONT_PATH
    )

    width = picture.width + 2 * FRAME_PADDING
    height = picture.height + text_height + FRAME_YSPACING + 2 * FRAME_PADDING
    aspect_ratio = width / height
    if width > height:
        frame_width = frame_size[0]
        frame_height = frame_size[0] / aspect_ratio
    else:
        frame_height = frame_size[1]
        frame_width = frame_size[1] * aspect_ratio

    frame = PILImage.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(frame)

    frame.paste(picture, (FRAME_PADDING, FRAME_PADDING))
    draw.text(
        (FRAME_PADDING, FRAME_PADDING + picture.height + FRAME_YSPACING),
        image_data["caption"],
        fill=(0, 0, 0),
        font=font,
    )

    return frame, (frame_width, frame_height)


if __name__ == "__main__":

    INPUT_DIR = "input/"
    OUTPUT_DIR = "output/"
    images = [os.path.join(INPUT_DIR, img) for img in os.listdir(INPUT_DIR)]
    random.shuffle(images)

    packer = newPacker(
        pack_algo=rectpack.MaxRectsBaf,
        bin_algo=PackingBin.BBF,
        mode=PackingMode.Offline,
        rotation=True,
        sort_algo=rectpack.SORT_LSIDE,
    )
    packer.add_bin(
        PAGE_WIDTH - 2 * UNPRINTABLE_MARGIN,
        PAGE_HEIGHT - 2 * UNPRINTABLE_MARGIN,
        count=float("inf"),
    )

    data = get_image_data(images)
    for i, image_data in enumerate(data):
        frame, size = generate_frame(image_data, FRAME_SIZES["3R"])
        output_path = os.path.join(OUTPUT_DIR, os.path.basename(image_data["path"]))
        frame.save(
            output_path,
            format="JPEG",
            quality=95,
            subsampling=0,
        )
        # print(image_data)
        image_data["frame_path"] = output_path
        packer.add_rect(
            size[0] + CUTTING_SPACING,
            size[1] + CUTTING_SPACING,
            rid=i,
        )
    packer.pack()

    output_filename = os.path.join(OUTPUT_DIR, "collage.pdf")
    c = canvas.Canvas(output_filename, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    c.setStrokeColorRGB(0.9, 0.9, 0.9)
    c.setLineWidth(1)
    c.setDash([6, 3])
    for rect in packer.rect_list():
        bin_index, x, y, w, h, i = rect
        if bin_index > c.getPageNumber() - 1:
            c.showPage()
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.setLineWidth(1)
            c.setDash([6, 3])

        x += UNPRINTABLE_MARGIN
        y += UNPRINTABLE_MARGIN
        w -= CUTTING_SPACING
        h -= CUTTING_SPACING
        c.drawImage(data[i]["frame_path"], x, y, w, h, preserveAspectRatio=True)

        c.rect(x, y, w, h, stroke=1, fill=0)

    c.save()
    print(f"PDF saved as {output_filename}")
