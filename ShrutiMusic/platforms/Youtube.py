import asyncio
import os
import re
import json
from typing import Union
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from ShrutiMusic.utils.database import is_on_off
from ShrutiMusic.utils.formatters import time_to_seconds
import os
import glob
import random
import logging
import aiohttp
from os import getenv
from ShrutiMusic import app, LOGGER
from urllib.parse import urlparse

# API Configuration
API_URL = getenv("API_URL", 'https://api.thequickearn.xyz')
VIDEO_API_URL = getenv("VIDEO_API_URL", 'https://api.video.thequickearn.xyz')
API_KEY = getenv("API_KEY", "30DxNexGenBots787531")
YOUR_API_URL = None

# Google Drive Configuration
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    import io
    from datetime import datetime
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False
 
CLIENT_SECRET_PATH = "ShrutiMusic/assets/client_secret.json"
TOKEN_PATH = "ShrutiMusic/assets/token.json"
DRIVE_CACHE_PATH = "ShrutiMusic/assets/drive_cache.json"
METADATA_DRIVE_FILENAME = "music_metadata.json"
DRIVE_FOLDER_ID = None
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Initialize logger
logger = LOGGER("ShrutiMusic/platforms/Youtube.py")

async def load_api_url():
    """Load API URL from external source"""
    global YOUR_API_URL
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa") as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info(f"✅ API URL loaded successfully: {YOUR_API_URL}")
                else:
                    logger.error(f"❌ Failed to fetch API URL. HTTP Status: {response.status}")
    except Exception as e:
        logger.error(f"❌ Error loading API URL: {e}")

# Load API URL on startup
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass

def cookie_txt_file():
    """Get random cookie file from cookies directory"""
    cookie_dir = f"{os.getcwd()}/cookies"
    if not os.path.exists(cookie_dir):
        return None
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        return None
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file

async def get_telegram_file(telegram_link: str, video_id: str, file_type: str) -> str:
    """
    Download file from Telegram link
    """
    try:
        extension = ".webm" if file_type == "audio" else ".mkv"
        file_path = os.path.join("downloads", f"{video_id}{extension}")
        
        # If file already exists locally
        if os.path.exists(file_path):
            logger.info(f"📂 [LOCAL] File exists: {video_id}")
            return file_path
        
        # Parse Telegram link: https://t.me/channelname/messageid
        parsed = urlparse(telegram_link)
        parts = parsed.path.strip("/").split("/")
        
        if len(parts) < 2:
            logger.error(f"❌ Invalid Telegram link format: {telegram_link}")
            return None
            
        channel_name = parts[0]
        message_id = int(parts[1])
        
        logger.info(f"📥 [TELEGRAM] Downloading from @{channel_name}/{message_id}")
        
        # Download using Pyrogram
        msg = await app.get_messages(channel_name, message_id)
        
        os.makedirs("downloads", exist_ok=True)
        await msg.download(file_name=file_path)
        
        # Wait for file to download completely
        timeout = 0
        while not os.path.exists(file_path) and timeout < 60:
            await asyncio.sleep(0.5)
            timeout += 0.5
        
        if os.path.exists(file_path):
            logger.info(f"✅ [TELEGRAM] Downloaded: {video_id}")
            return file_path
        else:
            logger.error(f"❌ [TELEGRAM] Timeout: {video_id}")
            return None
        
    except Exception as e:
        logger.error(f"❌ [TELEGRAM] Failed to download {video_id}: {e}")
        return None

# Google Drive Functions
def get_drive_service():
    if not DRIVE_AVAILABLE:
        return None
    
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            logger.error(f"Token load error: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Token refreshed successfully")
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                creds = None
        else:
            if not os.path.exists(CLIENT_SECRET_PATH):
                logger.error(f"client_secret.json not found at {CLIENT_SECRET_PATH}")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
                auth_url, _ = flow.authorization_url(prompt='consent')
                print("Authorize this URL in your browser and paste the code here:")
                print(auth_url)
                code = input("Enter authorization code: ").strip()
                flow.fetch_token(code=code)
                creds = flow.credentials
                logger.info("New authorization completed")
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                return None
        
        try:
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            logger.info(f"Token saved to {TOKEN_PATH}")
        except Exception as e:
            logger.error(f"Token save failed: {e}")
    
    try:
        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        logger.info("Drive service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"Drive service build failed: {e}")
        return None

def search_drive_by_video_id(video_id):
    """Direct search in Drive by video ID without using cache"""
    service = get_drive_service()
    if not service:
        return None
    
    try:
        # Search directly in Drive for files containing the video_id in name
        query = f"name contains '{video_id}' and trashed=false"
        if DRIVE_FOLDER_ID:
            query += f" and '{DRIVE_FOLDER_ID}' in parents"
        
        results = service.files().list(
            q=query,
            fields="files(id, name, size, mimeType)",
            pageSize=10
        ).execute()
        
        files = results.get('files', [])
        if not files:
            return None
        
        # Filter for exact matches and get the first one
        exact_matches = [f for f in files if f['name'].startswith(f"{video_id}.")]
        if exact_matches:
            return exact_matches[0]['id']
        
        return None
    except Exception as e:
        logger.error(f"Drive search error for {video_id}: {e}")
        return None

def cleanup_duplicate_files(video_id):
    """Clean up duplicate files in Drive for the same video ID"""
    service = get_drive_service()
    if not service:
        return False
    
    try:
        query = f"name contains '{video_id}' and trashed=false"
        if DRIVE_FOLDER_ID:
            query += f" and '{DRIVE_FOLDER_ID}' in parents"
        
        results = service.files().list(
            q=query,
            fields="files(id, name, createdTime)",
            pageSize=20
        ).execute()
        
        files = results.get('files', [])
        if len(files) <= 1:
            return True
        
        # Sort by creation time (oldest first)
        files.sort(key=lambda x: x.get('createdTime', ''))
        
        # Keep the first file, delete others
        kept_file = files[0]
        deleted_count = 0
        
        for file in files[1:]:
            try:
                service.files().delete(fileId=file['id']).execute()
                logger.info(f"Deleted duplicate file: {file['name']} ({file['id']})")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete duplicate {file['id']}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} duplicate files for {video_id}")
        return True
        
    except Exception as e:
        logger.error(f"Duplicate cleanup error for {video_id}: {e}")
        return False

def download_metadata_from_drive():
    """Download metadata file from Drive to local cache"""
    service = get_drive_service()
    if not service:
        logger.error("Drive service not available for metadata download")
        return False
    try:
        q = f"name='{METADATA_DRIVE_FILENAME}' and trashed=false"
        res = service.files().list(q=q, fields="files(id,name)").execute()
        files = res.get("files", [])
        if not files:
            logger.info("No metadata file found on Drive")
            return False
        
        file_id = files[0]["id"]
        request = service.files().get_media(fileId=file_id)
        
        os.makedirs(os.path.dirname(DRIVE_CACHE_PATH), exist_ok=True)
        with open(DRIVE_CACHE_PATH, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        
        logger.info(f"Downloaded metadata from Drive to {DRIVE_CACHE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Metadata download failed: {e}")
        return False

def upload_metadata_to_drive():
    """Upload local metadata file to Drive"""
    service = get_drive_service()
    if not service or not os.path.exists(DRIVE_CACHE_PATH):
        logger.error("Cannot upload metadata - service unavailable or file missing")
        return False
    try:
        q = f"name='{METADATA_DRIVE_FILENAME}' and trashed=false"
        res = service.files().list(q=q, fields="files(id,name)").execute()
        files = res.get("files", [])
        
        media = MediaFileUpload(DRIVE_CACHE_PATH, mimetype="application/json", resumable=True)
        
        if files:
            service.files().update(fileId=files[0]["id"], media_body=media).execute()
            logger.info("Updated metadata file on Drive")
        else:
            body = {"name": METADATA_DRIVE_FILENAME}
            if DRIVE_FOLDER_ID:
                body["parents"] = [DRIVE_FOLDER_ID]
            service.files().create(body=body, media_body=media).execute()
            logger.info("Created new metadata file on Drive")
        return True
    except Exception as e:
        logger.error(f"Metadata upload failed: {e}")
        return False

def load_drive_cache():
    """Load cache with proper error handling and Drive sync"""
    if not DRIVE_AVAILABLE:
        logger.info("Drive not available, using empty cache")
        return {}
    
    cache_data = {}
    
    if os.path.exists(DRIVE_CACHE_PATH):
        try:
            with open(DRIVE_CACHE_PATH, 'r') as f:
                cache_data = json.load(f)
                logger.info(f"Loaded local cache with {len(cache_data)} entries")
        except Exception as e:
            logger.error(f"Local cache load error: {e}")
            cache_data = {}
    
    if not cache_data:
        logger.info("Local cache empty/missing, attempting Drive download...")
        if download_metadata_from_drive():
            try:
                with open(DRIVE_CACHE_PATH, 'r') as f:
                    cache_data = json.load(f)
                    logger.info(f"Successfully loaded cache from Drive with {len(cache_data)} entries")
            except Exception as e:
                logger.error(f"Failed to load downloaded cache: {e}")
                cache_data = {}
        else:
            logger.info("Drive download failed, starting with empty cache")
    
    return cache_data

def save_drive_cache(cache_data):
    """Save cache with proper error handling"""
    if not DRIVE_AVAILABLE:
        logger.info("Drive not available, cache not saved")
        return False
        
    try:
        os.makedirs(os.path.dirname(DRIVE_CACHE_PATH), exist_ok=True)
        with open(DRIVE_CACHE_PATH, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Local cache saved with {len(cache_data)} entries")
        
        try:
            if upload_metadata_to_drive():
                logger.info("Cache successfully synced to Drive")
            else:
                logger.info("Drive sync failed but local save successful")
        except Exception as e:
            logger.error(f"Drive sync error (non-critical): {e}")
            
        return True
    except Exception as e:
        logger.error(f"Critical cache save error: {e}")
        return False

def upload_to_drive(file_path, video_id):
    """Upload file to Drive with size check and duplicate cleanup"""
    service = get_drive_service()
    if not service:
        logger.error("Drive service not available for upload")
        return None
        
    if not os.path.exists(file_path):
        logger.error(f"File not found for upload: {file_path}")
        return None
    
    # Check file size before upload (120MB limit)
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    if file_size_mb > 120:
        logger.error(f"File size {file_size_mb:.2f} MB exceeds 120MB limit. Skipping upload.")
        return None
        
    try:
        # Clean up any existing duplicates first
        cleanup_duplicate_files(video_id)
        
        file_metadata = {"name": f"{video_id}.mp3"}
        if DRIVE_FOLDER_ID:
            file_metadata["parents"] = [DRIVE_FOLDER_ID]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields="id"
        ).execute()
        drive_id = file.get("id")
        logger.info(f"Successfully uploaded to Drive: {video_id} -> {drive_id} ({file_size_mb:.2f} MB)")
        return drive_id
    except Exception as e:
        logger.error(f"Drive upload failed for {video_id}: {e}")
        return None

def download_from_drive(drive_file_id, dest_path):
    """Download file from Drive with better error handling"""
    service = get_drive_service()
    if not service:
        logger.error("Drive service not available for download")
        return False
        
    try:
        try:
            service.files().get(fileId=drive_file_id).execute()
        except Exception as e:
            logger.error(f"File not found on Drive: {drive_file_id} - {e}")
            return False
            
        request = service.files().get_media(fileId=drive_file_id)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
                
        logger.info(f"Successfully downloaded from Drive: {drive_file_id} -> {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Drive download failed for {drive_file_id}: {e}")
        return False

async def download_song(link: str):
    """Enhanced download function with priority: Local -> API2 -> Drive Metadata -> Drive Search -> API1"""
    video_id = None
    if 'v=' in link:
        video_id = link.split('v=')[-1].split('&')[0]
    elif 'youtu.be/' in link:
        video_id = link.split('youtu.be/')[-1].split('?')[0]
    
    if not video_id:
        logger.error(f"❌ Could not extract video_id from: {link}")
        return None
        
    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)
    
    logger.info(f"🎵 [AUDIO] Starting download process for: {video_id}")
    
    # STEP 1: Check Local Cache
    logger.info(f"🔍 [STEP 1] Checking local files for: {video_id}")
    for ext in ["mp3", "m4a", "webm", "mkv"]:
        file_path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(file_path):
            logger.info(f"✅ [LOCAL] Found local file: {file_path}")
            return file_path
    
    # STEP 2: Try API 2
    logger.info(f"🔍 [STEP 2] Trying API 2 for: {video_id}")
    api2_result = await download_song_api2(link, video_id)
    if api2_result:
        logger.info(f"✅ [API2] Successfully downloaded via API2: {video_id}")
        return api2_result
    
    # STEP 3: Check Drive Metadata Cache
    logger.info(f"🔍 [STEP 3] Checking Drive metadata cache for: {video_id}")
    if DRIVE_AVAILABLE:
        cache = load_drive_cache()
        if video_id in cache:
            drive_file_id = cache[video_id].get("drive_file_id")
            if drive_file_id:
                local_path = f"{download_folder}/{video_id}.mp3"
                logger.info(f"✅ [DRIVE_METADATA] Found in cache! Downloading {video_id}")
                if download_from_drive(drive_file_id, local_path):
                    logger.info(f"✅ [DRIVE_METADATA] Successfully retrieved from Drive: {local_path}")
                    return local_path
                else:
                    logger.warning(f"⚠️ [DRIVE_METADATA] Download failed, removing from cache")
                    try:
                        del cache[video_id]
                        save_drive_cache(cache)
                        cleanup_duplicate_files(video_id)
                    except Exception as e:
                        logger.error(f"❌ [DRIVE_METADATA] Cache cleanup error: {e}")
    
    # STEP 4: Direct Drive Search
    logger.info(f"🔍 [STEP 4] Performing direct Drive search for: {video_id}")
    if DRIVE_AVAILABLE:
        drive_file_id = search_drive_by_video_id(video_id)
        if drive_file_id:
            local_path = f"{download_folder}/{video_id}.mp3"
            logger.info(f"✅ [DRIVE_SEARCH] Found via direct search! Downloading {video_id}")
            if download_from_drive(drive_file_id, local_path):
                logger.info(f"✅ [DRIVE_SEARCH] Successfully retrieved from Drive: {local_path}")
                
                # Update cache with the found file
                try:
                    cache = load_drive_cache()
                    if video_id not in cache:
                        file_size = os.path.getsize(local_path)
                        cache[video_id] = {
                            "drive_file_id": drive_file_id,
                            "uploaded_at": datetime.now().isoformat(),
                            "format": "mp3",
                            "file_size": file_size,
                            "title": "Unknown",
                            "found_via_direct_search": True
                        }
                        save_drive_cache(cache)
                        logger.info(f"✅ [DRIVE_SEARCH] Updated cache with direct search result: {video_id}")
                except Exception as e:
                    logger.error(f"❌ [DRIVE_SEARCH] Cache update failed: {e}")
                
                return local_path
            else:
                logger.warning(f"⚠️ [DRIVE_SEARCH] Direct Drive download failed")
                cleanup_duplicate_files(video_id)
        else:
            logger.info(f"❌ [DRIVE_SEARCH] Video_id {video_id} not found via direct Drive search")
    
    # STEP 5: Try API 1 (Fallback)
    logger.info(f"🔍 [STEP 5] Trying API 1 (Fallback) for: {video_id}")
    api1_result = await download_song_api1(link, video_id)
    if api1_result:
        logger.info(f"✅ [API1] Successfully downloaded via API1: {video_id}")
        return api1_result
    
    # Final fallback: yt-dlp
    logger.info(f"🔍 [FINAL] Trying yt-dlp fallback for: {video_id}")
    ytdlp_result = await download_song_ytdlp(link, video_id)
    if ytdlp_result:
        logger.info(f"✅ [YTDLP] Successfully downloaded via yt-dlp: {video_id}")
        return ytdlp_result
    
    logger.error(f"❌ [ALL_METHODS] All download methods failed for: {video_id}")
    return None

async def download_song_api2(link: str, video_id: str) -> str:
    """Download song using API 2"""
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            logger.error("❌ [API2] API URL not available")
            return None

    logger.info(f"🎵 [API2] Starting download for: {video_id}")

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

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
                    logger.error(f"❌ [API2] API error: {response.status}")
                    return None

                # Format 1: Direct Telegram link (already uploaded)
                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    logger.info(f"🔗 [API2] Telegram link received: {telegram_link}")
                    
                    # Download from Telegram
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "audio")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        logger.warning(f"⚠️ [API2] Telegram download failed")
                        return None
                
                # Format 2: Stream URL (not yet uploaded)
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    logger.info(f"🔗 [API2] Stream URL obtained: {video_id}")
                    
                    # Download from stream URL
                    async with session.get(
                        stream_url,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as file_response:
                        if file_response.status != 200:
                            logger.error(f"❌ [API2] Download failed: {file_response.status}")
                            return None
                            
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                f.write(chunk)
                        
                        logger.info(f"✅ [API2] Downloaded: {video_id}")
                        return file_path
                else:
                    logger.error(f"❌ [API2] Invalid response: {data}")
                    return None

    except asyncio.TimeoutError:
        logger.error(f"❌ [API2] Timeout: {video_id}")
        return None
    except Exception as e:
        logger.error(f"❌ [API2] Exception: {video_id} - {e}")
        return None

async def download_song_api1(link: str, video_id: str) -> str:
    """Download song using API 1"""
    logger.info(f"🎵 [API1] Starting API1 download for: {video_id}")
    
    api_success = False
    song_url = f"{API_URL}/song/{video_id}?api={API_KEY}"
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(5):
            try:
                async with session.get(song_url) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status code {response.status}")
                
                    data = await response.json()
                    status = data.get("status", "").lower()

                    if status == "done":
                        download_url = data.get("link")
                        if not download_url:
                            raise Exception("API response did not provide a download URL.")
                        logger.info(f"✅ [API1] API ready for download: {video_id}")
                        api_success = True
                        break
                    elif status == "downloading":
                        logger.info(f"⏳ [API1] API processing... attempt {attempt + 1}")
                        await asyncio.sleep(4)
                    else:
                        error_msg = data.get("error") or data.get("message") or f"Unexpected status '{status}'"
                        raise Exception(f"API error: {error_msg}")
            except Exception as e:
                logger.error(f"❌ [API1] Attempt {attempt + 1} failed: {e}")
                if attempt == 4:
                    logger.error("❌ [API1] API completely failed after 5 attempts")
                    break
                await asyncio.sleep(2)

        if api_success:
            try:
                file_format = data.get("format", "mp3")
                file_extension = file_format.lower()
                file_name = f"{video_id}.{file_extension}"
                download_folder = "downloads"
                file_path = os.path.join(download_folder, file_name)

                logger.info(f"⬇️ [API1] Downloading from API: {file_name}")
                async with session.get(download_url) as file_response:
                    with open(file_path, 'wb') as f:
                        total_size = 0
                        while True:
                            chunk = await file_response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            total_size += len(chunk)
                    
                    logger.info(f"✅ [API1] API download completed: {file_name} ({total_size} bytes)")
                    
                    # Upload to Drive if successful and not too large
                    if DRIVE_AVAILABLE and total_size > 0:
                        try:
                            cache = load_drive_cache()
                            if video_id not in cache:
                                file_size_mb = total_size / (1024 * 1024)
                                if file_size_mb <= 120:
                                    logger.info(f"☁️ [API1] Uploading to Drive: {video_id} ({file_size_mb:.2f} MB)")
                                    drive_file_id = upload_to_drive(file_path, video_id)
                                    if drive_file_id:
                                        cache[video_id] = {
                                            "drive_file_id": drive_file_id,
                                            "uploaded_at": datetime.now().isoformat(),
                                            "format": file_extension,
                                            "file_size": total_size,
                                            "title": "Unknown"
                                        }
                                        save_drive_cache(cache)
                                        logger.info(f"✅ [API1] Successfully cached to Drive: {video_id}")
                                else:
                                    logger.warning(f"⚠️ [API1] Skipping Drive upload - file size {file_size_mb:.2f} MB exceeds 120MB limit")
                        except Exception as e:
                            logger.error(f"❌ [API1] Drive caching failed: {e}")
                    
                    return file_path
                    
            except Exception as e:
                logger.error(f"❌ [API1] File download failed: {e}")
    
    return None

async def download_song_ytdlp(link: str, video_id: str) -> str:
    """Download song using yt-dlp fallback"""
    logger.info(f"🎵 [YTDLP] Trying yt-dlp fallback for: {video_id}")
    
    cookie_file = cookie_txt_file()
    if not cookie_file:
        logger.error("❌ [YTDLP] No cookies available for fallback download")
        return None
        
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"downloads/{video_id}.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "cookiefile": cookie_file,
            "no_warnings": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            expected_path = f"downloads/{video_id}.{info.get('ext', 'mp3')}"
            
            if os.path.exists(expected_path):
                logger.info(f"✅ [YTDLP] File already exists: {expected_path}")
                return expected_path
                
            ydl.download([link])
            
            if os.path.exists(expected_path):
                logger.info(f"✅ [YTDLP] Download successful: {expected_path}")
                
                # Upload to Drive with size check
                if DRIVE_AVAILABLE:
                    try:
                        cache = load_drive_cache()
                        if video_id not in cache:
                            file_size = os.path.getsize(expected_path)
                            file_size_mb = file_size / (1024 * 1024)
                            
                            if file_size_mb <= 120:
                                drive_file_id = upload_to_drive(expected_path, video_id)
                                if drive_file_id:
                                    cache[video_id] = {
                                        "drive_file_id": drive_file_id,
                                        "uploaded_at": datetime.now().isoformat(),
                                        "format": info.get('ext', 'mp3'),
                                        "file_size": file_size,
                                        "title": info.get('title', 'Unknown')
                                    }
                                    save_drive_cache(cache)
                                    logger.info(f"✅ [YTDLP] Successfully cached to Drive: {video_id}")
                            else:
                                logger.warning(f"⚠️ [YTDLP] Skipping Drive upload - file size {file_size_mb:.2f} MB exceeds 120MB limit")
                    except Exception as e:
                        logger.error(f"❌ [YTDLP] Drive upload failed: {e}")
                
                return expected_path
            else:
                logger.error("❌ [YTDLP] Download failed - file not created")
                return None
                
    except Exception as e:
        logger.error(f"❌ [YTDLP] Fallback failed: {e}")
        return None

async def download_video(link: str):
    """Download video with similar priority logic"""
    video_id = link.split('v=')[-1].split('&')[0]

    download_folder = "downloads"
    
    # STEP 1: Check Local Files
    for ext in ["mp4", "webm", "mkv"]:
        file_path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(file_path):
            logger.info(f"✅ [VIDEO_LOCAL] Found local file: {file_path}")
            return file_path
    
    # STEP 2: Try Video API
    if VIDEO_API_URL:
        logger.info(f"🎥 [VIDEO_API] Trying video API for: {video_id}")
        video_url = f"{VIDEO_API_URL}/video/{video_id}?api={API_KEY}"
        async with aiohttp.ClientSession() as session:
            for attempt in range(10):
                try:
                    async with session.get(video_url) as response:
                        if response.status != 200:
                            raise Exception(f"API request failed with status code {response.status}")
                    
                        data = await response.json()
                        status = data.get("status", "").lower()

                        if status == "done":
                            download_url = data.get("link")
                            if not download_url:
                                raise Exception("API response did not provide a download URL.")
                            break
                        elif status == "downloading":
                            await asyncio.sleep(8)
                        else:
                            error_msg = data.get("error") or data.get("message") or f"Unexpected status '{status}'"
                            raise Exception(f"API error: {error_msg}")
                except Exception as e:
                    logger.error(f"❌ [VIDEO_API] Attempt {attempt + 1} failed: {e}")
                    if attempt == 9:
                        logger.error("❌ [VIDEO_API] Max retries reached")
                        return None
            else:
                logger.error("❌ [VIDEO_API] Max retries reached")
                return None

            try:
                file_format = data.get("format", "mp4")
                file_extension = file_format.lower()
                file_name = f"{video_id}.{file_extension}"
                download_folder = "downloads"
                os.makedirs(download_folder, exist_ok=True)
                file_path = os.path.join(download_folder, file_name)

                async with session.get(download_url) as file_response:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await file_response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                    logger.info(f"✅ [VIDEO_API] Downloaded: {file_path}")
                    return file_path
            except aiohttp.ClientError as e:
                logger.error(f"❌ [VIDEO_API] Network error: {e}")
                return None
            except Exception as e:
                logger.error(f"❌ [VIDEO_API] Download error: {e}")
                return None
    
    logger.error(f"❌ [VIDEO] All video download methods failed for: {video_id}")
    return None

# Other utility functions remain the same as in your original code
async def check_file_size(link):
    async def get_format_info(link):
        cookie_file = cookie_txt_file()
        if not cookie_file:
            logger.error("No cookies found. Cannot check file size.")
            return None
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        logger.error("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

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
        
        if DRIVE_AVAILABLE:
            logger.info("Initializing Drive integration...")
            service = get_drive_service()
            if service:
                logger.info("Drive integration ready")
                cache = load_drive_cache()
                logger.info(f"Initial cache loaded with {len(cache)} entries")
            else:
                logger.warning("Drive integration failed - continuing with local only")
        else:
            logger.info("Drive dependencies not available - using local cache only")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
        except Exception as e:
            logger.error(f"Video API failed: {e}")
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return 0, "No cookies found. Cannot download video."
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file,
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return []
            
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file} --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return [], link
            
        ytdl_opts = {"quiet": True, "cookiefile" : cookie_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

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
        loop = asyncio.get_running_loop()
        
        def audio_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download audio.")
                
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile" : cookie_file,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download video.")
                
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile" : cookie_file,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download song video.")
                
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile" : cookie_file,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download song audio.")
                
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile" : cookie_file,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            result = await download_song(link)
            return result, True
        elif songaudio:
            result = await download_song(link)
            return result, True
        elif video:
            try:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    direct = True
                    return downloaded_file, direct
            except Exception as e:
                logger.error(f"Video API failed: {e}")
            
            cookie_file = cookie_txt_file()
            if not cookie_file:
                logger.error("No cookies found. Cannot download video.")
                return None, None
                
            if await is_on_off(1):
                direct = True
                downloaded_file = await download_song(link)
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "--cookies", cookie_file,
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = False
                else:
                   file_size = await check_file_size(link)
                   if not file_size:
                     logger.error("None file Size")
                     return None, None
                   total_size_mb = file_size / (1024 * 1024)
                   if total_size_mb > 250:
                     logger.error(f"File size {total_size_mb:.2f} MB exceeds the 100MB limit.")
                     return None, None
                   direct = True
                   downloaded_file = await loop.run_in_executor(None, video_dl)
        else:
            direct = True
            downloaded_file = await download_song(link)
        return downloaded_file, direct

def get_cache_stats():
    """Get cache statistics for debugging"""
    if not DRIVE_AVAILABLE:
        return {"status": "Drive not available"}
    
    try:
        cache = load_drive_cache()
        total_entries = len(cache)
        total_size = 0
        formats = {}
        
        for entry in cache.values():
            size = entry.get("file_size", 0)
            format_type = entry.get("format", "unknown")
            total_size += size
            formats[format_type] = formats.get(format_type, 0) + 1
        
        return {
            "status": "Available",
            "total_entries": total_entries,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "formats": formats,
            "cache_file_exists": os.path.exists(DRIVE_CACHE_PATH)
        }
    except Exception as e:
        return {"status": f"Error: {e}"}

async def cleanup_cache():
    """Clean up invalid cache entries and duplicates"""
    if not DRIVE_AVAILABLE:
        logger.info("Drive not available for cleanup")
        return False
        
    try:
        cache = load_drive_cache()
        if not cache:
            logger.info("No cache to cleanup")
            return True
            
        service = get_drive_service()
        if not service:
            logger.error("Drive service not available for cleanup")
            return False
            
        cleaned_count = 0
        # Clean invalid cache entries
        for video_id, entry in list(cache.items()):
            drive_file_id = entry.get("drive_file_id")
            if not drive_file_id:
                continue
                
            try:
                service.files().get(fileId=drive_file_id).execute()
            except Exception:
                logger.info(f"Removing invalid cache entry: {video_id}")
                del cache[video_id]
                cleaned_count += 1
        
        # Clean duplicate files in Drive
        duplicate_cleaned = 0
        for video_id in cache:
            if cleanup_duplicate_files(video_id):
                duplicate_cleaned += 1
        
        if cleaned_count > 0 or duplicate_cleaned > 0:
            save_drive_cache(cache)
            logger.info(f"Cleaned {cleaned_count} invalid cache entries and {duplicate_cleaned} duplicate files")
        else:
            logger.info("No invalid entries or duplicates found")
            
        return True
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return False
