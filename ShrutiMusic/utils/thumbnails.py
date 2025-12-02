import asyncio, os, re, httpx, aiofiles.os
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
            "tfont": ImageFont.truetype("ShrutiMusic/assets/font.ttf", 30),
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
    glow_width = 100
    
    dominant_color = get_dominant_color(img)
    
    glow_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    for i in range(glow_width):
        progress = 1 - (i / glow_width)
        alpha = int(180 * progress * progress)
        
        glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow_layer)
        
        draw.rectangle([i, i, width - i, height - i], 
                      outline=dominant_color + (alpha,), 
                      width=2)
        
        glow_overlay = Image.alpha_composite(glow_overlay, glow_layer)
    
    result = Image.alpha_composite(img.convert("RGBA"), glow_overlay)
    return result

async def add_controls(img: Image.Image) -> Image.Image:
    img = img.filter(ImageFilter.GaussianBlur(radius=10))
    box = (305, 125, 975, 595)
    region = img.crop(box)
    
    try:
        controls = Image.open("ShrutiMusic/assets/controls.png").convert("RGBA")
        controls = controls.resize((1200, 320), Image.Resampling.LANCZOS)
        controls = ImageEnhance.Sharpness(controls).enhance(5.0)
        controls = ImageEnhance.Contrast(controls).enhance(1.0)
        controls = controls.resize((600, 160), Image.Resampling.LANCZOS)
        controls_x = 305 + (670 - 600) // 2 
        controls_y = 415  
    except Exception as e:
        LOGGER.error("Controls image loading error: %s", e)
        controls = Image.new("RGBA", (600, 160), (0, 0, 0, 0))
        controls_x, controls_y = 335, 415

    dark_region = ImageEnhance.Brightness(region).enhance(0.5)
    mask = Image.new("L", dark_region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, box[2] - box[0], box[3] - box[1]), radius=20, fill=255
    )

    img.paste(dark_region, box, mask)
    img.paste(controls, (controls_x, controls_y), controls)
    
    region.close()
    controls.close()
    return img

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
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *size), radius=20, fill=255)

    rounded = ImageOps.fit(resize, size)
    rounded.putalpha(mask)
    crop.close()
    resize.close()
    return rounded

def add_audio_visualizer(bg: Image.Image, thumb: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    dominant_color = get_dominant_color(thumb)
    
    center_x = 750
    center_y = 290
    
    num_bars = 30
    bar_width = 4
    radius_start = 60
    radius_end = 95
    
    import math
    for i in range(num_bars):
        angle = (i / num_bars) * 2 * math.pi
        bar_height = 20 + (i % 3) * 10
        
        x1 = center_x + int(radius_start * math.cos(angle))
        y1 = center_y + int(radius_start * math.sin(angle))
        x2 = center_x + int((radius_start + bar_height) * math.cos(angle))
        y2 = center_y + int((radius_start + bar_height) * math.sin(angle))
        
        alpha = 120 - (i % 3) * 30
        draw.line([x1, y1, x2, y2], fill=dominant_color + (alpha,), width=bar_width)
    
    for r in range(50, 0, -5):
        alpha = int(15 * (1 - r / 50))
        draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=dominant_color + (alpha,)
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
        title = clean_text(result.get("title", "Unknown Title"), limit=25)
        artist = clean_text(result.get("channel", {}).get("name", "Unknown Artist"), limit=28)
        thumbnail_url = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        views = result.get("viewCount", {}).get("text", "0").replace(" views", "").replace(",", "")
        try:
            views_count = int(views)
            views_text = format_views(views_count)
        except:
            views_text = "0"
    except Exception as e:
        LOGGER.error("YouTube metadata fetch error for video %s: %s", videoid, e)
        title, artist, views_text = "Unknown Title", "Unknown Artist", "0"
        thumbnail_url = YOUTUBE_IMG_URL

    try:
        bot_username = f"@{app.username}"
    except:
        bot_username = "@ShrutiBots"

    thumb = await fetch_image(thumbnail_url)
    bg = await add_controls(thumb)
    image = make_rounded_rectangle(thumb, size=(184, 184))

    paste_x, paste_y = 325, 155 
    bg.paste(image, (paste_x, paste_y), image)
    
    draw = ImageDraw.Draw(bg)
    draw.text((540, 155), title, (255, 255, 255), font=FONTS["tfont"])  
    draw.text((540, 200), artist, (255, 255, 255), font=FONTS["cfont"])
    
    draw.text((540, 235), f"👁 {views_text} Views", (200, 200, 200), font=FONTS["sfont"])
    draw.text((750, 235), bot_username, (200, 200, 200), font=FONTS["sfont"])

    bg = add_audio_visualizer(bg, thumb)
    bg = add_edge_glow(bg)
    
    bg = ImageEnhance.Contrast(bg).enhance(1.1)
    bg = ImageEnhance.Color(bg).enhance(1.2)

    try:
        await asyncio.to_thread(bg.save, save_dir, format="PNG", quality=95, optimize=True)
        if await aiopath.exists(save_dir):
            thumb.close()
            image.close()
            bg.close()
            return save_dir
        LOGGER.error("Failed to save thumbnail at %s", save_dir)
    except Exception as e:
        LOGGER.error("Thumbnail save error for %s: %s", save_dir, e)

    thumb.close()
    image.close()
    bg.close()
    return ""
