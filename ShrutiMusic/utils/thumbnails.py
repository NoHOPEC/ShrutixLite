import asyncio, os, re, httpx, aiofiles, aiofiles.os
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from aiofiles.os import path as aiopath
from py_yt import VideosSearch

from ..logging import LOGGER
from ShrutiMusic import app

def load_fonts():
    try:
        return {
            "cfont": ImageFont.truetype("ShrutiMusic/assets/cfont.ttf", 24),
            "tfont": ImageFont.truetype("ShrutiMusic/assets/font.ttf", 34),
            "sfont": ImageFont.truetype("ShrutiMusic/assets/cfont.ttf", 20),
        }
    except Exception as e:
        LOGGER.error("Font loading error: %s, using default fonts", e)
        return {
            "cfont": ImageFont.load_default(),
            "tfont": ImageFont.load_default(),
            "sfont": ImageFont.load_default(),
        }

FONTS = load_fonts()

FALLBACK_IMAGE_PATH = "ShrutiMusic/assets/controller.png"
YOUTUBE_IMG_URL = "https://i.ytimg.com/vi/default.jpg"

async def resize_youtube_thumbnail(img: Image.Image) -> Image.Image:
    target_width, target_height = 1280, 720
    aspect_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if aspect_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * aspect_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / aspect_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    img = img.crop((left, top, right, bottom))
    enhanced = ImageEnhance.Sharpness(img).enhance(1.5)
    img.close()
    return enhanced

async def fetch_image(url: str) -> Image.Image:
    async with httpx.AsyncClient() as client:
        try:
            if not url:
                raise ValueError("No thumbnail URL provided")
            response = await client.get(url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            if url.startswith("https://i.ytimg.com"):
                img = await resize_youtube_thumbnail(img)
            else:
                img.close()
                img = Image.new("RGBA", (1280, 720), (255, 255, 255, 255))
            return img
        except Exception as e:
            LOGGER.error("Image loading error for URL %s: %s", url, e)
            try:
                response = await client.get(YOUTUBE_IMG_URL, timeout=5)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content)).convert("RGBA")
                img = await resize_youtube_thumbnail(img)
                return img
            except Exception as e:
                LOGGER.error("YouTube fallback image error: %s", e)
                try:
                    async with aiofiles.open(FALLBACK_IMAGE_PATH, mode="rb") as f:
                        img = Image.open(BytesIO(await f.read())).convert("RGBA")
                        img = await resize_youtube_thumbnail(img)
                        return img
                except Exception as e:
                    LOGGER.error("Local fallback image error: %s", e)
                    return Image.new("RGBA", (1280, 720), (255, 255, 255, 255))

def clean_text(text: str, limit: int = 25) -> str:
    if not text:
        return "Unknown"
    text = text.strip()
    return f"{text[:limit - 3]}..." if len(text) > limit else text

def get_dominant_color(img: Image.Image) -> tuple:
    small = img.resize((50, 50))
    pixels = list(small.getdata())
    r_total, g_total, b_total = 0, 0, 0
    count = 0
    for pixel in pixels:
        if len(pixel) >= 3:
            r_total += pixel[0]
            g_total += pixel[1]
            b_total += pixel[2]
            count += 1
    if count == 0:
        return (100, 100, 100)
    return (r_total // count, g_total // count, b_total // count)

def add_edge_glow(img: Image.Image) -> Image.Image:
    width, height = img.size
    glow_width = 110
    dominant_color = get_dominant_color(img)
    glow_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for i in range(glow_width):
        progress = 1 - (i / glow_width)
        alpha = int(210 * progress * progress)
        glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow_layer)
        draw.rectangle(
            [i, i, width - i, height - i],
            outline=dominant_color + (alpha,),
            width=2,
        )
        glow_overlay = Image.alpha_composite(glow_overlay, glow_layer)
    result = Image.alpha_composite(img.convert("RGBA"), glow_overlay)
    return result

def make_rounded_rectangle(image: Image.Image, size: tuple = (184, 184)) -> Image.Image:
    width, height = image.size
    side_length = min(width, height)
    crop = image.crop(
        (
            (width - side_length) // 2,
            (height - side_length) // 2,
            (width + side_length) // 2,
            (height + side_length) // 2,
        )
    )
    resize = crop.resize(size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *size), radius=26, fill=255)
    rounded = ImageOps.fit(resize, size)
    rounded.putalpha(mask)
    crop.close()
    resize.close()
    return rounded

def add_audio_visualizer(bg: Image.Image, thumb: Image.Image, center_x: int, center_y: int) -> Image.Image:
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    dominant_color = get_dominant_color(thumb)
    num_bars = 42
    bar_width = 5
    radius_start = 115
    import math
    for i in range(num_bars):
        angle = (i / num_bars) * 2 * math.pi
        bar_height = 24 + (i % 4) * 10
        x1 = center_x + int(radius_start * math.cos(angle))
        y1 = center_y + int(radius_start * math.sin(angle))
        x2 = center_x + int((radius_start + bar_height) * math.cos(angle))
        y2 = center_y + int((radius_start + bar_height) * math.sin(angle))
        alpha = 135 - (i % 4) * 25
        draw.line([x1, y1, x2, y2], fill=dominant_color + (alpha,), width=bar_width)
    for r in range(100, 0, -6):
        alpha = int(18 * (1 - r / 100))
        draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=dominant_color + (alpha,),
        )
    bg = Image.alpha_composite(bg, overlay)
    return bg

def format_views(views: int) -> str:
    if views >= 1000000000:
        return f"{views / 1000000000:.1f}B"
    elif views >= 1000000:
        return f"{views / 1000000:.1f}M"
    elif views >= 1000:
        return f"{views / 1000:.1f}K"
    else:
        return str(views)

def draw_glass_panel(bg: Image.Image, panel_box: tuple, blur_radius: int = 22) -> Image.Image:
    x1, y1, x2, y2 = panel_box
    panel_width = x2 - x1
    panel_height = y2 - y1
    crop = bg.crop(panel_box)
    crop = crop.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    crop = ImageEnhance.Brightness(crop).enhance(0.35)
    glass = Image.new("RGBA", (panel_width, panel_height), (0, 0, 0, 160))
    glass = Image.alpha_composite(crop.convert("RGBA"), glass)
    mask = Image.new("L", (panel_width, panel_height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, panel_width, panel_height), radius=32, fill=255)
    panel = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    panel.paste(glass, (x1, y1), mask)
    shadow = Image.new("RGBA", (panel_width + 40, panel_height + 40), (0, 0, 0, 0))
    shadow_mask = Image.new("L", (panel_width + 40, panel_height + 40), 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle(
        (0, 0, panel_width + 40, panel_height + 40), radius=36, fill=210
    )
    shadow.putalpha(shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=25))
    bg.paste(shadow, (x1 - 20, y1 - 10), shadow)
    bg = Image.alpha_composite(bg, panel)
    return bg

def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, box: tuple, fill: tuple):
    x1, y1, x2, y2 = box
    w, h = draw.textsize(text, font=font)
    tx = x1 + (x2 - x1 - w) // 2
    ty = y1 + (y2 - y1 - h) // 2
    draw.text((tx, ty), text, fill, font=font)

async def gen_thumb(videoid: str) -> str:
    if not videoid or not re.match(r"^[a-zA-Z0-9_-]{11}$", videoid):
        LOGGER.error("Invalid YouTube video ID: %s", videoid)
        return ""

    save_dir = f"database/photos/{videoid}.png"

    try:
        save_dir_parent = "database/photos"
        if not await aiopath.exists(save_dir_parent):
            await asyncio.to_thread(os.makedirs, save_dir_parent)
    except Exception as e:
        LOGGER.error("Failed to create directory %s: %s", save_dir_parent, e)
        return ""

    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]
        title = clean_text(result.get("title", "Unknown Title"), limit=40)
        artist = clean_text(result.get("channel", {}).get("name", "Unknown Artist"), limit=32)
        thumbnail_url = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        views = result.get("viewCount", {}).get("text", "0").replace(" views", "").replace(",", "")
        try:
            views_count = int(views)
            views_text = format_views(views_count)
        except Exception:
            views_text = "0"
    except Exception as e:
        LOGGER.error("YouTube metadata fetch error for video %s: %s", videoid, e)
        title, artist, views_text = "Unknown Title", "Unknown Artist", "0"
        thumbnail_url = YOUTUBE_IMG_URL

    try:
        bot_username = f"@{app.username}"
    except Exception:
        bot_username = "@ShrutiBots"

    thumb = await fetch_image(thumbnail_url)
    bg = thumb.copy()

    bg = ImageEnhance.Brightness(bg).enhance(0.75)
    bg = ImageEnhance.Color(bg).enhance(1.15)
    bg = ImageEnhance.Contrast(bg).enhance(1.05)

    panel_width = 900
    panel_height = 320
    center_x = bg.width // 2
    center_y = bg.height // 2
    panel_x1 = center_x - panel_width // 2
    panel_y1 = center_y - panel_height // 2
    panel_x2 = center_x + panel_width // 2
    panel_y2 = center_y + panel_height // 2
    bg = draw_glass_panel(bg, (panel_x1, panel_y1, panel_x2, panel_y2))

    cover_size = (210, 210)
    cover_x = panel_x1 + 40
    cover_y = panel_y1 + (panel_height - cover_size[1]) // 2
    center_cover_x = cover_x + cover_size[0] // 2
    center_cover_y = cover_y + cover_size[1] // 2

    bg = add_audio_visualizer(bg, thumb, center_cover_x, center_cover_y)

    cover_img = make_rounded_rectangle(thumb, size=cover_size)
    bg.paste(cover_img, (cover_x, cover_y), cover_img)

    draw = ImageDraw.Draw(bg)

    text_left = cover_x + cover_size[0] + 40
    text_right = panel_x2 - 40
    title_box = (text_left, panel_y1 + 40, text_right, panel_y1 + 40 + 50)
    artist_box = (text_left, panel_y1 + 95, text_right, panel_y1 + 95 + 40)

    title_text = title
    artist_text = artist

    def truncate_to_width(text, font, max_width):
        while text and draw.textsize(text, font=font)[0] > max_width:
            text = text[:-1]
        return text + "..." if text else ""

    max_text_width = text_right - text_left
    if draw.textsize(title_text, font=FONTS["tfont"])[0] > max_text_width:
        title_text = truncate_to_width(title_text, FONTS["tfont"], max_text_width)
    if draw.textsize(artist_text, font=FONTS["cfont"])[0] > max_text_width:
        artist_text = truncate_to_width(artist_text, FONTS["cfont"], max_text_width)

    draw.text((title_box[0], title_box[1]), title_text, (255, 255, 255), font=FONTS["tfont"])
    draw.text((artist_box[0], artist_box[1]), artist_text, (210, 210, 210), font=FONTS["cfont"])

    meta_y = artist_box[1] + 55
    meta_x = text_left
    meta_color = (200, 200, 200)

    draw.text((meta_x, meta_y), f"{views_text} Views", meta_color, font=FONTS["sfont"])
    meta_x += draw.textsize(f"{views_text} Views   ", font=FONTS["sfont"])[0]
    draw.text((meta_x, meta_y), bot_username, meta_color, font=FONTS["sfont"])

    duration_text = "Duration: 3:45"
    duration_width, _ = draw.textsize(duration_text, font=FONTS["sfont"])
    duration_x = text_right - duration_width
    draw.text((duration_x, meta_y), duration_text, (185, 185, 185), font=FONTS["sfont"])

    bg = add_edge_glow(bg)
    bg = ImageEnhance.Contrast(bg).enhance(1.12)
    bg = ImageEnhance.Color(bg).enhance(1.18)

    try:
        await asyncio.to_thread(bg.save, save_dir, format="PNG", quality=95, optimize=True)
        if await aiopath.exists(save_dir):
            thumb.close()
            cover_img.close()
            bg.close()
            return save_dir
        LOGGER.error("Failed to save thumbnail at %s", save_dir)
    except Exception as e:
        LOGGER.error("Thumbnail save error for %s: %s", save_dir, e)

    thumb.close()
    cover_img.close()
    bg.close()
    return ""
