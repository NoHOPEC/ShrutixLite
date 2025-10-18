# ShrutiMusic/plugins/edit_guardians.py
from ShrutiMusic import app
from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.utils.permissions import adminsOnly, member_permissions, SUDOERS

# -------------------- Helpers -------------------- #
async def get_group_settings(chat_id):
    """Fetch group settings from MongoDB"""
    data = await mongodb.edit_guardians.find_one({"chat_id": chat_id})
    if not data:
        data = {
            "chat_id": chat_id,
            "edit_status": False,
            "admin_edit_status": False,
            "free_edit_users": []
        }
        await mongodb.edit_guardians.insert_one(data)
    return data

async def set_group_settings(chat_id, key, value):
    """Update a single setting in group"""
    await mongodb.edit_guardians.update_one(
        {"chat_id": chat_id}, {"$set": {key: value}}, upsert=True
    )

async def add_free_edit_user(chat_id, user_id):
    await mongodb.edit_guardians.update_one(
        {"chat_id": chat_id}, {"$addToSet": {"free_edit_users": user_id}}, upsert=True
    )

async def remove_free_edit_user(chat_id, user_id):
    await mongodb.edit_guardians.update_one(
        {"chat_id": chat_id}, {"$pull": {"free_edit_users": user_id}}
    )

# -------------------- Commands -------------------- #

@app.on_message(filters.command("edit") & filters.group)
@adminsOnly("can_change_info")
async def edit_toggle(client, message: Message):
    if len(message.command) < 2 or message.command[1].lower() not in ["on", "off"]:
        return await message.reply_text("Usage: /edit on|off")
    
    status = message.command[1].lower() == "on"
    await set_group_settings(message.chat.id, "edit_status", status)
    await message.reply_text(
        f"✅ Edit protection for <b>users</b> is now {'enabled' if status else 'disabled'}."
    )

@app.on_message(filters.command("adminedit") & filters.group)
@adminsOnly("can_change_info")
async def admin_edit_toggle(client, message: Message):
    if len(message.command) < 2 or message.command[1].lower() not in ["on", "off"]:
        return await message.reply_text("Usage: /adminedit on|off")
    
    status = message.command[1].lower() == "on"
    await set_group_settings(message.chat.id, "admin_edit_status", status)
    await message.reply_text(
        f"✅ Edit protection for <b>admins</b> is now {'enabled' if status else 'disabled'}."
    )

@app.on_message(filters.command("freeedit") & filters.group)
@adminsOnly("can_change_info")
async def free_edit_user(client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "Usage: /freeedit <username|user_id> or reply to a user"
        )
    
    chat_id = message.chat.id
    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user.id
    else:
        try:
            target_user = int(message.command[1])
        except ValueError:
            user = await app.get_users(message.command[1])
            target_user = user.id

    await add_free_edit_user(chat_id, target_user)
    await message.reply_text(
        f"✅ User <b>{target_user}</b> can now freely edit messages."
    )

@app.on_message(filters.command("removefreeedit") & filters.group)
@adminsOnly("can_change_info")
async def remove_free_edit(client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "Usage: /removefreeedit <username|user_id> or reply to a user"
        )
    
    chat_id = message.chat.id
    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user.id
    else:
        try:
            target_user = int(message.command[1])
        except ValueError:
            user = await app.get_users(message.command[1])
            target_user = user.id

    await remove_free_edit_user(chat_id, target_user)
    await message.reply_text(
        f"❌ User <b>{target_user}</b> can no longer freely edit messages."
    )

# -------------------- Message Edited Handler -------------------- #
@app.on_edited_message()
async def edit_guard(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return

    settings = await get_group_settings(chat_id)

    # Free edit users are allowed
    if user_id in settings.get("free_edit_users", []):
        return

    # Check if user is admin
    permissions = await member_permissions(chat_id, user_id)
    is_admin = "can_change_info" in permissions

    # Ignore reactions and non-text edits
    if not message.text and not message.caption:
        return  # reaction or media update, ignore

    # Admin edit protection
    if is_admin and settings.get("admin_edit_status"):
        await message.delete()
        await message.reply_text(
            f"⚠️ {message.from_user.mention} your edited message was deleted because admin edits are not allowed."
        )
        return

    # Normal user edit protection
    if not is_admin and settings.get("edit_status"):
        await message.delete()
        await message.reply_text(
            f"⚠️ {message.from_user.mention} your edited message was deleted because editing is disabled for users."
        )
