import asyncio
import os
import re
import json
from typing import Union
from datetime import datetime, timedelta
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from urllib.parse import urlparse

from ShrutiMusic import app, LOGGER
from ShrutiMusic.utils.formatters import time_to_seconds

MONGO_URI = "mongodb+srv://pr7bup_db_user:1LjZqfNQZRtNDGba@nandquerycluster.3xkifll.mongodb.net/?appName=NandQueryCluster"
YOUTUBE_API_KEY = "AIzaSyBQiay14PC57wRBBT7v2JFRawJNVsPhgGw"
YOUTUBE_API_LIMIT_PER_DAY = 100

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.ShrutiMusic
cache_collection = db.youtube_cache
api_usage_collection = db.api_usage

YOUR_API_URL = None

async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("ShrutiMusic.platforms.Youtube")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa") as response:
                if response.status == 200:
                    YOUR_API_URL = (await response.text()).strip()
                    logger.info("API URL loaded")
    except Exception as e:
        logger.error(f"Error loading API URL: {e}")

try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass

async def check_api_limit():
    try:
        today = datetime.utcnow().date()
        usage_doc = await api_usage_collection.find_one({"date": str(today)})
        if not usage_doc:
            await api_usage_collection.insert_one({
                "date": str(today),
                "count": 0,
                "reset_time": str(datetime.utcnow() + timedelta(days=1))
            })
            return True
        return usage_doc["count"] < YOUTUBE_API_LIMIT_PER_DAY
    except:
        return False

async def increment_api_usage():
    try:
        today = datetime.utcnow().date()
        await api_usage_collection.update_one(
            {"date": str(today)},
            {"$inc": {"count": 1}},
            upsert=True
        )
    except Exception as e:
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        logger.error(f"Failed to increment API usage: {e}")

async def get_from_cache(query_type: str, query: str):
    try:
        cache_key = f"{query_type}:{query.lower()}"
        cached = await cache_collection.find_one({"cache_key": cache_key})
        if cached:
            cache_time = cached.get("cached_at")
            if cache_time:
                cache_datetime = datetime.fromisoformat(cache_time)
                if datetime.utcnow() - cache_datetime < timedelta(days=30):
                    return cached.get("data")
        return None
    except Exception:
        return None

async def save_complete_video_data(video_data: dict):
    try:
        video_id = video_data.get("vidid")
        if not video_id:
            return
        
        complete_data = {
            "cache_key": f"complete:{video_id}",
            "video_id": video_id,
            "title": video_data.get("title", ""),
            "url": video_data.get("link", ""),
            "thumbnail": video_data.get("thumb", ""),
            "duration_min": video_data.get("duration_min", ""),
            "duration_sec": video_data.get("duration_sec", 0),
            "channel": video_data.get("channel", ""),
            "views": video_data.get("views", "0"),
            "publish_date": video_data.get("publish_date", ""),
            "keywords": video_data.get("keywords", []),
            "description": video_data.get("description", ""),
            "cached_at": datetime.utcnow().isoformat(),
            "source": video_data.get("source", "unknown")
        }
        
        await cache_collection.update_one(
            {"cache_key": f"complete:{video_id}"},
            {"$set": complete_data},
            upsert=True
        )
        
        await cache_collection.update_one(
            {"cache_key": f"details:{video_id}"},
            {"$set": {"data": video_data}},
            upsert=True
        )
        
        await cache_collection.update_one(
            {"cache_key": f"track:{video_id}"},
            {"$set": {"data": video_data}},
            upsert=True
        )
        
    except Exception as e:
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        logger.error(f"Cache save error: {e}")

async def get_complete_video_data(video_id: str):
    try:
        cached = await cache_collection.find_one({"cache_key": f"complete:{video_id}"})
        if cached:
            cache_time = cached.get("cached_at")
            if cache_time:
                cache_datetime = datetime.fromisoformat(cache_time)
                if datetime.utcnow() - cache_datetime < timedelta(days=30):
                    return {
                        "title": cached.get("title", ""),
                        "link": cached.get("url", ""),
                        "vidid": cached.get("video_id", ""),
                        "duration_min": cached.get("duration_min", ""),
                        "duration_sec": cached.get("duration_sec", 0),
                        "thumb": cached.get("thumbnail", ""),
                        "channel": cached.get("channel", ""),
                        "views": cached.get("views", "0"),
                        "publish_date": cached.get("publish_date", ""),
                        "keywords": cached.get("keywords", []),
                        "description": cached.get("description", "")
                    }
        return None
    except Exception:
        return None

async def search_youtube_api(query: str):
    logger = LOGGER("ShrutiMusic.platforms.Youtube")
    try:
        if not await check_api_limit():
            logger.warning("Daily API limit reached")
            return None
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "key": YOUTUBE_API_KEY
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("items") and len(data["items"]) > 0:
                        video_id = data["items"][0]["id"]["videoId"]
                        details = await get_video_details_api(video_id)
                        if details:
                            details["source"] = "yt_api"
                            await increment_api_usage()
                            await save_complete_video_data(details)
                            return details
                elif response.status == 403:
                    today = datetime.utcnow().date()
                    await api_usage_collection.update_one(
                        {"date": str(today)},
                        {"$set": {"count": YOUTUBE_API_LIMIT_PER_DAY}},
                        upsert=True
                    )
                    return None
    except Exception as e:
        logger.error(f"YT API Error: {e}")
        return None

async def get_video_details_api(video_id: str):
    logger = LOGGER("ShrutiMusic.platforms.Youtube")
    try:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id,
            "key": YOUTUBE_API_KEY
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("items") and len(data["items"]) > 0:
                        item = data["items"][0]
                        snippet = item["snippet"]
                        content_details = item["contentDetails"]
                        statistics = item.get("statistics", {})
                        
                        duration_sec = parse_iso_duration(content_details["duration"])
                        duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                        
                        thumbnails = snippet["thumbnails"]
                        thumbnail = (
                            thumbnails.get("maxres", {}).get("url") or
                            thumbnails.get("high", {}).get("url") or
                            thumbnails.get("medium", {}).get("url") or
                            thumbnails.get("default", {}).get("url")
                        )
                        
                        if thumbnail and "?" in thumbnail:
                            thumbnail = thumbnail.split("?")[0]
                        
                        tags = snippet.get("tags", [])
                        description = snippet.get("description", "")
                        
                        return {
                            "title": snippet["title"],
                            "link": f"https://www.youtube.com/watch?v={video_id}",
                            "vidid": video_id,
                            "duration_min": duration_min,
                            "duration_sec": duration_sec,
                            "thumb": thumbnail,
                            "channel": snippet.get("channelTitle", ""),
                            "publish_date": snippet.get("publishedAt", ""),
                            "views": statistics.get("viewCount", "0"),
                            "keywords": tags[:10] if tags else [],
                            "description": description[:200]
                        }
                return None
    except Exception as e:
        logger.error(f"YT API Details error: {e}")
        return None

def parse_iso_duration(duration: str) -> int:
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

async def get_telegram_file(telegram_link: str, video_id: str, file_type: str) -> str:
    logger = LOGGER("ShrutiMusic.platforms.Youtube")
    try:
        extension = ".webm" if file_type == "audio" else ".mkv"
        file_path = os.path.join("downloads", f"{video_id}{extension}")
        
        if os.path.exists(file_path):
            return file_path
        
        parsed = urlparse(telegram_link)
        parts = parsed.path.strip("/").split("/")
        
        if len(parts) < 2:
            return None
            
        channel_name = parts[0]
        message_id = int(parts[1])
        
        msg = await app.get_messages(channel_name, message_id)
        os.makedirs("downloads", exist_ok=True)
        await msg.download(file_name=file_path)
        
        timeout = 0
        while not os.path.exists(file_path) and timeout < 60:
            await asyncio.sleep(0.5)
            timeout += 0.5
        
        if os.path.exists(file_path):
            return file_path
        else:
            return None
    except Exception as e:
        logger.error(f"Telegram download failed: {e}")
        return None

async def download_song(link: str) -> str:
    global YOUR_API_URL
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            return None
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger = LOGGER("ShrutiMusic.platforms.Youtube")

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                data = await response.json()
                if response.status != 200:
                    return None

                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "audio")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        return None
                
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    async with session.get(
                        stream_url,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as file_response:
                        if file_response.status != 200:
                            return None
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                f.write(chunk)
                        return file_path
                else:
                    return None
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        logger.error(f"Audio download error: {e}")
        return None

async def download_video(link: str) -> str:
    global YOUR_API_URL
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            return None
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger = LOGGER("ShrutiMusic.platforms.Youtube")

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                data = await response.json()
                if response.status != 200:
                    return None

                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "video")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        return None
                
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    async with session.get(
                        stream_url,
                        timeout=aiohttp.ClientTimeout(total=600)
                    ) as file_response:
                        if file_response.status != 200:
                            return None
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                f.write(chunk)
                        return file_path
                else:
                    return None
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        logger.error(f"Video download error: {e}")
        return None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        video_id = None
        if "v=" in link:
            video_id = link.split("v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            video_id = link.split("youtu.be/")[1].split("?")[0]
        
        if video_id:
            cached_data = await get_complete_video_data(video_id)
            if cached_data:
                return (
                    cached_data["title"],
                    cached_data["duration_min"],
                    cached_data["duration_sec"],
                    cached_data["thumb"],
                    cached_data["vidid"]
                )
        
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                vidid = result["id"]
                duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
                
                video_data = {
                    "title": title,
                    "duration_min": duration_min,
                    "duration_sec": duration_sec,
                    "thumb": thumbnail,
                    "vidid": vidid,
                    "link": f"https://www.youtube.com/watch?v={vidid}",
                    "channel": result.get("channel", {}).get("name", ""),
                    "keywords": [],
                    "views": "0",
                    "source": "yt_search"
                }
                
                await save_complete_video_data(video_data)
                return title, duration_min, duration_sec, thumbnail, vidid
        except Exception as e:
            logger.warning(f"YT Search failed: {e}")
        
        if video_id:
            api_details = await get_video_details_api(video_id)
            if api_details:
                api_details["source"] = "yt_api"
                await save_complete_video_data(api_details)
                return (
                    api_details["title"],
                    api_details["duration_min"],
                    api_details["duration_sec"],
                    api_details["thumb"],
                    api_details["vidid"]
                )
        
        raise Exception("Failed to get video details")

    async def title(self, link: str, videoid: Union[bool, str] = None):
        details = await self.details(link, videoid)
        return details[0] if details else None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        details = await self.details(link, videoid)
        return details[1] if details else None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        details = await self.details(link, videoid)
        return details[3] if details else None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            playlist = await shell_cmd(
                f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
            )
            result = [key for key in playlist.split("\n") if key]
            return result
        except Exception as e:
            logger = LOGGER("ShrutiMusic.platforms.Youtube")
            logger.error(f"Playlist failed: {e}")
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        video_id = None
        if "v=" in link:
            video_id = link.split("v=")[1].split("&")[0]
        elif "youtu.be/" in link:
            video_id = link.split("youtu.be/")[1].split("?")[0]
        
        if video_id:
            cached_data = await get_complete_video_data(video_id)
            if cached_data:
                return cached_data, cached_data["vidid"]
        
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                track_details = {
                    "title": result["title"],
                    "link": result["link"],
                    "vidid": result["id"],
                    "duration_min": result["duration"],
                    "thumb": result["thumbnails"][0]["url"].split("?")[0],
                    "channel": result.get("channel", {}).get("name", ""),
                    "keywords": [],
                    "views": "0",
                    "source": "yt_search"
                }
                
                await save_complete_video_data(track_details)
                return track_details, track_details["vidid"]
        except Exception as e:
            logger.warning(f"YT Search failed: {e}")
        
        if not video_id and isinstance(link, str) and not link.startswith("http"):
            api_result = await search_youtube_api(link)
            if api_result:
                return api_result, api_result["vidid"]
        
        elif video_id:
            api_details = await get_video_details_api(video_id)
            if api_details:
                api_details["source"] = "yt_api"
                await save_complete_video_data(api_details)
                return api_details, video_id
        
        raise Exception("Failed to get track details")

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        return [], link

    async def slider(self, query: str, query_type: int, videoid: Union[bool, str] = None):
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        link = query
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            a = VideosSearch(link, limit=10)
            result = (await a.next()).get("result")
            if result and len(result) > query_type:
                title = result[query_type]["title"]
                duration_min = result[query_type]["duration"]
                vidid = result[query_type]["id"]
                thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
                return title, duration_min, thumbnail, vidid
        except Exception as e:
            logger.warning(f"Slider search failed: {e}")
        
        try:
            api_result = await search_youtube_api(query)
            if api_result:
                return api_result["title"], api_result["duration_min"], api_result["thumb"], api_result["vidid"]
        except:
            pass
        
        raise Exception("Failed to get slider results")

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        if videoid:
            link = self.base + link

        try:
            if songvideo or songaudio:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            elif video:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            else:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, False
