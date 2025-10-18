import time
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb

# AFK Collection
afkdb = mongodb.afk

# Small caps mapping
SC_MAP = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
)

def to_small_caps(text):
    return text.translate(SC_MAP)

def get_readable_time(seconds):
    """Convert seconds to readable time format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes > 0:
            return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        if hours > 0:
            return f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
        return f"{days} day{'s' if days != 1 else ''}"

async def add_afk(user_id: int, afk_data: dict):
    """Add user to AFK database"""
    await afkdb.update_one(
        {"user_id": user_id},
        {"$set": afk_data},
        upsert=True
    )

async def is_afk(user_id: int):
    """Check if user is AFK"""
    user = await afkdb.find_one({"user_id": user_id})
    if user:
        return True, user
    return False, None

async def remove_afk(user_id: int):
    """Remove user from AFK database"""
    await afkdb.delete_one({"user_id": user_id})

# AFK Command Handler
@app.on_message(filters.command(["afk", "away", "bye", "goodnight", "gn", "seeyou"], prefixes=["/", "!", ".", ""]) & ~filters.bot)
async def set_afk(client, message: Message):
    """Set user as AFK"""
    if message.sender_chat:
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Get reason from command
    reason = None
    if len(message.command) > 1:
        reason = message.text.split(None, 1)[1].strip()[:200]
    
    # Prepare AFK data with the current message ID to ignore it later
    afk_data = {
        "user_id": user_id,
        "user_name": user_name,
        "reason": reason,
        "time": time.time(),
        "date": datetime.now(),
        "afk_message_id": message.id,  # Store the AFK setting message ID
        "chat_id": message.chat.id     # Store chat ID too for better tracking
    }
    
    # Add to database
    await add_afk(user_id, afk_data)
    
    # Send confirmation message
    if reason:
        await message.reply_text(
            f"<b>❖ {to_small_caps(user_name)}</b> ɪs ɴᴏᴡ <b>AFK</b>!\n\n"
            f"<b>● Reason:</b> <code>{to_small_caps(reason)}</code>",
            disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            f"<b>❖ {to_small_caps(user_name)}</b> ɪs ɴᴏᴡ <b>AFK</b>!",
            disable_web_page_preview=True
        )

# Message Watcher for AFK - Only for NON-command messages
@app.on_message(
    ~filters.bot & 
    ~filters.via_bot & 
    ~filters.command(["afk", "away", "unafk", "afkstatus"]),
    group=2
)
async def afk_watcher(client, message: Message):
    """Watch NON-COMMAND messages for AFK users"""
    if not message.from_user:
        return
    
    response_msg = ""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Check if sender was AFK and remove them
    is_sender_afk, afk_data = await is_afk(user_id)
    if is_sender_afk:
        # Check if this is the same message that set AFK status - if so, ignore it
        if (afk_data.get("afk_message_id") == message.id and 
            afk_data.get("chat_id") == message.chat.id):
            return  # Ignore the AFK setting message itself
        
        await remove_afk(user_id)
        time_away = get_readable_time(time.time() - afk_data["time"])
        
        if afk_data.get("reason"):
            response_msg += (
                f"<b>❖ Welcome back {to_small_caps(user_name)}!</b>\n"
                f"<b>● You were away for:</b> {time_away}\n"
                f"<b>● Reason:</b> <code>{to_small_caps(afk_data['reason'])}</code>\n\n"
            )
        else:
            response_msg += (
                f"<b>❖ Welcome back {to_small_caps(user_name)}!</b>\n"
                f"<b>● You were away for:</b> {time_away}\n\n"
            )
    
    # Check replied user if AFK
    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        is_replied_afk, replied_afk_data = await is_afk(replied_user.id)
        
        if is_replied_afk:
            time_away = get_readable_time(time.time() - replied_afk_data["time"])
            
            if replied_afk_data.get("reason"):
                response_msg += (
                    f"<b>❖ {to_small_caps(replied_user.first_name)}</b> ɪs <b>AFK</b>!\n"
                    f"<b>● Away for:</b> {time_away}\n"
                    f"<b>● Reason:</b> <code>{to_small_caps(replied_afk_data['reason'])}</code>\n\n"
                )
            else:
                response_msg += (
                    f"<b>❖ {to_small_caps(replied_user.first_name)}</b> ɪs <b>AFK</b>!\n"
                    f"<b>● Away for:</b> {time_away}\n\n"
                )
    
    # Check mentioned users if AFK
    if message.entities:
        checked_users = set()
        
        for entity in message.entities:
            try:
                user = None
                
                if entity.type == MessageEntityType.MENTION:
                    username = message.text[entity.offset + 1:entity.offset + entity.length]
                    try:
                        user = await app.get_users(username)
                    except:
                        continue
                        
                elif entity.type == MessageEntityType.TEXT_MENTION:
                    user = entity.user
                
                if user and user.id not in checked_users:
                    checked_users.add(user.id)
                    is_mentioned_afk, mentioned_afk_data = await is_afk(user.id)
                    
                    if is_mentioned_afk:
                        time_away = get_readable_time(time.time() - mentioned_afk_data["time"])
                        
                        if mentioned_afk_data.get("reason"):
                            response_msg += (
                                f"<b>❖ {to_small_caps(user.first_name)}</b> ɪs <b>AFK</b>!\n"
                                f"<b>● Away for:</b> {time_away}\n"
                                f"<b>● Reason:</b> <code>{to_small_caps(mentioned_afk_data['reason'])}</code>\n\n"
                            )
                        else:
                            response_msg += (
                                f"<b>❖ {to_small_caps(user.first_name)}</b> ɪs <b>AFK</b>!\n"
                                f"<b>● Away for:</b> {time_away}\n\n"
                            )
                            
            except Exception as e:
                print(f"Error in mention check: {e}")
                continue
    
    # Send response if there's any AFK info
    if response_msg.strip():
        try:
            await message.reply_text(
                response_msg.strip(),
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Error sending AFK message: {e}")

# Manual Remove AFK
@app.on_message(filters.command("unafk") & ~filters.bot)
async def remove_afk_manual(client, message: Message):
    """Manually remove AFK status"""
    if message.sender_chat:
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    is_user_afk, afk_data = await is_afk(user_id)
    
    if is_user_afk:
        await remove_afk(user_id)
        time_away = get_readable_time(time.time() - afk_data["time"])
        
        await message.reply_text(
            f"<b>❖ Welcome back {to_small_caps(user_name)}!</b>\n"
            f"<b>● You were away for:</b> {time_away}",
            disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            f"<b>❖ {to_small_caps(user_name)}</b> you are <b>NOT AFK</b>!",
            disable_web_page_preview=True
        )

# Check AFK Status
@app.on_message(filters.command("afkstatus") & ~filters.bot)
async def check_afk_status(client, message: Message):
    """Check AFK status of a user"""
    if message.sender_chat:
        return
    
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            username = message.command[1].replace("@", "")
            target_user = await app.get_users(username)
        except:
            await message.reply_text("❌ <b>User not found!</b>")
            return
    else:
        target_user = message.from_user
    
    is_user_afk, afk_data = await is_afk(target_user.id)
    
    if is_user_afk:
        time_away = get_readable_time(time.time() - afk_data["time"])
        
        if afk_data.get("reason"):
            await message.reply_text(
                f"<b>❖ {to_small_caps(target_user.first_name)}</b> ɪs <b>AFK</b>!\n\n"
                f"<b>● Away for:</b> {time_away}\n"
                f"<b>● Reason:</b> <code>{to_small_caps(afk_data['reason'])}</code>",
                disable_web_page_preview=True
            )
        else:
            await message.reply_text(
                f"<b>❖ {to_small_caps(target_user.first_name)}</b> ɪs <b>AFK</b>!\n\n"
                f"<b>● Away for:</b> {time_away}",
                disable_web_page_preview=True
            )
    else:
        await message.reply_text(
            f"<b>❖ {to_small_caps(target_user.first_name)}</b> ɪs <b>NOT AFK</b>!",
            disable_web_page_preview=True
        )
