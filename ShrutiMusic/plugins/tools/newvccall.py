import asyncio
from typing import Set, Dict
from pyrogram import filters
from pyrogram.types import Message
from pytgcalls.types import UpdatedGroupCallParticipant, GroupCallParticipant
from pytgcalls import filters as fl

from ShrutiMusic import app, userbot
from ShrutiMusic.core.call import Aviax
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.misc import SUDOERS
from config import adminlist

vcloggerdb = mongodb.vclogger

enabled_chats: Set[int] = set()
user_join_count: Dict[tuple, int] = {}
user_cache: Dict[int, tuple] = {}
vc_participants_cache: Dict[int, list] = {}
DELETE_DELAY = 10

prefixes = [".", "!", "/", "@", "?", "'"]

async def delete_message_after_delay(chat_id: int, message_id: int):
    try:
        await asyncio.sleep(DELETE_DELAY)
        await app.delete_messages(chat_id, message_id)
    except:
        pass

async def get_vc_participants(chat_id: int):
    try:
        for ass in [Aviax.one, Aviax.two, Aviax.three, Aviax.four, Aviax.five]:
            if ass:
                try:
                    participants = await ass.get_participants(chat_id)
                    if participants:
                        vc_participants_cache[chat_id] = participants
                        return participants
                except:
                    continue
    except:
        pass
    return vc_participants_cache.get(chat_id, [])

async def get_user_info(chat_id: int, user_id: int) -> tuple:
    if user_id in user_cache:
        return user_cache[user_id]
    
    name = None
    username = None
    
    try:
        participants = await get_vc_participants(chat_id)
        if participants:
            for p in participants:
                if p.user_id == user_id:
                    break
    except:
        pass
    
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member and member.user:
            user = member.user
            name = user.first_name or ""
            if user.last_name:
                name += f" {user.last_name}"
            username = f"@{user.username}" if user.username else "ɪɢɴᴏʀᴇᴅ"
            name = name.strip()
            if name:
                user_cache[user_id] = (name, username)
                return (name, username)
    except:
        pass
    
    clients = [app, userbot.one, userbot.two, userbot.three, userbot.four, userbot.five]
    
    for client in clients:
        if not client:
            continue
        try:
            user = await client.get_users(user_id)
            if user:
                name = user.first_name or ""
                if user.last_name:
                    name += f" {user.last_name}"
                username = f"@{user.username}" if user.username else "ɪɢɴᴏʀᴇᴅ"
                name = name.strip()
                if name:
                    user_cache[user_id] = (name, username)
                    return (name, username)
        except:
            continue
    
    try:
        async for member in app.get_chat_members(chat_id, limit=200):
            if member.user.id == user_id:
                name = member.user.first_name or ""
                if member.user.last_name:
                    name += f" {member.user.last_name}"
                username = f"@{member.user.username}" if member.user.username else "ɪɢɴᴏʀᴇᴅ"
                name = name.strip()
                if name:
                    user_cache[user_id] = (name, username)
                    return (name, username)
                break
    except:
        pass
    
    name = "ᴜsᴇʀ"
    username = "ɪɢɴᴏʀᴇᴅ"
    user_cache[user_id] = (name, username)
    return (name, username)

def format_user_mention(user_id: int, name: str = None):
    display = name if name else "ᴜsᴇʀ"
    return f'<a href="tg://user?id={user_id}">{display}</a>'

async def send_join_notification(chat_id: int, user_id: int):
    try:
        key = (chat_id, user_id)
        user_join_count[key] = user_join_count.get(key, 0) + 1
        count = user_join_count[key]
        name, username = await get_user_info(chat_id, user_id)
        user_mention = format_user_mention(user_id, name)
        msg = f"➕ {user_mention} ᴊᴏɪɴᴇᴅ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"
        if count > 1:
            msg += f" | ᴊᴏɪɴ ᴄᴏᴜɴᴛ: <code>{count}</code>"
        sent = await app.send_message(chat_id, f"<b>{msg}</b>")
        asyncio.create_task(delete_message_after_delay(chat_id, sent.id))
    except:
        pass

async def send_leave_notification(chat_id: int, user_id: int):
    try:
        name, username = await get_user_info(chat_id, user_id)
        user_mention = format_user_mention(user_id, name)
        msg = f"➖ {user_mention} ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"
        sent = await app.send_message(chat_id, f"<b>{msg}</b>")
        asyncio.create_task(delete_message_after_delay(chat_id, sent.id))
    except:
        pass

async def is_vc_logger(chat_id: int) -> bool:
    try:
        doc = await vcloggerdb.find_one({"chat_id": chat_id})
        if doc and "status" in doc:
            return doc.get("status", True)
    except:
        pass
    return True

async def set_vc_logger(chat_id: int, status: bool):
    try:
        await vcloggerdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "status": status}},
            upsert=True
        )
    except:
        pass

async def get_served_chats() -> list:
    from ShrutiMusic.core.mongo import mongodb
    chatsdb = mongodb.chats
    chats_list = []
    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)
    return chats_list

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        if user_id in SUDOERS:
            return True
        admins = adminlist.get(chat_id)
        if admins and user_id in admins:
            return True
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except:
        return False

async def participant_event_handler(update: UpdatedGroupCallParticipant, action_type: str):
    chat_id = update.chat_id
    user_id = update.participant.user_id
    if chat_id not in enabled_chats:
        enabled_chats.add(chat_id)
    if await is_vc_logger(chat_id):
        if action_type == "join":
            await send_join_notification(chat_id, user_id)
        elif action_type == "leave":
            await send_leave_notification(chat_id, user_id)

for aviax in [Aviax.one, Aviax.two, Aviax.three, Aviax.four, Aviax.five]:
    if aviax:
        aviax.on_update(fl.call_participant(GroupCallParticipant.Action.JOINED))(
            lambda client, update, av=aviax: asyncio.create_task(participant_event_handler(update, "join"))
        )
        aviax.on_update(fl.call_participant(GroupCallParticipant.Action.LEFT))(
            lambda client, update, av=aviax: asyncio.create_task(participant_event_handler(update, "leave"))
        )

async def setup_vc_logger():
    await asyncio.sleep(10)
    try:
        chats = await get_served_chats()
        for chat in chats:
            chat_id = chat.get("chat_id")
            if chat_id and await is_vc_logger(chat_id):
                enabled_chats.add(chat_id)
    except:
        pass

def generate_vclogger_filters():
    return filters.command("vclogger", prefixes=prefixes) & filters.group

@app.on_message(generate_vclogger_filters())
async def vclogger_cmd(client, message: Message):
    try:
        chat_id = message.chat.id
        if not message.from_user:
            if len(message.command) < 2:
                await message.reply_text("<b>⚠️ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ | ᴜsᴇ: /vclogger on ᴏʀ /vclogger off</b>")
                return
            action = message.command[1].lower()
        else:
            if not await is_admin(chat_id, message.from_user.id):
                await message.reply_text("<b>❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!</b>")
                return
            action = message.command[1].lower() if len(message.command) > 1 else None
        if not action:
            status = await is_vc_logger(chat_id)
            status_text = "✅ ᴇɴᴀʙʟᴇᴅ" if status else "❌ ᴅɪsᴀʙʟᴇᴅ"
            await message.reply_text(f"<b>📊 ᴠᴄ ʟᴏɢɢᴇʀ: {status_text}</b>")
            return
        if action in ["on", "enable", "yes"]:
            await set_vc_logger(chat_id, True)
            enabled_chats.add(chat_id)
            await message.reply_text("<b>✅ ᴠᴄ ʟᴏɢɢᴇʀ ᴇɴᴀʙʟᴇᴅ</b>")
        elif action in ["off", "disable", "no"]:
            await set_vc_logger(chat_id, False)
            enabled_chats.discard(chat_id)
            user_join_count.clear()
            await message.reply_text("<b>❌ ᴠᴄ ʟᴏɢɢᴇʀ ᴅɪsᴀʙʟᴇᴅ</b>")
        else:
            await message.reply_text("<b>❌ ᴜsᴇ: /vclogger on ᴏʀ /vclogger off</b>")
    except:
        await message.reply_text("<b>❌ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!</b>")

@app.on_message(filters.command("vcstatus") & filters.group)
async def vcstatus_cmd(client, message: Message):
    try:
        chat_id = message.chat.id
        if not message.from_user or not await is_admin(chat_id, message.from_user.id):
            await message.reply_text("<b>❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!</b>")
            return
        participants = None
        for ass in [Aviax.one, Aviax.two, Aviax.three, Aviax.four, Aviax.five]:
            if ass:
                try:
                    participants = await ass.get_participants(chat_id)
                    break
                except:
                    await asyncio.sleep(1)
                    continue
        if not participants:
            await message.reply_text("<b>📭 ɴᴏ ᴏɴᴇ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ!</b>")
            return
        text = f"<b>📊 ᴠᴏɪᴄᴇ ᴄʜᴀᴛ sᴛᴀᴛᴜs | 👥 ᴛᴏᴛᴀʟ: {len(participants)}</b>\n"
        for i, p in enumerate(participants, 1):
            name, username = await get_user_info(chat_id, p.user_id)
            status = "🔇" if getattr(p, "muted", False) else "🎤"
            if getattr(p, "video", False):
                status += " 🎥"
            display_name = format_user_mention(p.user_id, name)
            text += f"{i}. {display_name} | {status}\n"
        await message.reply_text(text)
    except:
        await message.reply_text("<b>❌ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!</b>")

try:
    asyncio.create_task(setup_vc_logger())
except:
    pass
