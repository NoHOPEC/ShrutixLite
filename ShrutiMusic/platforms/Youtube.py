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
YOUTUBE_API_KEY = "AIzaSyCIWrKdlCOrK-ze82jp5ictpWXnHoDZvKk"
YOUTUBE_API_LIMIT_PER_DAY = 100

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.ShrutixMusic
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
                    logger.info("Download API loaded")
    except Exception as e:
        logger.error(f"Download API load error: {e}")

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
    except:
        pass

async def save_api_data_to_mongo(query: str, video_data: dict):
    try:
        video_id = video_data.get("vidid")
        if not video_id:
            return
        
        duration_sec = video_data.get("duration_sec", 0)
        if not duration_sec and video_data.get("duration_min"):
            try:
                duration_sec = int(time_to_seconds(video_data["duration_min"]))
            except:
                duration_sec = 0
        
        complete_data = {
            "video_id": video_id,
            "query": query.lower().strip() if query else "",
            "title": video_data.get("title", ""),
            "url": video_data.get("link", f"https://www.youtube.com/watch?v={video_id}"),
            "thumbnail": video_data.get("thumb", ""),
            "duration_min": video_data.get("duration_min", ""),
            "duration_sec": duration_sec,
            "channel": video_data.get("channel", ""),
            "views": video_data.get("views", "0"),
            "publish_date": video_data.get("publish_date", ""),
            "keywords": video_data.get("keywords", []),
            "description": video_data.get("description", ""),
            "cached_at": datetime.utcnow().isoformat(),
            "source": "api"
        }
        
        await cache_collection.update_one(
            {"video_id": video_id},
            {"$set": complete_data},
            upsert=True
        )
        
        if query and query.strip() and query.lower() != video_id:
            await cache_collection.update_one(
                {"query": query.lower().strip()},
                {"$set": complete_data},
                upsert=True
            )
        
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        logger.info(f"[API DATA SAVED] {video_id} | Query: {query[:30]}")
        
    except Exception as e:
        logger = LOGGER("ShrutiMusic.platforms.Youtube")
        logger.error(f"[MONGO SAVE ERROR] {e}")

async def get_from_mongo(identifier: str):
    try:
        if not identifier:
            return None
        
        identifier_lower = identifier.lower().strip()
        
        cached = await cache_collection.find_one({"video_id": identifier_lower})
        
        if not cached:
            cached = await cache_collection.find_one({"query": identifier_lower})
        
        if cached:
            cache_time = cached.get("cached_at")
            if cache_time:
                try:
                    cache_datetime = datetime.fromisoformat(cache_time)
                    if datetime.utcnow() - cache_datetime < timedelta(days=30):
                        logger = LOGGER("ShrutiMusic.platforms.Youtube")
                        
                        if cached.get("video_id") == identifier_lower:
                            logger.info(f"[MONGO HIT - VIDEO_ID] {identifier_lower}")
                        else:
                            logger.info(f"[MONGO HIT - QUERY] {identifier_lower}")
                        
                        duration_sec = cached.get("duration_sec", 0)
                        if not duration_sec and cached.get("duration_min"):
                            try:
                                duration_sec = int(time_to_seconds(cached["duration_min"]))
                            except:
                                duration_sec = 0
                        
                        video_id = cached.get("video_id", "")
                        return {
                            "title": cached.get("title", ""),
                            "link": cached.get("url", f"https://www.youtube.com/watch?v={video_id}"),
                            "vidid": video_id,
                            "duration_min": cached.get("duration_min", ""),
                            "duration_sec": duration_sec,
                            "thumb": cached.get("thumbnail", ""),
                            "channel": cached.get("channel", ""),
                            "views": cached.get("views", "0"),
                            "publish_date": cached.get("publish_date", ""),
                            "keywords": cached.get("keywords", []),
                            "description": cached.get("description", "")
                        }
                except:
                    pass
        return None
    except:
        return None

async def search_youtube_api(query: str):
    logger = LOGGER("ShrutiMusic.platforms.Youtube")
    
    try:
        if not await check_api_limit():
            logger.warning("[YT API] Daily limit reached")
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
                            await increment_api_usage()
                            await save_api_data_to_mongo(query, details)
                            logger.info(f"[YT API SUCCESS] {query[:40]} -> {video_id}")
                            return details
                elif response.status == 403:
                    today = datetime.utcnow().date()
                    await api_usage_collection.update_one(
                        {"date": str(today)},
                        {"$set": {"count": YOUTUBE_API_LIMIT_PER_DAY}},
                        upsert=True
                    )
                    logger.warning("[YT API] Quota exceeded")
                    return None
    except Exception as e:
        logger.error(f"[YT API] Search error: {e}")
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
                            thumbnails.get("default", {}).get("url") or
                            ""
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
        logger.error(f"[YT API] Details error: {e}")
        return None

def parse_iso_duration(duration: str) -> int:
    try:
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    except:
        return 0

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
    except:
        return None

async def download_video(link: str) -> str:
    global YOUR_API_URL
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            return None
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

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
    except:
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
        
        try:
            results = VideosSearch(link, limit=1)
            result_data = await results.next()
            if result_data and result_data.get("result"):
                for result in result_data["result"]:
                    title = result.get("title") or ""
                    duration_min = result.get("duration") or ""
                    vidid = result.get("id") or ""
                    
                    if not title or not vidid:
                        continue
                    
                    thumbnails = result.get("thumbnails") or []
                    thumbnail = ""
                    if thumbnails and len(thumbnails) > 0:
                        thumb_url = thumbnails[0].get("url") or ""
                        if thumb_url and "?" in thumb_url:
                            thumbnail = thumb_url.split("?")[0]
                        else:
                            thumbnail = thumb_url
                    
                    duration_sec = 0
                    if duration_min:
                        try:
                            duration_sec = int(time_to_seconds(duration_min))
                        except:
                            duration_sec = 0
                    
                    channel_info = result.get("channel") or {}
                    channel_name = ""
                    if channel_info and isinstance(channel_info, dict):
                        channel_name = channel_info.get("name") or ""
                    
                    logger.info(f"[YT SEARCH SUCCESS] {vidid}")
                    return title, duration_min or "0:00", duration_sec, thumbnail, vidid
        except Exception as e:
            logger.warning(f"[YT SEARCH FAILED] {e}")
        
        mongo_data = await get_from_mongo(video_id if video_id else link)
        if mongo_data:
            logger.info(f"[MONGO HIT] {link[:40]}")
            return (
                mongo_data["title"],
                mongo_data["duration_min"],
                mongo_data["duration_sec"],
                mongo_data["thumb"],
                mongo_data["vidid"]
            )
        
        if video_id:
            logger.info(f"[YT API] Video ID: {video_id}")
            api_details = await get_video_details_api(video_id)
            if api_details:
                await save_api_data_to_mongo(video_id, api_details)
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
        except:
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
        
        logger.info(f"[CHECKING MONGO] {link}")
        
        if video_id:
            mongo_data = await get_from_mongo(video_id)
            if mongo_data:
                logger.info(f"[MONGO HIT - VIDEO_ID] {video_id}")
                return mongo_data, mongo_data["vidid"]
        
        mongo_data = await get_from_mongo(link.lower().strip())
        if mongo_data:
            logger.info(f"[MONGO HIT - QUERY] {link} -> {mongo_data['vidid']}")
            return mongo_data, mongo_data["vidid"]
        
        logger.info(f"[MONGO MISS] Not found in database")
        
        try:
            logger.info(f"[YT SEARCH] {link}")
            results = VideosSearch(link, limit=1)
            result_data = await results.next()
            if result_data and result_data.get("result"):
                for result in result_data["result"]:
                    title = result.get("title") or ""
                    vidid = result.get("id") or ""
                    link_url = result.get("link") or ""
                    duration_min = result.get("duration") or ""
                    
                    thumbnails = result.get("thumbnails") or []
                    thumbnail = ""
                    if thumbnails and len(thumbnails) > 0:
                        thumb_url = thumbnails[0].get("url") or ""
                        if thumb_url and "?" in thumb_url:
                            thumbnail = thumb_url.split("?")[0]
                        else:
                            thumbnail = thumb_url
                    
                    channel_info = result.get("channel") or {}
                    channel_name = ""
                    if channel_info and isinstance(channel_info, dict):
                        channel_name = channel_info.get("name") or ""
                    
                    duration_sec = 0
                    if duration_min:
                        try:
                            duration_sec = int(time_to_seconds(duration_min))
                        except:
                            duration_sec = 0
                    
                    if title and vidid:
                        track_details = {
                            "title": title,
                            "link": link_url if link_url else f"https://www.youtube.com/watch?v={vidid}",
                            "vidid": vidid,
                            "duration_min": duration_min or "0:00",
                            "duration_sec": duration_sec,
                            "thumb": thumbnail,
                            "channel": channel_name,
                            "keywords": [],
                            "views": "0"
                        }
                        
                        logger.info(f"[YT SEARCH SUCCESS] {link} -> {vidid}")
                        return track_details, vidid
        except Exception as e:
            logger.warning(f"[YT SEARCH FAILED] {str(e)}")
        
        logger.info(f"[YT API] {link}")
        api_result = await search_youtube_api(link)
        if api_result:
            return api_result, api_result["vidid"]
        
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
            result_data = await a.next()
            result = result_data.get("result") or []
            if result and len(result) > query_type:
                title = result[query_type].get("title") or ""
                duration_min = result[query_type].get("duration") or ""
                vidid = result[query_type].get("id") or ""
                
                thumbnails = result[query_type].get("thumbnails") or []
                thumbnail = ""
                if thumbnails and len(thumbnails) > 0:
                    thumb_url = thumbnails[0].get("url") or ""
                    if thumb_url and "?" in thumb_url:
                        thumbnail = thumb_url.split("?")[0]
                    else:
                        thumbnail = thumb_url
                
                if title and vidid:
                    logger.info(f"[YT SEARCH] Slider {vidid}")
                    return title, duration_min or "0:00", thumbnail, vidid
        except Exception as e:
            logger.warning(f"[YT SEARCH] Slider failed: {str(e)}")
        
        mongo_data = await get_from_mongo(query)
        if mongo_data:
            logger.info(f"[MONGO] Slider {query[:40]}")
            return mongo_data["title"], mongo_data["duration_min"], mongo_data["thumb"], mongo_data["vidid"]
        
        try:
            logger.info(f"[YT API] Slider query: {query[:40]}")
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
            logger = LOGGER("ShrutiMusic.platforms.Youtube")
            logger.error(f"Download error: {e}")
            return None, False
