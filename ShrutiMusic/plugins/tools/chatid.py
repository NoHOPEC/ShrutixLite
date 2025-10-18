from ShrutiMusic import app
from pyrogram import filters
from pyrogram.types import Message


# ID Command
@app.on_message(filters.command(["id", "chatid"]))
async def get_id(client, message: Message):
    chat = message.chat
    user_id = message.from_user.id
    msg_id = message.id
    reply = message.reply_to_message

    text = "<b>✨ ɪᴅ ɪɴғᴏ ✨</b>\n\n"
    text += f"🔹 <b>Message ID:</b> <code>{msg_id}</code>\n"
    text += f"👤 <b>Your ID:</b> <code>{user_id}</code>\n"

    # Agar /id ke baad koi username ya id diya gaya hai
    if len(message.command) == 2:
        try:
            user = message.text.split(None, 1)[1].strip()
            user_info = await client.get_users(user)
            text += f"🧾 <b>User ID:</b> <code>{user_info.id}</code>\n"
        except:
            text += "⚠️ <b>User not found</b>\n"

    # Chat ka ID (group, channel ya private)
    text += f"🌐 <b>Chat ID:</b> <code>{chat.id}</code>\n\n"

    # Agar reply kiya gaya hai
    if reply:
        text += f"💬 <b>Replied Msg ID:</b> <code>{reply.id}</code>\n"
        if reply.from_user:
            text += f"👤 <b>Replied User ID:</b> <code>{reply.from_user.id}</code>\n"
        if reply.forward_from_chat:
            text += f"📢 <b>Forwarded Chat ID:</b> <code>{reply.forward_from_chat.id}</code>\n"
        if reply.sender_chat:
            text += f"🏷 <b>Sender Chat ID:</b> <code>{reply.sender_chat.id}</code>"

    await message.reply_text(text, disable_web_page_preview=True)


__MODULE__ = "Chat ID"
__HELP__ = """
<b>📌 Chat & User ID</b>

• /id → Shows your User ID + Chat ID + Message ID.  
• /id [username|id] → Shows that user's ID.  
• Reply + /id → Shows replied user's ID & replied msg ID.  
• /chatid → Same as /id.
"""
