from pyrogram import Client, filters, enums
from ShrutiMusic import app
import shutil
from typing import List
import asyncio
import re
import config
import random
import requests
from motor.motor_asyncio import AsyncIOMotorClient as MongoCli
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, VideoChatScheduled
from pyrogram.errors import ChatAdminRequired, UserIsBlocked, ChatWriteForbidden, FloodWait, RPCError
from pyrogram.types import ChatMemberUpdated

mongodb = MongoCli(config.MONGO_DB_URI)
db = mongodb.Anonymous

CHAT_STORAGE = [
    "mongodb+srv://chatbot1:a@cluster0.pxbu0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot2:b@cluster0.9i8as.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot3:c@cluster0.0ak9k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot4:d@cluster0.4i428.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot5:e@cluster0.pmaap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot6:f@cluster0.u63li.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot7:g@cluster0.mhzef.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot8:h@cluster0.okxao.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot9:i@cluster0.yausb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "mongodb+srv://chatbot10:j@cluster0.9esnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
]

VIPBOY = MongoCli(random.choice(CHAT_STORAGE))
chatdb = VIPBOY.Anonymous
chatai = chatdb.Word.WordDb
storeai = VIPBOY.Anonymous.Word.NewWordDb  

sticker_db = db.stickers.sticker
chatbot_settings = db.chatbot_settings

reply = []
sticker = []
LOAD = "FALSE"
BLACKLIST_WORDS = set()

# Blacklist URL
BLACKLIST_URL = "https://gist.githubusercontent.com/YaduvanshiNand/184d00e0d2ff75afdc178e8139282657/raw/77c35a15a37635adc2b6db1bb85a9ed8ded929e1/shrutibots_blacklist.txt"

async def load_blacklist():
    """Load blacklist words from gist"""
    global BLACKLIST_WORDS
    try:
        print("⏳ Loading blacklist words from gist...")
        response = requests.get(BLACKLIST_URL, timeout=10)
        if response.status_code == 200:
            words = response.text.strip().split('\n')
            BLACKLIST_WORDS = set(word.strip().lower() for word in words if word.strip())
            print(f"✅ Loaded {len(BLACKLIST_WORDS)} blacklist words")
        else:
            print(f"❌ Failed to load blacklist: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error loading blacklist: {e}")

async def load_caches():
    global reply, sticker, LOAD
    if LOAD == "TRUE":
        return
    LOAD = "TRUE"
    reply.clear()
    sticker.clear()
    
    print("🧹 All cache cleaned successfully")
    await asyncio.sleep(1)
    try:
        print("⏳ Loading All Caches...")
        
        # Load blacklist first
        await load_blacklist()
        
        reply = await chatai.find().to_list(length=10000)
        print("✅ Replies Loaded Successfully")
        await asyncio.sleep(1)
        
        sticker = await sticker_db.find().to_list(length=None)
        if not sticker:
            sticker_id = "CAACAgUAAxkBAAENzH5nsI3qB-eJNDAUZQL9v3SQl_m-DAACigYAAuT1GFUScU-uCJCWAjYE"
            await sticker_db.insert_one({"sticker_id": sticker_id})
        print("✅ Stickers Loaded Successfully")
        print("🎉 All caches loaded successfully!")
        LOAD = "FALSE"
    except Exception as e:
        print(f"❌ Error loading caches: {e}")
        LOAD = "FALSE"
    return

async def is_chat_enabled(chat_id: int) -> bool:
    chat = await chatbot_settings.find_one({"chat_id": chat_id})
    return chat and chat.get("enabled", False)

async def set_chat_status(chat_id: int, status: bool):
    await chatbot_settings.update_one({"chat_id": chat_id}, {"$set": {"enabled": status}}, upsert=True)

def contains_blacklist_word(text: str) -> bool:
    """Check if text contains any blacklist word"""
    if not text or not BLACKLIST_WORDS:
        return False
    text_lower = text.lower()
    # Check for whole words and partial matches
    return any(word in text_lower for word in BLACKLIST_WORDS)

async def is_adult_sticker(sticker_id: str) -> bool:
    """Basic check for adult stickers"""
    adult_sticker_ids = []
    return sticker_id in adult_sticker_ids

@app.on_message(filters.command("chatbot") & filters.group)
async def toggle_chatbot(client: Client, message: Message):
    user = message.from_user
    chat_id = message.chat.id

    # Only admins/owners can use this command
    chat_member = await client.get_chat_member(chat_id, user.id)
    if chat_member.status not in [CMS.OWNER, CMS.ADMINISTRATOR]:
        return await message.reply_text("<b>❌ Only Admin/Owner can use this command!</b>", parse_mode=enums.ParseMode.HTML)

    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 Enable", callback_data=f"chatbot_on_{chat_id}"),
            InlineKeyboardButton("🔴 Disable", callback_data=f"chatbot_off_{chat_id}")
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data=f"chatbot_status_{chat_id}")
        ]
    ])

    await message.reply_text(
        "<b>🤖 Chatbot Control Panel</b>\n\n"
        "<b>Choose an option:</b>",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"chatbot_"))
async def chatbot_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    chat_id = int(data.split("_")[-1])
    action = data.split("_")[1]

    # Check if user is admin
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        if chat_member.status not in [CMS.OWNER, CMS.ADMINISTRATOR]:
            return await callback_query.answer("❌ Only admins can control chatbot!", show_alert=True)
    except:
        return await callback_query.answer("❌ Error checking permissions!", show_alert=True)

    if action == "on":
        await set_chat_status(chat_id, True)
        await callback_query.edit_message_text(
            "<b>✅ Chatbot Enabled Successfully!</b>\n\n"
            "<b>🎉 Now I will reply to messages in this group.</b>",
            parse_mode=enums.ParseMode.HTML
        )
    
    elif action == "off":
        await set_chat_status(chat_id, False)
        await callback_query.edit_message_text(
            "<b>🚫 Chatbot Disabled Successfully!</b>\n\n"
            "<b>😴 I will not reply to messages in this group now.</b>",
            parse_mode=enums.ParseMode.HTML
        )
    
    elif action == "status":
        enabled = await is_chat_enabled(chat_id)
        status_text = "<b>🟢 ENABLED</b>" if enabled else "<b>🔴 DISABLED</b>"
        await callback_query.edit_message_text(
            f"<b>🤖 Chatbot Status</b>\n\n"
            f"<b>Current Status:</b> {status_text}\n\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>",
            parse_mode=enums.ParseMode.HTML
        )

async def get_reply(message_text: str):
    global reply
    matched_replies = [reply_data for reply_data in reply if reply_data["word"] == message_text]

    if matched_replies:
         return random.choice(matched_replies)
        
    return random.choice(reply) if reply else None

async def save_reply(original_message: Message, reply_message: Message):
    global reply
    try:
        # Check for blacklist words in original message before saving
        if original_message.text and contains_blacklist_word(original_message.text):
            return  # Don't save blacklisted content

        reply_data = {
            "word": original_message.text,
            "text": None,
            "check": "none",
        }

        if reply_message.sticker:
            if await is_adult_sticker(reply_message.sticker.file_id):
                return
            reply_data["text"] = reply_message.sticker.file_id
            reply_data["check"] = "sticker"
        elif reply_message.photo:
            reply_data["text"] = reply_message.photo.file_id
            reply_data["check"] = "photo"
        elif reply_message.video:
            reply_data["text"] = reply_message.video.file_id
            reply_data["check"] = "video"
        elif reply_message.audio:
            reply_data["text"] = reply_message.audio.file_id
            reply_data["check"] = "audio"
        elif reply_message.animation:
            reply_data["text"] = reply_message.animation.file_id
            reply_data["check"] = "gif"
        elif reply_message.voice:
            reply_data["text"] = reply_message.voice.file_id
            reply_data["check"] = "voice"
        elif reply_message.text:
            # Check for blacklist words in reply text
            if contains_blacklist_word(reply_message.text):
                return  # Don't save blacklisted content
            reply_data["text"] = reply_message.text
            reply_data["check"] = "none"

        # Save stickers to sticker database
        if reply_message.sticker:
            sticker_data = {"sticker_id": reply_message.sticker.file_id}
            existing_sticker = await sticker_db.find_one(sticker_data)
            if not existing_sticker:
                await sticker_db.insert_one(sticker_data)
                sticker.append(sticker_data)

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            reply.append(reply_data)

    except Exception as e:
        print(f"❌ Error in save_reply: {e}")
          
async def reply_message(client, chat_id, bot_id, message_text, message):
    try:
        reply_data = await get_reply(message_text)
        if reply_data:
            response_text = reply_data["text"]
            
            # Check if bot's reply contains blacklist words
            if reply_data["check"] == "none" and contains_blacklist_word(response_text):
                # Find a clean reply instead
                clean_replies = [r for r in reply if r["check"] == "none" and not contains_blacklist_word(r.get("text", ""))]
                if clean_replies:
                    reply_data = random.choice(clean_replies)
                    response_text = reply_data["text"]
                else:
                    return  # No clean reply available
            
            if reply_data["check"] == "sticker":
                await message.reply_sticker(reply_data["text"])
            elif reply_data["check"] == "photo":
                await message.reply_photo(reply_data["text"])
            elif reply_data["check"] == "video":
                await message.reply_video(reply_data["text"])
            elif reply_data["check"] == "audio":
                await message.reply_audio(reply_data["text"])
            elif reply_data["check"] == "gif":
                await message.reply_animation(reply_data["text"])
            elif reply_data["check"] == "voice":
                await message.reply_voice(reply_data["text"])
            else:
                await message.reply_text(response_text, disable_web_page_preview=True)

    except (ChatAdminRequired, UserIsBlocked, ChatWriteForbidden, RPCError) as e:
        return
    except Exception as e:
        print(f"❌ Error in reply_message: {e}")
        return

@app.on_message(filters.incoming, group=1)
async def chatbot(client: Client, message: Message):
    global sticker
    bot_id = client.me.id
    
    # Return if chatbot is disabled in group, but always work in DM
    if message.chat.type != enums.ChatType.PRIVATE and not await is_chat_enabled(message.chat.id):
        return

    if not sticker:
        await load_caches()
        return
    
    if not message.from_user or message.from_user.is_bot:
        return
    
    chat_id = message.chat.id
    
    try:
        # Ignore commands
        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", "@", ".", "?", "#"]):
            return
          
        if (message.reply_to_message and message.reply_to_message.from_user.id == client.me.id) or (not message.reply_to_message):
            
            if message.text and message.from_user:
                message_text = message.text.lower()
                
                # Check for blacklist words - don't reply if found
                if contains_blacklist_word(message_text):
                    return  # Silently ignore blacklisted messages
                
                # Predefined responses
                if "gn" in message_text or "good night" in message_text:
                    return await message.reply_text(f"🌙 Good Night! Sweet dreams {message.from_user.mention} ✨")
    
                elif "gm" in message_text or "good morning" in message_text:
                    return await message.reply_text(f"☀️ Good Morning ji! {message.from_user.mention} 🌅")
    
                elif "hello" in message_text or "hii" in message_text or "hey" in message_text:
                    return await message.reply_text(f"👋 Hi {message.from_user.mention}! Kaise ho? 😊")
    
                elif "bye" in message_text or "goodbye" in message_text:
                    return await message.reply_text(f"👋 Goodbye! Take care! {message.from_user.mention} 😊")
    
                elif "thanks" in message_text or "thank you" in message_text:
                    return await message.reply_text("😊 Hehe welcome! Always happy to help! 💫")

                else:
                    try:
                        await client.read_chat_history(message.chat.id)
                    except Exception:
                        pass
                    await reply_message(client, chat_id, bot_id, message_text, message)
                    return
        
        # Save replies from users (only if they don't contain blacklist words)
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)
            
    except (ChatAdminRequired, UserIsBlocked, ChatWriteForbidden, RPCError) as e:
        return
    except (Exception, asyncio.TimeoutError) as e:
        return
