#!env/bin/python3
# -*- coding: utf-8 -*-

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
in a 4×2 layout. Each front page is followed by a matching back page
with visual elements for double-sided printing.
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

#Metadata
pdf.setTitle("FFTDA.fr · Examens Dan 1 à 5 · Module A · KIBON")
pdf.setSubject("Les fiches de révision des Kibons de Taekwondo avec QR-code vers les vidéos")
pdf.setAuthor("Fédération Française de Taekwondo et disciplines associées")
pdf.setKeywords("Taekwondo, Kibon, FFTDA, Passage de grade, Module A")
pdf.setCreator("benjamin@moudok.fr")

# Register fonts
pdfmetrics.registerFont(TTFont("OpenSans", "fonts/Open_Sans/static/OpenSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("OpenSansBold", "fonts/Open_Sans/static/OpenSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("OpenSansExtraBold", "fonts/Open_Sans/static/OpenSans-ExtraBold.ttf"))

def hex_to_rgb(hex_str):
    hex_str = hex_str.strip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255. for i in (0, 2, 4))

def draw_card(c, x, y, main_cat, sub_cat, card, video_url, color_code, image_name):
    c.setFillColorRGB(*hex_to_rgb(color_code))
    c.rect(x + 5 * mm, y + 5 * mm, card_width - 10 * mm, card_height - 10 * mm, fill=True, stroke=False)

    margin = 6 * mm
    c.setFillColor("#f8f8f8")
    c.rect(x + margin, y + margin, card_width - 2 * margin, card_height - 2 * margin, fill=True, stroke=False)

    c.setFillColor("black")
    c.setFont("OpenSansExtraBold", 12)
    c.drawCentredString(x + card_width / 2, y + card_height - 12 * mm, main_cat)

    c.setFont("OpenSansBold", 9)
    subcat_x = x + 15 * mm
    subcat_y_start = y + card_height - 18 * mm
    max_width = card_width - (subcat_x - x) - 5 * mm

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

    svg_path = os.path.join("images", image_name)
    svg_size = 10 * mm
    if image_name and os.path.exists(svg_path):
        drawing = svg2rlg(svg_path)
        scale_x = svg_size / drawing.width
        scale_y = svg_size / drawing.height
        drawing.scale(scale_x, scale_y)
        renderPDF.draw(drawing, c, x + 5 * mm, subcat_y_start - 6 * mm)

    c.setFillColor("#808080")
    for i, line in enumerate(lines):
        c.drawString(subcat_x, subcat_y_start - (i * 5 * mm), line)

    c.setFont("OpenSans", 9)
    c.setFillColor("#a0a0a0")
    c.drawCentredString(x + card_width / 2, y + card_height - 33 * mm, f"Carte n°{card['Numéro']}")
    c.setFillColor("black")

    y_offset = 38 * mm
    for move in card["Mouvements"]:
        if "SEUGUI" in move.upper():
            c.setFont("OpenSansBold", 9)
        else:
            c.setFont("OpenSans", 9)
        c.drawCentredString(x + card_width / 2, y + card_height - y_offset, move)
        y_offset += 5 * mm

    qr_url = f"{video_url}?t={card['Marqueur']}"
    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    qr_img = ImageReader(buffer)
    qr_size = 30 * mm
    c.drawImage(qr_img, x + (card_width - qr_size) / 2, y + 7 * mm, width=qr_size, height=qr_size)

def draw_back_card(c, x, y, main_cat, sub_cat, color_code, image_name):
    c.setFillColorRGB(*hex_to_rgb(color_code))
    c.rect(x + 5 * mm, y + 5 * mm, card_width - 10 * mm, card_height - 10 * mm, fill=True, stroke=False)
    # Header text
    c.setFont("OpenSans", 6)
    c.setFillColor("white")
    c.drawString(x + 8 * mm, y + card_height - 9 * mm, "Source: FFTDA.fr 2022")
    c.drawRightString(x + card_width - 8 * mm, y + card_height - 9 * mm, "moudok.fr")
    center_x = x + card_width / 2
    center_y = y + card_height / 2 + 10 * mm
    radius = 25 * mm
    c.setFillColorRGB(1, 1, 1, alpha=0.5)
    c.circle(center_x, center_y, radius, stroke=False, fill=True)

    svg_path = os.path.join("images", image_name)
    svg_size = 30 * mm
    if image_name and os.path.exists(svg_path):
        drawing = svg2rlg(svg_path)
        scale_x = svg_size / drawing.width
        scale_y = svg_size / drawing.height
        drawing.scale(scale_x, scale_y)
        renderPDF.draw(drawing, c, center_x - svg_size / 2, center_y - svg_size / 2)

    # Black semi-transparent rectangle below category/subcategory
    rect_x = x + 5 * mm
    rect_y = y + card_height / 2 - 38 * mm  # adjust vertically to be below texts
    rect_w = card_width
    rect_h = 15 * mm
    c.setFillColorRGB(0, 0, 0, alpha=0.25)
    c.rect(rect_x, rect_y, rect_w - 10 * mm, rect_h, fill=True, stroke=False)

    c.setFont("OpenSansExtraBold", 18)
    c.setFillColor("black")
    c.drawCentredString(center_x - 0.3 * mm, y + card_height / 2 - 30.3 * mm, main_cat)
    c.drawCentredString(center_x + 0.1 * mm, y + card_height / 2 - 29.9 * mm, main_cat)
    c.setFillColor("white")
    c.drawCentredString(center_x, y + card_height / 2 - 30 * mm, main_cat)
    c.setFont("OpenSans", 6)
    c.drawCentredString(center_x, y + card_height / 2 - 35 * mm, sub_cat)
    c.setFillColor("black")

# Main loop: 8 cards per page, front + back
page_cards = []
card_counter = 0

for main_cat, subcats in kibon_data.items():
    for sub_cat, content in subcats.items():
        video_url = content["Vidéo"]
        color = config_data.get(main_cat, {}).get(sub_cat, {}).get("color", "ffffff")
        image_name = config_data.get(main_cat, {}).get(sub_cat, {}).get("image", "")
        for card in content["Cartes"]:
            page_cards.append((main_cat, sub_cat, card, video_url, color, image_name))

            if len(page_cards) == 8:
                for idx, (main_cat, sub_cat, card, video_url, color, image_name) in enumerate(page_cards):
                    col = idx % cards_per_row
                    row = idx // cards_per_row
                    x = col * card_width
                    y = page_height - (row + 1) * card_height
                    draw_card(pdf, x, y, main_cat, sub_cat, card, video_url, color, image_name)
                pdf.showPage()

                for idx, (main_cat, _, _, _, color, image_name) in enumerate(page_cards):
                    col = idx % cards_per_row
                    row = idx // cards_per_row
                    x = col * card_width
                    y = page_height - (row + 1) * card_height
                    draw_back_card(pdf, x, y, main_cat, sub_cat, color, image_name)
                pdf.showPage()

                page_cards = []

# Render remaining cards
if page_cards:
    for idx, (main_cat, sub_cat, card, video_url, color, image_name) in enumerate(page_cards):
        col = idx % cards_per_row
        row = idx // cards_per_row
        x = col * card_width
        y = page_height - (row + 1) * card_height
        draw_card(pdf, x, y, main_cat, sub_cat, card, video_url, color, image_name)
    pdf.showPage()

    for idx, (main_cat, _, _, _, color, image_name) in enumerate(page_cards):
        col = idx % cards_per_row
        row = idx // cards_per_row
        x = col * card_width
        y = page_height - (row + 1) * card_height
        draw_back_card(pdf, x, y, main_cat, sub_cat, color, image_name)
    pdf.showPage()

pdf.save()
print("PDF created: kibon.pdf")
