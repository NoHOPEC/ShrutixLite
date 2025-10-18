from typing import Dict, Union

from motor.motor_asyncio import AsyncIOMotorClient as MongoCli
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter

from config import MONGO_DB_URI
from ShrutiMusic import app

mongo = MongoCli(MONGO_DB_URI).Rankings

impdb = mongo.pretender


async def usr_data(chat_id: int, user_id: int) -> bool:
    user = await impdb.find_one({"chat_id": chat_id, "user_id": user_id})
    return bool(user)


async def get_userdata(chat_id: int, user_id: int) -> Union[Dict[str, str], None]:
    user = await impdb.find_one({"chat_id": chat_id, "user_id": user_id})
    return user


async def add_userdata(
    chat_id: int, user_id: int, username: str, first_name: str, last_name: str
):
    await impdb.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {
            "$set": {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }
        },
        upsert=True,
    )


async def check_pretender(chat_id: int) -> bool:
    chat = await impdb.find_one({"chat_id_toggle": chat_id})
    return bool(chat)


async def impo_on(chat_id: int) -> None:
    await impdb.insert_one({"chat_id_toggle": chat_id})


async def impo_off(chat_id: int) -> None:
    await impdb.delete_one({"chat_id_toggle": chat_id})


# Auto-enable pretender when bot is added to a group
@app.on_message(filters.group & filters.new_chat_members)
async def auto_enable_pretender(_, message: Message):
    if app.id in [user.id for user in message.new_chat_members]:
        chat_id = message.chat.id
        if not await check_pretender(chat_id):
            await impo_on(chat_id)
            #await message.reply(
            #    f"<b>🤖 Pretender Auto-Enabled!</b>\n\n"
            #    f"Pretender feature has been automatically enabled for this group. "
            #    f"I will monitor username and name changes.\n\n"
            #    f"Use <code>/pretender off</code> to disable."
           # )


@app.on_message(filters.group & ~filters.bot & ~filters.via_bot, group=69)
async def chk_usr(_, message: Message):
    chat_id = message.chat.id
    
    # Auto-enable pretender if not already enabled (for existing groups)
    if not await check_pretender(chat_id):
        await impo_on(chat_id)
    
    if message.sender_chat:
        return
        
    user_id = message.from_user.id
    user_data = await get_userdata(chat_id, user_id)
    
    if not user_data:
        await add_userdata(
            chat_id,
            user_id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
        )
        return

    usernamebefore = user_data.get("username", "")
    first_name = user_data.get("first_name", "")
    lastname_before = user_data.get("last_name", "")

    msg = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>\n\n"

    changes = []

    if (
        first_name != message.from_user.first_name
        and lastname_before != message.from_user.last_name
    ):
        changes.append(
            f"<b>📝 Name Changed:</b> {first_name} {lastname_before} → <b>{message.from_user.first_name} {message.from_user.last_name}</b>\n"
        )
    elif first_name != message.from_user.first_name:
        changes.append(
            f"<b>📝 First Name Changed:</b> {first_name} → <b>{message.from_user.first_name}</b>\n"
        )
    elif lastname_before != message.from_user.last_name:
        changes.append(
            f"<b>📝 Last Name Changed:</b> {lastname_before} → <b>{message.from_user.last_name}</b>\n"
        )

    if usernamebefore != message.from_user.username:
        changes.append(
            f"<b>🔗 Username Changed:</b> @{usernamebefore} → <b>@{message.from_user.username}</b>\n"
        )

    if changes:
        msg += "".join(changes)
        msg += f"\n<code>User ID: {user_id}</code>"
        await message.reply_text(msg)

    await add_userdata(
        chat_id,
        user_id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )


@app.on_message(
    filters.group & filters.command("pretender") & ~filters.bot & ~filters.via_bot
)
async def set_mataa(_, message: Message):
    admin_ids = [
        admin.user.id
        async for admin in app.get_chat_members(
            message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]
    if message.from_user.id not in admin_ids:
        return await message.reply("<b>❌ You need to be an admin to use this command.</b>")
        
    if len(message.command) == 1:
        return await message.reply(
            "<b>🔍 Pretender Commands:</b>\n\n"
            "<code>/pretender on</code> - Enable monitoring\n"
            "<code>/pretender off</code> - Disable monitoring\n"
            "<code>/pretender status</code> - Check current status"
        )
        
    chat_id = message.chat.id
    
    if message.command[1] == "on":
        cekset = await check_pretender(chat_id)
        if cekset:
            await message.reply(
                f"<b>✅ Pretender is already enabled for</b> <code>{message.chat.title}</code>"
            )
        else:
            await impo_on(chat_id)
            await message.reply(
                f"<b>✅ Successfully enabled pretender for</b> <code>{message.chat.title}</code>"
            )
            
    elif message.command[1] == "off":
        cekset = await check_pretender(chat_id)
        if not cekset:
            await message.reply(
                f"<b>❌ Pretender is already disabled for</b> <code>{message.chat.title}</code>"
            )
        else:
            await impo_off(chat_id)
            await message.reply(
                f"<b>✅ Successfully disabled pretender for</b> <code>{message.chat.title}</code>"
            )
            
    elif message.command[1] == "status":
        cekset = await check_pretender(chat_id)
        status = "<b>🟢 ENABLED</b>" if cekset else "<b>🔴 DISABLED</b>"
        await message.reply(
            f"<b>📊 Pretender Status for</b> <code>{message.chat.title}</code>\n\n"
            f"<b>Status:</b> {status}"
        )
        
    else:
        await message.reply(
            "<b>❌ Invalid command!</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/pretender on</code> - Enable\n"
            "<code>/pretender off</code> - Disable\n"
            "<code>/pretender status</code> - Check status"
        )


@app.on_message(
    filters.group & filters.command("checkuser") & ~filters.bot & ~filters.via_bot
)
async def check_user_details(_, message: Message):
    if len(message.command) != 2:
        return await message.reply("<b>❌ Usage:</b> <code>/checkuser &lt;user_id&gt;</code>")

    try:
        user_id = int(message.command[1])
    except ValueError:
        return await message.reply("<b>❌ Invalid user ID!</b>")

    chat_id = message.chat.id

    # Fetch user data from the database
    user_data = await get_userdata(chat_id, user_id)
    if not user_data:
        return await message.reply(f"<b>❌ No data found for user ID:</b> <code>{user_id}</code>")

    # Extract old data from the database
    old_username = user_data.get("username", "N/A")
    old_first_name = user_data.get("first_name", "N/A")
    old_last_name = user_data.get("last_name", "N/A")

    # Fetch current data
    try:
        current_user = await app.get_users(user_id)
        new_username = current_user.username or "N/A"
        new_first_name = current_user.first_name or "N/A"
        new_last_name = current_user.last_name or "N/A"
    except:
        return await message.reply(f"<b>❌ Could not fetch current data for user ID:</b> <code>{user_id}</code>")

    # Generate response message
    msg = (
        f"<b>👤 User Details</b>\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        
        f"<b>📁 Old Data:</b>\n"
        f"• <b>Username:</b> @{old_username}\n"
        f"• <b>First Name:</b> {old_first_name}\n"
        f"• <b>Last Name:</b> {old_last_name}\n\n"
        
        f"<b>🔄 Current Data:</b>\n"
        f"• <b>Username:</b> @{new_username}\n"
        f"• <b>First Name:</b> {new_first_name}\n"
        f"• <b>Last Name:</b> {new_last_name}\n"
    )

    # Check for changes
    changes = []
    if old_username != new_username:
        changes.append(
            f"• <b>Username:</b> @{old_username} → @{new_username}\n"
        )
    if old_first_name != new_first_name:
        changes.append(
            f"• <b>First Name:</b> {old_first_name} → {new_first_name}\n"
        )
    if old_last_name != new_last_name:
        changes.append(
            f"• <b>Last Name:</b> {old_last_name} → {new_last_name}\n"
        )

    # Add changes to the message
    if changes:
        msg += f"\n<b>📈 Changes Detected:</b>\n" + "".join(changes)
    else:
        msg += f"\n<b>✅ No changes detected.</b>"

    await message.reply(msg)


__MODULE__ = "Pretender"
__HELP__ = """
<b>🔍 Pretender Monitoring System</b>

<i>Automatically detects when users change their username, first name, or last name.</i>

<b>Commands:</b>
• <code>/pretender on</code> - Enable monitoring
• <code>/pretender off</code> - Disable monitoring  
• <code>/pretender status</code> - Check current status
• <code>/checkuser &lt;user_id&gt;</code> - Check user's name history

<b>Note:</b> Pretender is automatically enabled when bot is added to a group.
"""
