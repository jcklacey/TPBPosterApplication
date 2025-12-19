import time
import os
import csv
import urllib.request
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import qrcode

Image.MAX_IMAGE_PIXELS = None  # remove the limit

def flatten_to_rgb(img, bg_colour=(255, 255, 255)):
    img = img.convert("RGBA")
    bg = Image.new("RGB", img.size, bg_colour)
    alpha = img.getchannel("A")
    bg.paste(img, mask=alpha)

    pixels = bg.load()
    for y in range(bg.height):
        for x in range(bg.width):
            if alpha.getpixel((x, y)) == 0:
                pixels[x, y] = bg_colour

    return bg


def process_poster_csv(file_path, save_dir, progress_callback=None):
    print(f"📂 Processing CSV: {file_path}")

    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    total_rows = len(rows)
    print(f"🧾 Found {total_rows} rows")

    shipment_totals = defaultdict(int)
    for row in rows:
        shipment_id = row.get("Shipment id", "").strip()
        if shipment_id:
            shipment_totals[shipment_id] += 1

    shipment_counters = defaultdict(int)

    for i, row in enumerate(rows, start=1):
        itemID = row.get("Id", "").strip()
        shipment_id = row.get("Shipment id", "").strip()
        shipment_item = row.get("Shipment item number", "").strip()
        artwork_url = row.get("Artwork 1 artwork file url", "").strip()

        if not itemID or not shipment_id or not artwork_url:
            continue

        shipment_counters[shipment_id] += 1
        item_index = shipment_counters[shipment_id]
        total_items = shipment_totals[shipment_id]

        file_name = f"{shipment_id}-{shipment_item}"

        if progress_callback:
            progress_callback(f"Downloading {file_name} ({i}/{total_rows})")

        local_file_path = os.path.join(save_dir, f"{file_name}.pdf")
        urllib.request.urlretrieve(artwork_url, local_file_path)

        if progress_callback:
            progress_callback(f"Generating {file_name}...")

        generate_dynamic_poster(
            poster_path=local_file_path,
            itemID=itemID,
            shipment_id=shipment_id,
            shipment_item=shipment_item,
            item_index=item_index,
            total_items=total_items,
            file_name=file_name,
            save_dir=save_dir,
            index=i,
            total=total_rows
        )

        time.sleep(0.25)

    if progress_callback:
        progress_callback("All files processed ✅")


def generate_dynamic_poster(
    poster_path,
    itemID,
    shipment_id,
    shipment_item,
    item_index,
    total_items,
    file_name,
    save_dir,
    index,
    total
):
    try:
        if poster_path.lower().endswith(".pdf"):
            img = convert_from_path(poster_path, dpi=300)[0]
        else:
            img = Image.open(poster_path).convert("RGB")

        bottom_margin = 10
        line_thickness = 10

        template_bg = Image.new(
            "RGB",
            (img.width, img.height + bottom_margin),
            (255, 255, 255)
        )
        template_bg.paste(img, (0, 0))

        draw = ImageDraw.Draw(template_bg)
        draw.rectangle(
            [0, template_bg.height - line_thickness,
             template_bg.width, template_bg.height],
            fill=(255, 0, 0)
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(itemID)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white") \
                   .convert("RGB") \
                   .resize((200, 200), Image.Resampling.LANCZOS)

        combined_height = template_bg.height + 220
        combined_img = Image.new("RGB", (template_bg.width, combined_height), (255, 255, 255))
        combined_img.paste(template_bg, (0, 0))
        combined_img.paste(qr_img, (0, template_bg.height + 10))

        draw = ImageDraw.Draw(combined_img)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            font = ImageFont.load_default()

        shipment_text = f"Shipment ID: {shipment_id}\nItem: {item_index} of {total_items}"

        draw.multiline_text(
            (220, template_bg.height + 30),
            shipment_text,
            fill=(0, 0, 0),
            font=font
        )

        output_path = os.path.join(save_dir, f"{file_name}_{index}.png")
        combined_img.save(output_path, dpi=(300, 300))

    finally:
        try:
            os.remove(poster_path)
        except Exception:
            pass
