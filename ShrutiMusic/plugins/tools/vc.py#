import asyncio
from logging import getLogger
from typing import Dict, Set
import random

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.raw import functions
from ShrutiMusic import app
from ShrutiMusic.utils.database import get_assistant

LOGGER = getLogger(__name__)

vc_active_users: Dict[int, Set[int]] = {}
active_monitoring: Dict[int, asyncio.Task] = {}

@app.on_message(filters.video_chat_started)
async def on_vc_started(_, message: Message):
    chat_id = message.chat.id
    LOGGER.info(f"VC started in chat {chat_id}")
    
    if chat_id not in active_monitoring or active_monitoring[chat_id].done():
        active_monitoring[chat_id] = asyncio.create_task(monitor_vc(chat_id))

@app.on_message(filters.video_chat_ended)
async def on_vc_ended(_, message: Message):
    chat_id = message.chat.id
    LOGGER.info(f"VC ended in chat {chat_id}")
    
    if chat_id in active_monitoring and not active_monitoring[chat_id].done():
        active_monitoring[chat_id].cancel()
        active_monitoring.pop(chat_id, None)
    
    vc_active_users.pop(chat_id, None)

async def get_group_call_participants(userbot, peer):
    try:
        full_chat = await userbot.invoke(functions.channels.GetFullChannel(channel=peer))
        if not hasattr(full_chat.full_chat, 'call') or not full_chat.full_chat.call:
            return []
        call = full_chat.full_chat.call
        participants = await userbot.invoke(functions.phone.GetGroupParticipants(
            call=call, ids=[], sources=[], offset="", limit=100
        ))
        return participants.participants
    except Exception as e:
        error_msg = str(e).upper()
        if "420" in error_msg:
            wait_time = int(error_msg.split("FLOOD_WAIT_")[1].split("]")[0])
            await asyncio.sleep(wait_time + 1)
            return await get_group_call_participants(userbot, peer)
        if any(x in error_msg for x in ["GROUPCALL_NOT_FOUND", "CALL_NOT_FOUND", "NO_GROUPCALL"]):
            return []
        return []

async def monitor_vc(chat_id):
    userbot = await get_assistant(chat_id)
    if not userbot:
        LOGGER.error(f"No assistant found for chat {chat_id}")
        return
    
    LOGGER.info(f"Started monitoring VC in chat {chat_id}")
    vc_active_users[chat_id] = set()
    
    while True:
        try:
            peer = await userbot.resolve_peer(chat_id)
            participants_list = await get_group_call_participants(userbot, peer)
            
            if not participants_list:
                await asyncio.sleep(5)
                continue
            
            new_users = set()
            for p in participants_list:
                if hasattr(p, 'peer') and hasattr(p.peer, 'user_id'):
                    new_users.add(p.peer.user_id)
            
            current_users = vc_active_users.get(chat_id, set())
            joined = new_users - current_users
            left = current_users - new_users
            
            if joined or left:
                tasks = []
                for user_id in joined:
                    tasks.append(handle_user_join(chat_id, user_id, userbot))
                for user_id in left:
                    tasks.append(handle_user_leave(chat_id, user_id, userbot))
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            
            vc_active_users[chat_id] = new_users
            await asyncio.sleep(5)
            
        except asyncio.CancelledError:
            LOGGER.info(f"Monitoring stopped for chat {chat_id}")
            break
        except Exception as e:
            LOGGER.error(f"Error monitoring VC in chat {chat_id}: {e}")
            await asyncio.sleep(5)

async def handle_user_join(chat_id, user_id, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "Someone"
        mention = f'<a href="tg://user?id={user_id}"><b>{to_small_caps(name)}</b></a>'
        messages = [
            f"🎤 {mention} <b>ᴊᴜsᴛ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴠᴄ – ʟᴇᴛ's ᴍᴀᴋᴇ ɪᴛ ʟɪᴠᴇʟʏ! 🎶</b>",
            f"✨ {mention} <b>ɪs ɴᴏᴡ ɪɴ ᴛʜᴇ ᴠᴄ – ᴡᴇʟᴄᴏᴍᴇ ᴀʙᴏᴀʀᴅ! 💫</b>",
            f"🎵 {mention} <b>ʜᴀs ᴊᴏɪɴᴇᴅ – ʟᴇᴛ's ʀᴏᴄᴋ ᴛʜɪs ᴠɪʙᴇ! 🔥</b>",
        ]
        msg = random.choice(messages)
        sent_msg = await app.send_message(chat_id, msg)
        asyncio.create_task(delete_after_delay(sent_msg, 10))
    except:
        pass

async def handle_user_leave(chat_id, user_id, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "Someone"
        mention = f'<a href="tg://user?id={user_id}"><b>{to_small_caps(name)}</b></a>'
        messages = [
            f"👋 {mention} <b>ʟᴇғᴛ ᴛʜᴇ ᴠᴄ – ʜᴏᴘᴇ ᴛᴏ sᴇᴇ ʏᴏᴜ ʙᴀᴄᴋ sᴏᴏɴ! 🌟</b>",
            f"🚪 {mention} <b>sᴛᴇᴘᴘᴇᴅ ᴏᴜᴛ – ᴅᴏɴ'ᴛ ᴛᴀᴋᴇ ᴛᴏᴏ ʟᴏɴɢ, ᴡᴇ'ʟʟ ᴍɪss ʏᴏᴜ! 💖</b>",
            f"✌️ {mention} <b>sᴀɪᴅ ɢᴏᴏᴅʙʏᴇ – ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴀɴᴅ ᴊᴏɪɴ ᴛʜᴇ ғᴜɴ ᴀɢᴀɪɴ! 🎶</b>",
        ]
        msg = random.choice(messages)
        sent_msg = await app.send_message(chat_id, msg)
        asyncio.create_task(delete_after_delay(sent_msg, 10))
    except:
        pass

async def delete_after_delay(message, delay):
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

def to_small_caps(text):
    mapping = {
        "a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ꜰ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ",
        "k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ",
        "u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ",
        "A":"ᴀ","B":"ʙ","C":"ᴄ","D":"ᴅ","E":"ᴇ","F":"ꜰ","G":"ɢ","H":"ʜ","I":"ɪ","J":"ᴊ",
        "K":"ᴋ","L":"ʟ","M":"ᴍ","N":"ɴ","O":"ᴏ","P":"ᴘ","Q":"ǫ","R":"ʀ","S":"s","T":"ᴛ",
        "U":"ᴜ","V":"ᴠ","W":"ᴡ","X":"x","Y":"ʏ","Z":"ᴢ"
    }
    return "".join(mapping.get(c,c) for c in text)
