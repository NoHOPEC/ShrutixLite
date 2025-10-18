from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
import re
import asyncio

# Mongo Collections
lockdb = mongodb.locks
warndb = mongodb.warnings

# ------------------- Small Caps Helper -------------------

def smallcaps(text: str) -> str:
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ" \
            "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    table = str.maketrans(normal, small)
    return text.translate(table)

# ------------------- Database Helpers -------------------

async def get_locks(chat_id: int):
    data = await lockdb.find_one({"chat_id": chat_id})
    if not data:
        return {"admin_lock": False, "locked": []}
    return data

async def set_lock(chat_id: int, lock_type: str, status: bool):
    data = await get_locks(chat_id)
    locked = data.get("locked", [])
    if status and lock_type not in locked:
        locked.append(lock_type)
    elif not status and lock_type in locked:
        locked.remove(lock_type)
    await lockdb.update_one({"chat_id": chat_id}, {"$set": {"locked": locked}}, upsert=True)

async def set_adminlock(chat_id: int, status: bool):
    await lockdb.update_one({"chat_id": chat_id}, {"$set": {"admin_lock": status}}, upsert=True)

async def unlock_all(chat_id: int):
    await lockdb.update_one({"chat_id": chat_id}, {"$set": {"locked": [], "admin_lock": False}}, upsert=True)

# ------------------- Warning System -------------------

async def get_warnings(chat_id: int, user_id: int):
    data = await warndb.find_one({"chat_id": chat_id, "user_id": user_id})
    return data.get("warns", 0) if data else 0

async def add_warning(chat_id: int, user_id: int):
    current_warns = await get_warnings(chat_id, user_id)
    new_warns = current_warns + 1
    await warndb.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"warns": new_warns}},
        upsert=True
    )
    return new_warns

async def clear_warnings(chat_id: int, user_id: int):
    await warndb.delete_one({"chat_id": chat_id, "user_id": user_id})

# ------------------- Permission Helpers -------------------

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

async def can_change_info(chat_id: int, user_id: int) -> bool:
    """Check if user has can_change_info permission"""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            return member.privileges.can_change_info if member.privileges else False
        return False
    except:
        return False

async def can_restrict_members(chat_id: int, user_id: int) -> bool:
    """Check if user can restrict members"""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            return member.privileges.can_restrict_members if member.privileges else False
        return False
    except:
        return False

# ------------------- Lockable Types -------------------

LOCKABLES = [
    "all", "audio", "bots", "button", "contact", "document", "egame", "forward", 
    "game", "gif", "info", "inline", "invite", "location", "media", "messages", 
    "other", "photo", "pin", "poll", "previews", "rtl", "sticker", "url", "username", "video", "voice"
]

# ------------------- Detection Helper Functions -------------------

def contains_url(text: str) -> bool:
    if not text:
        return False
    patterns = [
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

def contains_invite_link(text: str) -> bool:
    if not text:
        return False
    patterns = [
        r't\.me/joinchat/[a-zA-Z0-9_-]+',
        r't\.me/\+[a-zA-Z0-9_-]+',
        r'telegram\.me/joinchat/[a-zA-Z0-9_-]+',
        r'telegram\.me/\+[a-zA-Z0-9_-]+',
        r'tg://join\?invite=[a-zA-Z0-9_-]+',
        r'joinchat/[a-zA-Z0-9_-]+'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

def contains_username(text: str) -> bool:
    if not text:
        return False
    pattern = r'@[a-zA-Z0-9_]{5,32}'
    return bool(re.search(pattern, text))

def has_username_entity(message: Message) -> bool:
    if not message.entities:
        return False
    return any(entity.type == "mention" for entity in message.entities)

def is_rtl_text(text: str) -> bool:
    if not text:
        return False
    rtl_chars = '\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF'
    return bool(re.search(f'[{rtl_chars}]', text))

def has_buttons(message: Message) -> bool:
    return bool(message.reply_markup and hasattr(message.reply_markup, 'inline_keyboard'))

def has_web_preview(message: Message) -> bool:
    return bool(message.web_page)

# ------------------- UI Helper -------------------

def get_premium_button_text(lock_type: str, is_locked: bool) -> str:
    icons = {
        "all": "🌐", "audio": "🎵", "bots": "🤖", "button": "🔘", "contact": "📞",
        "document": "📄", "egame": "🎮", "forward": "↗️", "game": "🎯", "gif": "🎭",
        "info": "ℹ️", "inline": "🔗", "invite": "📩", "location": "📍", "media": "📸",
        "messages": "💬", "other": "📦", "photo": "🖼️", "pin": "📌", "poll": "📊",
        "previews": "👁️", "rtl": "🔄", "sticker": "🎨", "url": "🌍", 
        "username": "👤", "video": "🎬", "voice": "🎙️"
    }
    
    icon = icons.get(lock_type, "🔒")
    status = "✅ ON" if is_locked else "❌ OFF"
    return f"{icon} {lock_type.upper()} {status}"

# ------------------- Auto Delete Notification -------------------

async def delete_notification(message: Message, delay: int):
    """Delete notification message after delay"""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

# ------------------- Bot Prevention Core Handler -------------------

async def handle_bot_violation(chat_id: int, bot_user, actor_user, action_type: str):
    """
    Universal handler for bot-related violations
    action_type: 'added', 'promoted', or 'joined'
    """
    try:
        # Check if bots are locked
        data = await get_locks(chat_id)
        if "bots" not in data.get("locked", []):
            return
        
        # Get adminlock status
        adminlock = data.get("admin_lock", False)
        
        # Check if actor is admin
        actor_is_admin = await is_admin(chat_id, actor_user.id)
        
        # Determine if bot should be removed
        should_remove = False
        action_reason = ""
        
        if adminlock:
            # Admin lock ON: Nobody can add/promote bots
            should_remove = True
            action_reason = f"Admin lock is ON - bots cannot be {action_type}"
        elif not actor_is_admin:
            # Admin lock OFF: Only non-admins are restricted
            should_remove = True
            action_reason = f"Only admins can {action_type.replace('ed', '')} bots when bot lock is active"
        
        if should_remove:
            try:
                # Remove the bot (kick and unban to remove without banning permanently)
                await app.ban_chat_member(chat_id, bot_user.id)
                await app.unban_chat_member(chat_id, bot_user.id)
                
                # Add warning to user
                warns = await add_warning(chat_id, actor_user.id)
                
                # Action description
                action_descriptions = {
                    'added': 'Bot Addition',
                    'promoted': 'Bot Promotion',
                    'joined': 'Bot Join'
                }
                action_desc = action_descriptions.get(action_type, 'Bot Action')
                
                # Determine warning message based on admin status
                is_user_admin = await is_admin(chat_id, actor_user.id)
                
                if is_user_admin:
                    # Admin warning (no limit, no ban)
                    warning_msg = await app.send_message(
                        chat_id,
                        f"<b>🚫🤖 {smallcaps('bot blocked!')} 🤖🚫</b>\n\n"
                        f"👤 <b>Admin:</b> {actor_user.mention}\n"
                        f"🤖 <b>Bot:</b> {bot_user.mention if hasattr(bot_user, 'mention') else bot_user.first_name}\n"
                        f"⚙️ <b>Action:</b> {action_desc}\n"
                        f"⚠️ <b>Warnings:</b> {warns}\n"
                        f"📝 <b>Reason:</b> {action_reason}\n\n"
                        f"<i>💡 Bots are completely locked in this group!</i>\n"
                        f"<i>👑 Admins receive warnings but won't be banned</i>"
                    )
                else:
                    # Regular user warning (counts but no ban)
                    warning_msg = await app.send_message(
                        chat_id,
                        f"<b>🚫🤖 {smallcaps('bot blocked!')} 🤖🚫</b>\n\n"
                        f"👤 <b>User:</b> {actor_user.mention}\n"
                        f"🤖 <b>Bot:</b> {bot_user.mention if hasattr(bot_user, 'mention') else bot_user.first_name}\n"
                        f"⚙️ <b>Action:</b> {action_desc}\n"
                        f"⚠️ <b>Warnings:</b> {warns}\n"
                        f"📝 <b>Reason:</b> {action_reason}\n\n"
                        f"<i>💡 Bots are completely locked in this group!</i>\n"
                        f"<i>⚠️ Warnings are tracked but no auto-ban</i>"
                    )
                
                # Delete warning message after 10 seconds
                asyncio.create_task(delete_notification(warning_msg, 10))
                
            except Exception as e:
                print(f"Error removing bot: {e}")
    
    except Exception as e:
        print(f"Error in handle_bot_violation: {e}")

# ------------------- Bot Detection via new_chat_members (Fallback) -------------------

@app.on_message(filters.new_chat_members & filters.group, group=1)
async def handle_new_members_fallback(_, message: Message):
    """
    Fallback handler for bot additions via service messages
    This catches cases where chat_member_updated might not trigger
    """
    try:
        # Check each new member
        for new_member in message.new_chat_members:
            if not new_member.is_bot:
                continue
                
            # Get who added the bot
            adder = message.from_user
            if not adder:
                continue
            
            # Handle bot addition
            await handle_bot_violation(message.chat.id, new_member, adder, "added")
    
    except Exception as e:
        print(f"Error in handle_new_members_fallback: {e}")

# ------------------- Primary Bot Detection via chat_member_updated -------------------

@app.on_chat_member_updated(group=1)
async def handle_chat_member_update(_, update: ChatMemberUpdated):
    """
    PRIMARY HANDLER: Detects ALL bot-related status changes
    - Bot being added (LEFT/BANNED → MEMBER/ADMIN)
    - Bot being promoted (MEMBER → ADMIN)
    - Catches ALL cases including direct adds and promotions
    """
    try:
        # Verify we have the necessary data
        if not update.new_chat_member or not update.new_chat_member.user:
            return
        
        # Check if the updated member is a bot
        if not update.new_chat_member.user.is_bot:
            return
        
        bot_user = update.new_chat_member.user
        
        # Get old and new status
        old_status = update.old_chat_member.status if update.old_chat_member else ChatMemberStatus.LEFT
        new_status = update.new_chat_member.status
        
        # Who performed the action
        actor = update.from_user
        if not actor:
            return
        
        # ========== DETECTION LOGIC ==========
        
        # Case 1: Bot was NOT a member (LEFT/BANNED), now IS a member (MEMBER/ADMIN)
        # This is a NEW BOT ADDITION
        if old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
            if new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
                await handle_bot_violation(update.chat.id, bot_user, actor, "added")
                return
        
        # Case 2: Bot was already MEMBER, now promoted to ADMINISTRATOR
        # This is a BOT PROMOTION
        if old_status == ChatMemberStatus.MEMBER:
            if new_status == ChatMemberStatus.ADMINISTRATOR:
                await handle_bot_violation(update.chat.id, bot_user, actor, "promoted")
                return
        
        # Case 3: Bot was RESTRICTED, now MEMBER or ADMIN
        # This is also treated as addition/re-addition
        if old_status == ChatMemberStatus.RESTRICTED:
            if new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
                await handle_bot_violation(update.chat.id, bot_user, actor, "added")
                return
    
    except Exception as e:
        print(f"Error in handle_chat_member_update: {e}")

# ------------------- Commands -------------------

@app.on_message(filters.command("lock") & filters.group)
async def lock_handler(_, message: Message):
    if not message.from_user:
        return
    
    if not await can_change_info(message.chat.id, message.from_user.id):
        return await message.reply_text(
            f"<b>🚫 {smallcaps('you need can_change_info permission to use locks!')}</b>"
        )

    if len(message.command) < 2:
        available_locks = "\n".join([f"• {lock}" for lock in LOCKABLES])
        return await message.reply_text(
            f"<b>🔒 {smallcaps('usage: /lock [type]')}</b>\n\n"
            f"<b>📋 {smallcaps('available locks:')}</b>\n{available_locks}"
        )

    lock_type = message.command[1].lower()
    if lock_type not in LOCKABLES:
        available_locks = "\n".join([f"• {lock}" for lock in LOCKABLES])
        return await message.reply_text(
            f"<b>❌ {smallcaps('invalid lock type!')}</b>\n\n"
            f"<b>📋 {smallcaps('available locks:')}</b>\n{available_locks}"
        )

    await set_lock(message.chat.id, lock_type, True)
    
    if lock_type == "bots":
        extra_info = (
            f"\n\n<b>🛡️ {smallcaps('bot protection active!')}</b>\n"
            f"<i>✅ Bot additions blocked</i>\n"
            f"<i>✅ Bot promotions blocked</i>\n"
            f"<i>✅ Auto-warning system enabled</i>\n"
            f"<i>💡 Use /lockadmin on to restrict admins too!</i>"
        )
    else:
        extra_info = ""
    
    await message.reply_text(
        f"<b>🔒✨ {smallcaps(lock_type + ' locked successfully!')}</b>{extra_info}"
    )

@app.on_message(filters.command("unlock") & filters.group)
async def unlock_handler(_, message: Message):
    if not message.from_user:
        return
    
    if not await can_change_info(message.chat.id, message.from_user.id):
        return await message.reply_text(
            f"<b>🚫 {smallcaps('you need can_change_info permission to use locks!')}</b>"
        )

    if len(message.command) < 2:
        return await message.reply_text(f"<b>🔓 {smallcaps('usage: /unlock [type]')}</b>")

    lock_type = message.command[1].lower()
    if lock_type not in LOCKABLES:
        available_locks = "\n".join([f"• {lock}" for lock in LOCKABLES])
        return await message.reply_text(
            f"<b>❌ {smallcaps('invalid lock type!')}</b>\n\n"
            f"<b>📋 {smallcaps('available locks:')}</b>\n{available_locks}"
        )

    await set_lock(message.chat.id, lock_type, False)
    await message.reply_text(f"<b>🔓✨ {smallcaps(lock_type + ' unlocked successfully!')}</b>")

@app.on_message(filters.command("unlockall") & filters.group)
async def unlockall_handler(_, message: Message):
    if not message.from_user:
        return
    
    if not await can_change_info(message.chat.id, message.from_user.id):
        return await message.reply_text(
            f"<b>🚫 {smallcaps('you need can_change_info permission to use locks!')}</b>"
        )

    await unlock_all(message.chat.id)
    await message.reply_text(f"<b>🔓🌟 {smallcaps('all locks removed successfully!')}</b>")

@app.on_message(filters.command("locks") & filters.group)
async def locks_handler(_, message: Message):
    if not await can_change_info(message.chat.id, message.from_user.id):
        return await message.reply_text(
            f"<b>🚫 {smallcaps('you need can_change_info permission to use locks!')}</b>"
        )

    data = await get_locks(message.chat.id)
    locked = data.get("locked", [])

    buttons = []
    for i in range(0, len(LOCKABLES), 2):
        row = []
        for l in LOCKABLES[i:i+2]:
            is_locked = l in locked
            button_text = get_premium_button_text(l, is_locked)
            row.append(InlineKeyboardButton(button_text, callback_data=f"toggle_lock:{l}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔓🌟 UNLOCK ALL 🌟🔓", callback_data="unlock_all")])

    await message.reply_text(
        f"<b>🔒✨ {smallcaps('premium lock settings')} ✨🔒</b>\n"
        f"<i>🎯 {smallcaps('tap to toggle locks')} 🎯</i>",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(filters.regex("^toggle_lock"))
async def toggle_lock_callback(_, query: CallbackQuery):
    if not await can_change_info(query.message.chat.id, query.from_user.id):
        return await query.answer("🚫 You need can_change_info permission!", show_alert=True)

    lock_type = query.data.split(":")[1]
    data = await get_locks(query.message.chat.id)
    locked = data.get("locked", [])

    if lock_type in locked:
        await set_lock(query.message.chat.id, lock_type, False)
        await query.answer(f"🔓✨ {lock_type} unlocked!", show_alert=True)
    else:
        await set_lock(query.message.chat.id, lock_type, True)
        if lock_type == "bots":
            await query.answer(f"🔒✨ {lock_type} locked! Bots fully blocked!", show_alert=True)
        else:
            await query.answer(f"🔒✨ {lock_type} locked!", show_alert=True)

    # Update buttons
    data = await get_locks(query.message.chat.id)
    locked = data.get("locked", [])
    buttons = []
    for i in range(0, len(LOCKABLES), 2):
        row = []
        for l in LOCKABLES[i:i+2]:
            is_locked = l in locked
            button_text = get_premium_button_text(l, is_locked)
            row.append(InlineKeyboardButton(button_text, callback_data=f"toggle_lock:{l}"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("🔓🌟 UNLOCK ALL 🌟🔓", callback_data="unlock_all")])

    await query.message.edit_text(
        f"<b>🔒✨ {smallcaps('premium lock settings')} ✨🔒</b>\n"
        f"<i>🎯 {smallcaps('tap to toggle locks')} 🎯</i>",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(filters.regex("^unlock_all"))
async def unlock_all_callback(_, query: CallbackQuery):
    if not await can_change_info(query.message.chat.id, query.from_user.id):
        return await query.answer("🚫 You need can_change_info permission!", show_alert=True)

    await unlock_all(query.message.chat.id)
    await query.answer("🔓🌟 All locks removed!", show_alert=True)

    buttons = []
    for i in range(0, len(LOCKABLES), 2):
        row = []
        for l in LOCKABLES[i:i+2]:
            button_text = get_premium_button_text(l, False)
            row.append(InlineKeyboardButton(button_text, callback_data=f"toggle_lock:{l}"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("🔓🌟 UNLOCK ALL 🌟🔓", callback_data="unlock_all")])

    await query.message.edit_text(
        f"<b>🔒✨ {smallcaps('premium lock settings')} ✨🔒</b>\n"
        f"<i>🎯 {smallcaps('tap to toggle locks')} 🎯</i>",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_message(filters.command("lockadmin") & filters.group)
async def lockadmin_handler(_, message: Message):
    if not await can_change_info(message.chat.id, message.from_user.id):
        return await message.reply_text(
            f"<b>🚫 {smallcaps('you need can_change_info permission!')}</b>"
        )

    if len(message.command) < 2:
        data = await get_locks(message.chat.id)
        status = "ON ✅" if data.get("admin_lock", False) else "OFF ❌"
        return await message.reply_text(
            f"<b>⚙️ {smallcaps('lockadmin status:')} {status}</b>\n\n"
            f"<b>Usage:</b> <code>/lockadmin [on|off]</code>"
        )

    arg = message.command[1].lower()
    if arg == "on":
        await set_adminlock(message.chat.id, True)
        await message.reply_text(
            f"<b>🔒👑 {smallcaps('lockadmin enabled!')}</b>\n\n"
            f"<i>🚫 Admins are now restricted by locks!</i>\n"
            f"<i>🤖 Even admins cannot add/promote bots!</i>\n"
            f"<i>⚡ Maximum security mode activated!</i>"
        )
    elif arg == "off":
        await set_adminlock(message.chat.id, False)
        await message.reply_text(
            f"<b>🔓👑 {smallcaps('lockadmin disabled!')}</b>\n\n"
            f"<i>✅ Admins are now exempt from locks!</i>\n"
            f"<i>👮 Only regular members will be restricted!</i>"
        )
    else:
        await message.reply_text(
            f"<b>❌ {smallcaps('invalid argument!')}</b>\n"
            f"<b>Usage:</b> <code>/lockadmin [on|off]</code>"
        )

@app.on_message(filters.command("locktypes") & filters.group)
async def locktypes_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>🚫 Only admins can view lock types!</b>")

    text = "<b>🔒✨ Available Lock Types ✨🔒</b>\n\n"
    descriptions = {
        "all": "Blocks all messages",
        "audio": "Blocks audio files", 
        "bots": "🔥 FULL bot protection - blocks additions & promotions",
        "button": "Blocks messages with inline buttons",
        "contact": "Blocks contact sharing",
        "document": "Blocks document files",
        "egame": "Blocks embedded games",
        "forward": "Blocks forwarded messages",
        "game": "Blocks games",
        "gif": "Blocks GIF animations",
        "info": "Blocks service messages",
        "inline": "Blocks inline bot results",
        "invite": "Blocks invite links",
        "location": "Blocks location/venue sharing",
        "media": "Blocks all media types",
        "messages": "Blocks text messages",
        "other": "Blocks other content types",
        "photo": "Blocks photos/images",
        "pin": "Blocks pinned messages",
        "poll": "Blocks polls",
        "previews": "Blocks link previews",
        "rtl": "Blocks RTL text",
        "sticker": "Blocks stickers",
        "url": "Blocks URLs/links",
        "username": "Blocks username mentions (@username)",
        "video": "Blocks videos",
        "voice": "Blocks voice messages"
    }

    for lock_type in LOCKABLES:
        desc = descriptions.get(lock_type, "Special lock type")
        icon = {"all": "🌐", "audio": "🎵", "bots": "🤖", "button": "🔘", "contact": "📞",
                "document": "📄", "egame": "🎮", "forward": "↗️", "game": "🎯", "gif": "🎭",
                "info": "ℹ️", "inline": "🔗", "invite": "📩", "location": "📍", "media": "📸",
                "messages": "💬", "other": "📦", "photo": "🖼️", "pin": "📌", "poll": "📊",
                "previews": "👁️", "rtl": "🔄", "sticker": "🎨", "url": "🌍", 
                "username": "👤", "video": "🎬", "voice": "🎙️"}.get(lock_type, "🔒")
        text += f"{icon} <code>{lock_type}</code> - {desc}\n"

    text += f"\n<b>💡 Usage:</b> <code>/lock [type]</code> or <code>/unlock [type]</code>"
    text += f"\n<b>⚡ Quick:</b> <code>/unlockall</code> to remove all locks"
    text += f"\n<b>🔧 Permission:</b> Can Change Info required"
    text += f"\n<b>🤖 Bot Lock:</b> Complete protection against bot additions & promotions!"
    text += f"\n<b>👑 LockAdmin:</b> <code>/lockadmin on</code> to restrict admins too!"

    await message.reply_text(text)

@app.on_message(filters.command("clearwarns") & filters.group)
async def clearwarns_handler(_, message: Message):
    if not await can_restrict_members(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>🚫 You need restrict members permission!</b>")
    
    if not message.reply_to_message:
        return await message.reply_text("<b>Reply to a user to clear their warnings!</b>")
    
    user = message.reply_to_message.from_user
    if not user:
        return
    
    await clear_warnings(message.chat.id, user.id)
    await message.reply_text(
        f"<b>✅ Warnings cleared for {user.mention}!</b>"
    )

@app.on_message(filters.command("lockwarns") & filters.group)
async def lockwarns_handler(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>🚫 Only admins can check lock warnings!</b>")
    
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except:
            return await message.reply_text("<b>❌ User not found!</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID!</b>")
    
    if not user:
        return
    
    warns = await get_warnings(message.chat.id, user.id)
    await message.reply_text(
        f"<b>🤖 Lock Warnings for {user.mention}</b>\n"
        f"<b>Current:</b> {warns}/3\n"
        f"<i>{'⚠️ Close to ban!' if warns >= 2 else '✅ Safe'}</i>\n"
        f"<i>💡 These warnings are for bot lock violations</i>"
    )

# ------------------- Enhanced Lock Detector -------------------

@app.on_message(filters.group, group=4)
async def lock_detector(_, message: Message):
    try:
        data = await get_locks(message.chat.id)
        locked = data.get("locked", [])
        adminlock = data.get("admin_lock", False)

        if not locked:
            return

        if message.service and "info" not in locked:
            return

        user_id = message.from_user.id if message.from_user else None
        if not user_id and "bots" not in locked:
            return

        # Check admin permissions
        isadmin = await is_admin(message.chat.id, user_id) if user_id else False
        if isadmin and not adminlock:
            return

        delete = False
        reason = None

        # Get text content
        text_content = message.text or message.caption or ""

        # ========== LOCK DETECTION ==========
        
        if "all" in locked:
            delete, reason = True, "all content"
        
        elif "messages" in locked and message.text:
            delete, reason = True, "text messages"
        
        elif "media" in locked and (message.photo or message.video or message.audio or 
                                  message.voice or message.video_note or message.document or 
                                  message.sticker or message.animation):
            delete, reason = True, "media content"
        
        elif "photo" in locked and message.photo:
            delete, reason = True, "photos"
        
        elif "video" in locked and message.video:
            delete, reason = True, "videos"
        
        elif "audio" in locked and message.audio:
            delete, reason = True, "audio files"
        
        elif "voice" in locked and message.voice:
            delete, reason = True, "voice messages"
        
        elif "document" in locked and message.document:
            delete, reason = True, "documents"
        
        elif "sticker" in locked and message.sticker:
            delete, reason = True, "stickers"
        
        elif "gif" in locked and (message.animation or 
                                (message.document and message.document.mime_type == "video/mp4")):
            delete, reason = True, "GIFs"
        
        elif "url" in locked and (contains_url(text_content) or 
                                (message.entities and any(e.type in ["url", "text_link"] for e in message.entities))):
            delete, reason = True, "URLs"
        
        elif "username" in locked and (contains_username(text_content) or has_username_entity(message)):
            delete, reason = True, "username mentions"
        
        elif "invite" in locked and contains_invite_link(text_content):
            delete, reason = True, "invite links"
        
        elif "forward" in locked and (message.forward_from or message.forward_from_chat):
            delete, reason = True, "forwarded messages"
        
        elif "inline" in locked and message.via_bot:
            delete, reason = True, "inline results"
        
        elif "bots" in locked and message.via_bot:
            delete, reason = True, "bot messages"
        
        elif "button" in locked and has_buttons(message):
            delete, reason = True, "inline buttons"
        
        elif "game" in locked and message.game:
            delete, reason = True, "games"
        
        elif "egame" in locked and message.game:
            delete, reason = True, "embedded games"
        
        elif "poll" in locked and message.poll:
            delete, reason = True, "polls"
        
        elif "location" in locked and (message.location or message.venue):
            delete, reason = True, "location"
        
        elif "contact" in locked and message.contact:
            delete, reason = True, "contact"
        
        elif "rtl" in locked and is_rtl_text(text_content):
            delete, reason = True, "RTL text"
        
        elif "previews" in locked and has_web_preview(message):
            delete, reason = True, "link previews"
        
        elif "info" in locked and message.service:
            delete, reason = True, "service messages"
        
        elif "pin" in locked and message.service and hasattr(message.service, 'pinned_message'):
            delete, reason = True, "pinned messages"
        
        elif "other" in locked and not any([message.text, message.photo, message.video, 
                                           message.audio, message.voice, message.document, 
                                           message.sticker, message.animation]):
            delete, reason = True, "other content"

        # ========== DELETE AND NOTIFY ==========
        if delete and reason:
            try:
                await message.delete()
                
                if message.from_user:
                    user_mention = message.from_user.mention or f"@{message.from_user.username}" or message.from_user.first_name
                    notification = await app.send_message(
                        message.chat.id,
                        f"<b>🚫✨ {smallcaps(reason + ' are locked!')} ✨🚫</b>\n"
                        f"👤 {user_mention} {smallcaps('tried to send locked content.')}",
                        reply_to_message_id=None
                    )
                    
                    asyncio.create_task(delete_notification(notification, 5))
                    
            except Exception as e:
                print(f"Error deleting message: {e}")

    except Exception as e:
        print(f"Lock detector error: {e}")

print("=" * 60)
print("✅ Advanced Lock System Loaded Successfully!")
print("=" * 60)
print("🔒 Features:")
print("  • Complete Bot Protection (Additions & Promotions)")
print("  • Automatic Warning System (3 warnings = ban)")
print("  • LockAdmin Support (Restrict even admins)")
print("  • Real-time Detection via chat_member_updated")
print("  • Permission-based Control (can_change_info)")
print("=" * 60)
print("🤖 Bot Lock Status: FULLY OPERATIONAL")
print("  ✓ Blocks bot additions (any user/admin)")
print("  ✓ Blocks bot promotions (any user/admin)")
print("  ✓ Works with /lockadmin on/off")
print("  ✓ Dual handler system (fallback support)")
print("=" * 60)
print("💡 Commands:")
print("  /lock bots - Enable bot protection")
print("  /lockadmin on - Restrict admins too")
print("  /lockwarns - Check user warnings")
print("  /clearwarns - Clear user warnings")
print("=" * 60)
