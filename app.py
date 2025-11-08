import os
import random
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from generator import get_image_data, generate_frame
from constants import (
    FRAME_SIZES,
    PAGE_WIDTH,
    PAGE_HEIGHT,
    UNPRINTABLE_MARGIN,
    CUTTING_SPACING,
)
from reportlab.pdfgen import canvas
import rectpack

from utils import cleanup
import threading
import time

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "output"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def periodic_cleanup():
    while True:
        cleanup(UPLOAD_FOLDER, OUTPUT_FOLDER)
        time.sleep(3600)  # every hour


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        frame_size_key = request.form.get("frame_size")
        frame_size = FRAME_SIZES.get(frame_size_key, FRAME_SIZES["3R"])

        uploaded_files = request.files.getlist("images")
        if not uploaded_files:
            return "No images uploaded", 400

        image_paths = []
        for file in uploaded_files:
            if file.filename == "":
                continue
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            image_paths.append(save_path)

        random.shuffle(image_paths)
        data = get_image_data(image_paths)

        # --- Packing algorithm for PDF layout ---
        packer = rectpack.newPacker(
            pack_algo=rectpack.MaxRectsBaf,
            bin_algo=rectpack.PackingBin.BBF,
            mode=rectpack.PackingMode.Offline,
            rotation=True,
            sort_algo=rectpack.SORT_LSIDE,
        )
        packer.add_bin(
            PAGE_WIDTH - 2 * UNPRINTABLE_MARGIN,
            PAGE_HEIGHT - 2 * UNPRINTABLE_MARGIN,
            count=float("inf"),
        )

        for i, image_data in enumerate(data):
            frame, size = generate_frame(image_data, frame_size)
            output_path = os.path.join(
                OUTPUT_FOLDER, os.path.basename(image_data["path"])
            )
            frame.save(output_path, format="JPEG", quality=95, subsampling=0)
            image_data["frame_path"] = output_path
            packer.add_rect(size[0] + CUTTING_SPACING, size[1] + CUTTING_SPACING, rid=i)

        packer.pack()

        output_pdf = os.path.join(OUTPUT_FOLDER, "collage.pdf")
        c = canvas.Canvas(output_pdf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
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

        return redirect(url_for("download_pdf"))

    return render_template("index.html", frame_sizes=FRAME_SIZES.keys())


@app.route("/download")
def download_pdf():
    pdf_path = os.path.join(OUTPUT_FOLDER, "collage.pdf")
    return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
    threading.Thread(target=periodic_cleanup, daemon=True).start()
    app.run(debug=True)
