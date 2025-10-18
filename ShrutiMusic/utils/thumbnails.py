import os
import re
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def changeImageSize(maxWidth, maxHeight, image):
    ratio = min(maxWidth / image.size[0], maxHeight / image.size[1])
    newSize = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    return image.resize(newSize, Image.LANCZOS)

def truncate_ellipsis(text, max_chars=20):
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    if ' ' in truncated:
        truncated = truncated[:truncated.rfind(' ')]
    return truncated + "..." if len(truncated) > 0 else text[:max_chars-3] + "..."

def ensure_text_fits(draw, text, font, max_width):
    text_width = draw.textlength(text, font=font)
    if text_width <= max_width:
        return text
    low = 1
    high = len(text)
    best = ""
    while low <= high:
        mid = (low + high) // 2
        truncated = truncate_ellipsis(text, mid)
        truncated_width = draw.textlength(truncated, font=font)
        if truncated_width <= max_width:
            best = truncated
            low = mid + 1
        else:
            high = mid - 1
    return best if best else "..."

def fit_text(draw, text, max_width, font_path, start_size, min_size):
    size = start_size
    while size >= min_size:
        try:
            font = ImageFont.truetype(font_path, size)
            if draw.textlength(text, font=font) <= max_width:
                return font
        except:
            pass
        size -= 1
    return ImageFont.load_default()

async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "00:00")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, mode="wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")
        bg_img = changeImageSize(1280, 720, base_img).convert("RGBA")
        blurred_bg = bg_img.filter(ImageFilter.GaussianBlur(20))
        final_bg = blurred_bg.copy()

        try:
            overlay_path = "ShrutiMusic/assets/ShrutiBots.png"
            overlay_img = Image.open(overlay_path).convert("RGBA")
            overlay_img = overlay_img.resize((1280, 720))
            final_bg.paste(overlay_img, (0, 0), overlay_img)
        except Exception as overlay_err:
            print(f"Overlay error: {overlay_err}")

        draw = ImageDraw.Draw(final_bg)

        thumb_size = 423
        corner_radius = 25
        mask = Image.new('L', (thumb_size, thumb_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, thumb_size, thumb_size), radius=corner_radius, fill=255)
        thumb_rect = base_img.resize((thumb_size, thumb_size))
        thumb_rect.putalpha(mask)

        thumb_x = 261
        thumb_y = (721 - thumb_size) // 2
        final_bg.paste(thumb_rect, (thumb_x, thumb_y), thumb_rect)

        info_x = thumb_x + thumb_size + 60
        info_y = thumb_y
        max_text_width = 1280 - info_x - 80

        font_path_regular = "ShrutiMusic/assets/font2.ttf"
        font_path_bold = "ShrutiMusic/assets/font3.ttf"

        limited_title = truncate_ellipsis(title, max_chars=15 if len(title) > 15 else max(10, len(title)))


        font_small = ImageFont.truetype(font_path_regular, 17)
        font_medium = ImageFont.truetype(font_path_regular, 20)
        font_title = fit_text(draw, limited_title, max_text_width, font_path_bold, 34, 20)
        
        title_text = ensure_text_fits(draw, limited_title, font_title, max_text_width)
        draw.text((info_x - 40, info_y + 120), title_text, fill=(0, 0, 0), font=font_title)
     
        artist_text = ensure_text_fits(draw, channel, font_medium, max_text_width)
        draw.text((info_x - 40, info_y + 170), artist_text, fill=(0, 0, 0), font=font_medium)

        duration_text = f"00:00                                                                           {duration}"
        duration_text = ensure_text_fits(draw, duration_text, font_small, max_text_width)
        draw.text((info_x - 40, info_y + 245), duration_text, fill=(150, 150, 150), font=font_small)

        output_path = CACHE_DIR / f"{videoid}_styled.png"
        final_bg.save(output_path)

        try:
            os.remove(thumb_path)
        except:
            pass

        return str(output_path)

    except Exception as e:
        print(f"[ShrutiMusic Error] {e}")
        traceback.print_exc()
        return None
