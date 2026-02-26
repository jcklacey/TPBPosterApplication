import time
import os
import shutil
import csv
import urllib.request
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import qrcode
from datetime import datetime, timedelta

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
        qrCode = row.get("QR code", "").strip()
        shipment_id = row.get("Shipment id", "").strip()
        shipment_item = row.get("Shipment item number", "").strip()
        artwork_url = row.get("Artwork 1 artwork file url", "").strip()
        product_type = row.get("Product type", "").strip()
        
        date_received_raw = row.get("Date received", "").strip()

        due_date_str = "N/A"
        if date_received_raw:
            try:
                # Trim fractional seconds to 6 digits if present
                if "." in date_received_raw:
                    main, rest = date_received_raw.split(".", 1)
                    fractional = rest.split("+", 1)[0][:6]
                    tz = "+" + rest.split("+", 1)[1] if "+" in rest else ""
                    date_received_raw = f"{main}.{fractional}{tz}"

                received_dt = datetime.fromisoformat(date_received_raw)
                # Add 1 day to date received to generate Due Date
                due_dt = received_dt + timedelta(days=1)
                due_date_str = f"{due_dt.strftime('%d/%m/%Y')}"
            except Exception as e:
                print(f"⚠️ Date parse failed: {date_received_raw} → {e}")

        if not qrCode or not shipment_id or not artwork_url:
            continue

        shipment_counters[shipment_id] += 1
        item_index = shipment_counters[shipment_id]
        total_items = shipment_totals[shipment_id]
        
        print("total_items comes out as: ")
        print(total_items)

        file_name = f"{shipment_id}-{shipment_item}"

        if progress_callback:
            progress_callback(f"Downloading {file_name} ({i}/{total_rows})")

        local_file_path = os.path.join(save_dir, f"{file_name}.pdf")
        urllib.request.urlretrieve(artwork_url, local_file_path)       


        if progress_callback:
            progress_callback(f"Generating {file_name}...")

        generate_dynamic_poster(
            poster_path=local_file_path,
            qrCode=qrCode,
            shipment_id=shipment_id,
            shipment_item=shipment_item,
            item_index=item_index,
            total_items=total_items,
            due_date_str=due_date_str,
            file_name=file_name,
            save_dir=save_dir,
            index=i,
            total=total_rows,
            product_type=product_type
        )

        time.sleep(0.25)
        
    multi_sort()    

    if progress_callback:
        progress_callback("All files processed ✅")


def generate_dynamic_poster(
    poster_path,
    qrCode,
    shipment_id,
    shipment_item,
    item_index,
    total_items,
    due_date_str,
    file_name,
    save_dir,
    index,
    total,
    product_type
):

    try:
        if poster_path.lower().endswith(".pdf"):
            img = convert_from_path(poster_path, dpi=300)[0]
        else:
            img = Image.open(poster_path).convert("RGB")

        ##############################
        # TRY CROP HERE - Has to be after its downloaded and converted to 300dpi, but before we add our info down the bottom.
        ##############################

        # MM to Pixels conversion
        # px = MM * (dpi/25.4)
        # 4mm x (300/25.4) = 47
        crop_px = 47
        w, h = img.size
        img = img.crop((crop_px, crop_px, w - crop_px, h - crop_px))

        #Add in an IF statement if we need to change the crop_px based on the Poster Size (product_type)
        ###############################

        bottom_margin = 10
        line_thickness = 10

        template_bg = Image.new(
            "RGB",
            (img.width, img.height + bottom_margin),
            (255, 255, 255)
        )
        template_bg.paste(img, (0, 0))

        draw = ImageDraw.Draw(template_bg)
        
        y = template_bg.height - (line_thickness // 2)

        dash_length = 20   # length of each dash
        gap_length = 10    # space between dashes

        x = 0
        while x < template_bg.width:
            draw.line(
                (x, y, min(x + dash_length, template_bg.width), y),
                fill=(255, 0, 0),
                width=line_thickness
            )
            x += dash_length + gap_length
        

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(qrCode)
        qr.make(fit=True)

        #QRCODE insert
        #-----------------------------------
        qr_img = qr.make_image(fill_color="black", back_color="lightblue") \
                   .convert("RGB") \
                   .resize((200, 200), Image.Resampling.LANCZOS)
        #-----------------------------------

        combined_height = template_bg.height + 220
        combined_img = Image.new("RGB", (template_bg.width, combined_height), (255, 255, 255))
        combined_img.paste(template_bg, (0, 0))
        combined_img.paste(qr_img, (0, template_bg.height + 10))

        draw = ImageDraw.Draw(combined_img)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            font = ImageFont.load_default()

        shipment_text = (
            f"Shipment ID: --- {shipment_id} \n"
            f"Item: --- {item_index} of {total_items} \n"
            f"Due Date: --- {due_date_str} \n"
            f"Product Type: --- {product_type} \n"
        )

        # INSERT TEXT -  as single line
        # draw.text((15, template_bg.height + 5), shipment_text, fill=(0, 0, 0), font=font)
        
        # INSERT TEXT - as multiline 
        draw.multiline_text(
            (230, template_bg.height + 30),
            shipment_text,
            fill=(0, 0, 0),
            font=font)
        
        
        output_path = os.path.join(save_dir, f"{file_name}_{index}.png")

        if total_items > 1:
            output_path = os.path.join(save_dir, f"{file_name}_{index}-Multi.png")

        combined_img.save(output_path, dpi=(300, 300))

    finally:
        try:
            os.remove(poster_path)
        except Exception:
            pass
            
def multi_sort():
    HOT_FOLDER = "C:/Users/DTFPrintBar/AppData/Local/PosterEngine/HotFolder/"
    MULTI = os.path.join(HOT_FOLDER, "Multi")

    os.makedirs(MULTI, exist_ok=True)

    for filename in os.listdir(HOT_FOLDER):
        if filename.endswith("-Multi.png"):
            src = os.path.join(HOT_FOLDER, filename)
            dst = os.path.join(MULTI, filename)
            
            print(f"📁 Moving {filename} → Multi/")
            shutil.move(src, dst)
