from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
import re

banworddb = mongodb.banwords

def smallcaps(text: str) -> str:
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ" \
            "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    table = str.maketrans(normal, small)
    return text.translate(table)

async def get_banwords(chat_id: int):
    data = await banworddb.find_one({"chat_id": chat_id})
    if not data:
        return []
    return data.get("words", [])

async def add_banword(chat_id: int, word: str):
    word = word.lower().strip()  # Clean the word
    words = await get_banwords(chat_id)
    if word in words:
        return False
    words.append(word)
    await banworddb.update_one(
        {"chat_id": chat_id}, {"$set": {"words": words}}, upsert=True
    )
    return True

async def remove_banword(chat_id: int, word: str):
    word = word.lower().strip()  # Clean the word
    words = await get_banwords(chat_id)
    if word not in words:
        return False
    words.remove(word)
    if words:  # If list is not empty
        await banworddb.update_one(
            {"chat_id": chat_id}, {"$set": {"words": words}}, upsert=True
        )
    else:  # If list is empty, remove the document or set empty list
        await banworddb.update_one(
            {"chat_id": chat_id}, {"$set": {"words": []}}, upsert=True
        )
    return True

async def get_adminlock(chat_id: int) -> bool:
    data = await banworddb.find_one({"chat_id": chat_id})
    if not data:
        return False
    return data.get("admin_lock", False)

async def set_adminlock(chat_id: int, status: bool):
    await banworddb.update_one(
        {"chat_id": chat_id}, {"$set": {"admin_lock": status}}, upsert=True
    )

async def is_admin(chat_id: int, user_id: int) -> bool:
    if not user_id:
        return False
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

def check_blacklist_word(text: str, blacklist_words: list) -> tuple:
    """
    Check if text contains any blacklist word as complete word
    Returns (is_found, found_word)
    """
    if not text or not blacklist_words:
        return False, None
    
    text_lower = text.lower()
    
    for word in blacklist_words:
        word = word.strip().lower()
        if not word:
            continue
            
        # Check for exact word match using word boundaries
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            return True, word
    
    return False, None

@app.on_message(filters.command("addblacklist") & filters.group)
async def add_blacklist_handler(_, message: Message):
    if not message.from_user:
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(f"<b>{smallcaps('only admins can add blacklist words!')}</b>")

    if len(message.command) < 2:
        return await message.reply_text(f"<b>{smallcaps('usage: /addblacklist word')}</b>")

    word = message.text.split(None, 1)[1].lower().strip()
    if not word:
        return await message.reply_text(f"<b>{smallcaps('please provide a valid word!')}</b>")
        
    done = await add_banword(message.chat.id, word)
    if done:
        await message.reply_text(f"<b>✅ {smallcaps('added blacklist word:')}</b> <code>{word}</code>")
    else:
        await message.reply_text(f"<b>⚠️ {smallcaps('word already in blacklist:')}</b> <code>{word}</code>")

@app.on_message(filters.command("removeblacklist") & filters.group)
async def remove_blacklist_handler(_, message: Message):
    if not message.from_user:
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(f"<b>{smallcaps('only admins can remove blacklist words!')}</b>")

    if len(message.command) < 2:
        return await message.reply_text(f"<b>{smallcaps('usage: /removeblacklist word')}</b>")

    word = message.text.split(None, 1)[1].lower().strip()
    if not word:
        return await message.reply_text(f"<b>{smallcaps('please provide a valid word!')}</b>")
        
    done = await remove_banword(message.chat.id, word)
    if done:
        await message.reply_text(f"<b>🗑️ {smallcaps('removed blacklist word:')}</b> <code>{word}</code>")
    else:
        await message.reply_text(f"<b>⚠️ {smallcaps('word not found in blacklist:')}</b> <code>{word}</code>")

@app.on_message(filters.command("listblacklist") & filters.group)
async def list_blacklist_handler(_, message: Message):
    words = await get_banwords(message.chat.id)
    if not words:
        return await message.reply_text(f"<b>{smallcaps('no blacklist words set in this group.')}</b>")
    
    text = f"<b>🚫 {smallcaps('blacklist words in this group:')}</b>\n\n"
    text += "\n".join([f"• <code>{w}</code>" for w in words if w.strip()])
    await message.reply_text(text)

@app.on_message(filters.command("adminblacklist") & filters.group)
async def adminblacklist_handler(_, message: Message):
    if not message.from_user:
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text(f"<b>{smallcaps('only admins can toggle admin blacklist!')}</b>")

    if len(message.command) < 2:
        current_status = await get_adminlock(message.chat.id)
        status_text = "enabled" if current_status else "disabled"
        return await message.reply_text(
            f"<b>{smallcaps('current adminblacklist status:')} {status_text}</b>\n"
            f"<b>{smallcaps('usage: /adminblacklist [on|off]')}</b>"
        )

    arg = message.command[1].lower()
    if arg == "on":
        await set_adminlock(message.chat.id, True)
        await message.reply_text(f"<b>🔒 {smallcaps('adminblacklist enabled! admins will also be restricted.')}</b>")
    elif arg == "off":
        await set_adminlock(message.chat.id, False)
        await message.reply_text(f"<b>🔓 {smallcaps('adminblacklist disabled! admins can use blacklist words.')}</b>")
    else:
        await message.reply_text(f"<b>{smallcaps('usage: /adminblacklist [on|off]')}</b>")

@app.on_message(filters.command("helpblacklist") & filters.group)
async def help_blacklist_handler(_, message: Message):
    text = f"""
<b>{smallcaps('blacklist commands:')}</b>

★ /addblacklist word - {smallcaps('add a blacklist word')}
★ /removeblacklist word - {smallcaps('remove a blacklist word')}
★ /listblacklist - {smallcaps('list all blacklist words')}
★ /adminblacklist on|off - {smallcaps('toggle admin blacklist')}
★ /helpblacklist - {smallcaps('show this help')}

<b>{smallcaps('note: blacklist checks for complete words only, not partial matches.')}</b>
"""
    await message.reply_text(text)

@app.on_message(filters.text & filters.group, group=3)
async def blacklist_detector(_, message: Message):
    # Skip if no message text or from_user
    if not message.text or not message.from_user:
        return
        
    words = await get_banwords(message.chat.id)
    if not words:
        return

    # Check for blacklist words using improved function
    is_found, found_word = check_blacklist_word(message.text, words)
    
    if is_found:
        user_id = message.from_user.id
        isadmin = await is_admin(message.chat.id, user_id)
        adminlock = await get_adminlock(message.chat.id)

        # If admin and adminlock is off -> ignore
        if isadmin and not adminlock:
            return

        try:
            await message.delete()
            await message.reply_text(
                f"<b>🚫 {smallcaps('blacklist word detected!')}</b>\n"
                f"{message.from_user.mention} {smallcaps('used a blacklisted word:')} <code>{found_word}</code>",
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Error deleting blacklist message: {e}")
            pass
