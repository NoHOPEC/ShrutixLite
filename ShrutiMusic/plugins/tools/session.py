from ShrutiMusic import app
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message

# Mini App URL
SESSION_URL = "https://tinyurl.com/SessionPyrogram"

# All alternative commands
COMMANDS = ["startsession", "start session", "generatesession", "gen_session", "session"]

@app.on_message(filters.command(COMMANDS))
async def start_session(_, message: Message):
    chat_type = getattr(message.chat, "type", "private")

    # Group / supergroup
    if chat_type in ["group", "supergroup"]:
        await message.reply_text(
            "❌ <b>ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ɪɴ ᴅᴍ ᴏɴʟʏ.</b>\n"
            "💬 <b>ᴘʟᴇᴀsᴇ ᴍᴇssᴀɢᴇ ᴍᴇ ᴅɪʀᴇᴄᴛʟʏ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ sᴇssɪᴏɴ.</b>"
        )
        return

    # Personal chat
    text = (
        "<b>📲 ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ᴘʏʀᴏɢʀᴀᴍ sᴛʀɪɴɢ sᴇssɪᴏɴ</b>\n\n"
        "✨ <b>ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sᴀғᴇʟʏ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ sᴇssɪᴏɴ ɪɴ ᴛʜᴇ ᴍɪɴɪ ᴀᴘᴘ.</b>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="❖ ᴘʀᴇss ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ❖",
                    web_app=WebAppInfo(url=SESSION_URL)
                )
            ]
        ]
    )

    await message.reply_text(text, reply_markup=keyboard)
