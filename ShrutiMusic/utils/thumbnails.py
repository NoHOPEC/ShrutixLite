import asyncio, os, re, math, httpx, aiofiles
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from aiofiles.os import path as aiopath
from py_yt import VideosSearch
from ShrutiMusic import app
from ..logging import LOGGER

WIDTH, HEIGHT = 1280, 720
CENTER_BOX = (240, 130, 1040, 590)

def load_fonts():
    try:
        return {
            "title": ImageFont.truetype("ShrutiMusic/assets/font.ttf", 46),
            "artist": ImageFont.truetype("ShrutiMusic/assets/cfont.ttf", 28),
            "meta": ImageFont.truetype("ShrutiMusic/assets/cfont.ttf", 22),
        }
    except:
        return {
            "title": ImageFont.load_default(),
            "artist": ImageFont.load_default(),
            "meta": ImageFont.load_default(),
        }

FONTS = load_fonts()

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines[:2]

def fit_title(draw, text, max_width):
    size = 46
    while size > 28:
        font = ImageFont.truetype("ShrutiMusic/assets/font.ttf", size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= 2:
            return font, lines
        size -= 2
    return FONTS["title"], wrap_text(draw, text, FONTS["title"], max_width)

async def fetch_image(url):
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=5)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return ImageOps.fit(img, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)

def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)
    return m

def glass_panel(bg):
    x1, y1, x2, y2 = CENTER_BOX
    region = bg.crop(CENTER_BOX).filter(ImageFilter.GaussianBlur(20))
    overlay = Image.new("RGBA", region.size, (0, 0, 0, 120))
    region = Image.alpha_composite(region, overlay)
    mask = rounded_mask(region.size, 32)
    bg.paste(region, CENTER_BOX[:2], mask)
    return bg

def rounded_thumb(img):
    img = ImageOps.fit(img, (200, 200), Image.Resampling.LANCZOS)
    mask = rounded_mask((200, 200), 26)
    img.putalpha(mask)
    return img

def visualizer(bg, cx, cy, color):
    draw = ImageDraw.Draw(bg)
    for i in range(40):
        a = (i / 40) * math.pi * 2
        h = 18 + (i % 4) * 8
        x1 = cx + int(92 * math.cos(a))
        y1 = cy + int(92 * math.sin(a))
        x2 = cx + int((92 + h) * math.cos(a))
        y2 = cy + int((92 + h) * math.sin(a))
        draw.line((x1, y1, x2, y2), color + (140,), 3)
    return bg

def format_views(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(v)

async def gen_thumb(videoid):
    if not re.match(r"^[\w-]{11}$", videoid):
        return ""

    path = f"database/photos/{videoid}.png"
    os.makedirs("database/photos", exist_ok=True)

    data = (await VideosSearch(f"https://youtube.com/watch?v={videoid}", limit=1).next())["result"][0]
    title = data.get("title", "Unknown")
    artist = data.get("channel", {}).get("name", "Unknown")
    thumb_url = data["thumbnails"][0]["url"].split("?")[0]
    views = int(data.get("viewCount", {}).get("text", "0").replace(",", "").replace(" views", "") or 0)

    bg = await fetch_image(thumb_url)
    bg = glass_panel(bg)

    cover = rounded_thumb(bg.copy())
    px, py = 290, 210
    bg.paste(cover, (px, py), cover)

    visualizer(bg, px + 100, py + 100, (255, 215, 120))

    draw = ImageDraw.Draw(bg)
    title_font, title_lines = fit_title(draw, title, 440)

    tx, ty = 530, 200
    for line in title_lines:
        draw.text((tx, ty), line, (255, 255, 255), font=title_font)
        ty += title_font.size + 4

    draw.text((tx, ty + 8), artist, (220, 220, 220), font=FONTS["artist"])
    draw.text((tx, ty + 46), f"{format_views(views)} Views", (180, 180, 180), font=FONTS["meta"])
    draw.text((tx + 180, ty + 46), f"@{app.username}", (180, 180, 180), font=FONTS["meta"])

    bg = ImageEnhance.Contrast(bg).enhance(1.15)
    bg = ImageEnhance.Color(bg).enhance(1.2)

    bg.save(path, "PNG", optimize=True)
    bg.close()
    return path
