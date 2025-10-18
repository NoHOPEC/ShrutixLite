from ShrutiMusic import app
from pyrogram import filters
from pyrogram.types import Message

# 🟢 Voice Chat Started
@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    await message.reply_text(
        "<b>🟢 ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʜᴀs sᴛᴀʀᴛᴇᴅ, ʟᴇᴛ's ᴠɪʙᴇ ᴛᴏɢᴇᴛʜᴇʀ 🎶</b>"
    )

# 🔴 Voice Chat Ended
@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    await message.reply_text(
        "<b>🔴 ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ, ᴛʜᴀɴᴋs ғᴏʀ ᴛʜᴇ ᴠɪʙᴇs 💫</b>"
    )

# 👥 User Invited Another User to VC
@app.on_message(filters.video_chat_members_invited)
async def vc_invite(_, message: Message):
    inviter = message.from_user
    invited = message.video_chat_members_invited.users

    if not inviter or not invited:
        return

    for user in invited:
        await message.reply_text(
            f"<b>🎧 {inviter.mention} ɪɴᴠɪᴛᴇᴅ {user.mention} ᴛᴏ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ 💞</b>"
        )
