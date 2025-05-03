#!env/bin/python3

"""
Title: Kibon Card PDF Generator
Author: benjamin@moudok.fr
Source: FFTDA.fr
License: MIT

Description:
Generates an A4 landscape PDF file with martial arts training cards.
Each card includes a title, subcategory, number, list of movements,
an SVG illustration, and a QR code pointing to a video URL with timestamp.
Cards are styled using Open Sans fonts and grouped 8 per page
in a 4×2 layout. Configuration (colors, images) is provided via YAML.
"""

import yaml
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
import qrcode
from io import BytesIO

# Load YAML data
with open("kibon.yaml", "r", encoding="utf-8") as f:
    kibon_data = yaml.safe_load(f)

with open("config.yaml", "r", encoding="utf-8") as f:
    config_data = yaml.safe_load(f)

# PDF and layout settings
page_width, page_height = landscape(A4)
card_width = 74.25 * mm
card_height = 105 * mm
cards_per_row = 4
cards_per_col = 2

pdf = canvas.Canvas("kibon.pdf", pagesize=landscape(A4))

# Register fonts
pdfmetrics.registerFont(TTFont("OpenSans", "fonts/Open_Sans/static/OpenSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("OpenSansBold", "fonts/Open_Sans/static/OpenSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("OpenSansExtraBold", "fonts/Open_Sans/static/OpenSans-ExtraBold.ttf"))

def hex_to_rgb(hex_str):
    hex_str = hex_str.strip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255. for i in (0, 2, 4))

def draw_card(c, x, y, main_cat, sub_cat, card, video_url, color_code, image_name):
    # Background color
    c.setFillColorRGB(*hex_to_rgb(color_code))
    c.rect(x, y, card_width, card_height, fill=True, stroke=False)

    # Inner white rectangle
    margin = 5 * mm
    c.setFillColor("#f8f8f8")
    c.rect(x + margin, y + margin, card_width - 2 * margin, card_height - 2 * margin, fill=True, stroke=False)

    c.setFillColor("black")

    # Title (centered)
    c.setFont("OpenSansExtraBold", 12)
    c.drawCentredString(x + card_width / 2, y + card_height - 12 * mm, main_cat)

    # Subcategory position and wrapping (left aligned at 15mm from left)
    c.setFont("OpenSansBold", 9)
    subcat_x = x + 15 * mm
    subcat_y_start = y + card_height - 18 * mm
    max_width = card_width - (subcat_x - x) - 5 * mm  # remaining space

    # Break into max 2 lines that fit the space
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = sub_cat.split()
    lines = []
    line = ''
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, "OpenSansBold", 9) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    lines = lines[:2]

    # SVG image (10mm × 10mm, vertically aligned with first subcategory line)
    svg_path = os.path.join("images", image_name)
    svg_size = 10 * mm
    if image_name and os.path.exists(svg_path):
        drawing = svg2rlg(svg_path)
        scale_x = svg_size / drawing.width
        scale_y = svg_size / drawing.height
        drawing.scale(scale_x, scale_y)
        renderPDF.draw(
            drawing,
            c,
            x + 5 * mm,  # left margin
            subcat_y_start - 6 * mm  # fine-tuned vertical alignment
        )

    # Draw subcategory text lines
    c.setFillColor("#808080")
    for i, line in enumerate(lines):
        c.drawString(subcat_x, subcat_y_start - (i * 5 * mm), line)

    # Card number (moved 10mm up, gray)
    c.setFont("OpenSans", 9)
    c.setFillColor("#a0a0a0")
    c.drawCentredString(x + card_width / 2, y + card_height - 33 * mm, f"Carte n°{card['Numéro']}")
    c.setFillColor("black")

    # Movements (moved 10mm up), bold if contains "SEUGUI"
    y_offset = 38 * mm
    for move in card["Mouvements"]:
        if "SEUGUI" in move.upper():
            c.setFont("OpenSansBold", 9)
        else:
            c.setFont("OpenSans", 9)
        c.drawCentredString(x + card_width / 2, y + card_height - y_offset, move)
        y_offset += 5 * mm


    # QR code (still centered at bottom)
    qr_url = f"{video_url}?t={card['Marqueur']}"
    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    qr_img = ImageReader(buffer)
    qr_size = 30 * mm
    c.drawImage(
        qr_img,
        x + (card_width - qr_size) / 2,
        y + 5 * mm,
        width=qr_size,
        height=qr_size
    )


# Draw all cards
card_counter = 0
for main_cat, subcats in kibon_data.items():
    for sub_cat, content in subcats.items():
        video_url = content["Vidéo"]
        color = config_data.get(main_cat, {}).get(sub_cat, {}).get("color", "ffffff")
        image_name = config_data.get(main_cat, {}).get(sub_cat, {}).get("image", "")
        for card in content["Cartes"]:
            col = card_counter % cards_per_row
            row = (card_counter // cards_per_row) % cards_per_col
            x = col * card_width
            y = page_height - (row + 1) * card_height
            draw_card(pdf, x, y, main_cat, sub_cat, card, video_url, color, image_name)
            card_counter += 1
            if card_counter % (cards_per_row * cards_per_col) == 0:
                pdf.showPage()

pdf.save()
print("PDF created: kibon.pdf")
