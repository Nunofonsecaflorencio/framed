from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

DPI = 72
PAGE_WIDTH, PAGE_HEIGHT = A4
FRAME_SIZES = {
    "wallet": (2 * inch, 3 * inch),
    "2R": (2.5 * inch, 3.5 * inch),
    "3R": (3.5 * inch, 5 * inch),
    "4R": (4 * inch, 6 * inch),
    "5R": (5 * inch, 7 * inch),
}

for size in FRAME_SIZES:
    w, h = FRAME_SIZES[size]
    FRAME_SIZES[size] = (int(w), int(h))

CUTTING_SPACING = 5
UNPRINTABLE_MARGIN = 0.25 * inch
FRAME_PADDING = int(3 * inch)
FRAME_YSPACING = int(0.5 * inch)

FONT_PATH = "COUR.TTF"
MIN_FONTSIZE = int(inch) // 2
MAX_FONTSIZE = int(1.2 * inch)
