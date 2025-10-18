import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic import app
from ShrutiMusic.utils.permissions import adminsOnly

# Global dictionary to track active chats for all tagging types
active_chats = {}

# Message templates for different times of day
GM_MESSAGES = [
    "➠ <b>ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ᴋᴇsᴇ ʜᴏ 🐱</b>\n\n{mention}",
    "➠ <b>ɢᴍ, sᴜʙʜᴀ ʜᴏ ɢʏɪ ᴜᴛʜɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ 🌤️</b>\n\n{mention}",
    "➠ <b>ɢᴍ ʙᴀʙʏ, ᴄʜᴀɪ ᴘɪ ʟᴏ ☕</b>\n\n{mention}",
    "➠ <b>ᴊᴀʟᴅɪ ᴜᴛʜᴏ, sᴄʜᴏᴏʟ ɴᴀʜɪ ᴊᴀɴᴀ ᴋʏᴀ 🏫</b>\n\n{mention}",
    "➠ <b>ɢᴍ, ᴄʜᴜᴘ ᴄʜᴀᴘ ʙɪsᴛᴇʀ sᴇ ᴜᴛʜᴏ ᴠʀɴᴀ ᴘᴀɴɪ ᴅᴀʟ ᴅᴜɴɢɪ 🧊</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ᴜᴛʜᴏ ᴀᴜʀ ᴊᴀʟᴅɪ ғʀᴇsʜ ʜᴏ ᴊᴀᴏ, ɴᴀsᴛᴀ ʀᴇᴀᴅʏ ʜᴀɪ 🫕</b>\n\n{mention}",
    "➠ <b>ᴏғғɪᴄᴇ ɴᴀʜɪ ᴊᴀɴᴀ ᴋʏᴀ ᴊɪ ᴀᴀᴊ, ᴀʙʜɪ ᴛᴀᴋ ᴜᴛʜᴇ ɴᴀʜɪ 🏣</b>\n\n{mention}",
    "➠ <b>ɢᴍ ᴅᴏsᴛ, ᴄᴏғғᴇᴇ/ᴛᴇᴀ ᴋʏᴀ ʟᴏɢᴇ ☕🍵</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ 8 ʙᴀᴊɴᴇ ᴡᴀʟᴇ ʜᴀɪ, ᴀᴜʀ ᴛᴜᴍ ᴀʙʜɪ ᴛᴋ ᴜᴛʜᴇ ɴᴀʜɪ 🕖</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ʜᴀᴠᴇ ᴀ ɴɪᴄᴇ ᴅᴀʏ... 🌄</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ʜᴀᴠᴇ ᴀ ɢᴏᴏᴅ ᴅᴀʏ... 🪴</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ ʙᴀʙʏ 😇</b>\n\n{mention}",
    "➠ <b>ᴍᴜᴍᴍʏ ᴅᴇᴋʜᴏ ʏᴇ ɴᴀʟᴀʏᴋ ᴀʙʜɪ ᴛᴀᴋ sᴏ ʀʜᴀ ʜᴀɪ... 😵‍💫</b>\n\n{mention}",
    "➠ <b>ʀᴀᴀᴛ ʙʜᴀʀ ʙᴀʙᴜ sᴏɴᴀ ᴋʀ ʀʜᴇ ᴛʜᴇ ᴋʏᴀ, ᴊᴏ ᴀʙʜɪ ᴛᴋ sᴏ ʀʜᴇ ʜᴏ ᴜᴛʜɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ... 😏</b>\n\n{mention}",
    "➠ <b>ʙᴀʙᴜ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴜᴛʜ ᴊᴀᴏ ᴀᴜʀ ɢʀᴏᴜᴘ ᴍᴇ sᴀʙ ғʀɪᴇɴᴅs ᴋᴏ ɢᴍ ᴡɪsʜ ᴋʀᴏ... 🌟</b>\n\n{mention}",
    "➠ <b>ᴘᴀᴘᴀ ʏᴇ ᴀʙʜɪ ᴛᴀᴋ ᴜᴛʜ ɴᴀʜɪ, sᴄʜᴏᴏʟ ᴋᴀ ᴛɪᴍᴇ ɴɪᴋᴀʟᴛᴀ ᴊᴀ ʀʜᴀ ʜᴀɪ... 🥲</b>\n\n{mention}",
    "➠ <b>ᴊᴀɴᴇᴍᴀɴ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ᴋʏᴀ ᴋʀ ʀʜᴇ ʜᴏ ... 😅</b>\n\n{mention}",
    "➠ <b>ɢᴍ ʙᴇᴀsᴛɪᴇ, ʙʀᴇᴀᴋғᴀsᴛ ʜᴜᴀ ᴋʏᴀ... 🍳</b>\n\n{mention}"
]

GA_MESSAGES = [
    "➠ <b>ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ, ʟᴜɴᴄʜ ʜᴏ ɢʏᴀ 🍽️</b>\n\n{mention}",
    "➠ <b>ɢᴀ, ᴅᴏᴘʜᴀʀ ʜᴏ ɢʏɪ ʜᴀɪ, ᴀᴀʀᴀᴍ ᴋᴀʀ ʟᴏ 😴</b>\n\n{mention}",
    "➠ <b>ᴀғᴛᴇʀɴᴏᴏɴ ᴍᴇʀɪ ᴊᴀᴀɴ, ᴄʜᴀɪ ᴘᴇᴇɴᴇ ᴄʜᴀʟᴏ ☕</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ 🌞</b>\n\n{mention}",
    "➠ <b>ᴅᴏᴘʜᴀʀ ᴋɪ ᴅʜᴜᴘ ᴍᴇɪɴ ᴊᴀɢᴛᴇ ʀʜᴏ, ɴᴀʜɪ ᴛᴏ sᴏʟᴀʀ ᴇᴄʟɪᴘsᴇ ʜᴏ ᴊᴀʏᴇɢᴀ ☀️</b>\n\n{mention}",
    "➠ <b>ɢᴀ ғʀɪᴇɴᴅ, ᴋʏᴀ ᴋᴀʀ ʀʜᴇ ʜᴏ 😊</b>\n\n{mention}",
    "➠ <b>ᴀᴀᴊ ᴋᴀ ᴋᴀᴍ ᴋʜᴀᴛᴍ ʜᴏ ɢʏᴀ ᴋʏᴀ, ᴊᴀʙ ᴛᴀᴋ ɴʜɪ ʜᴜᴀ ᴛᴀʙ ᴛᴀᴋ ᴋᴀʀᴏ 💼</b>\n\n{mention}",
    "➠ <b>ʟᴜɴᴄʜ ᴍᴇɪɴ ᴋʏᴀ ʙᴀɴᴀʏᴀ ᴀᴀᴊ, ᴍᴜᴊʜᴇ ʙʜɪ ʙᴀᴛᴀᴏ 🍲</b>\n\n{mention}",
    "➠ <b>ᴀғᴛᴇʀɴᴏᴏɴ sɴᴀᴄᴋs ᴛɪᴍᴇ, ᴋᴜᴄʜ ᴋʜᴀʏᴀ ᴋʏᴀ 🍪</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ ʜᴀᴠᴇ ᴀ ɢʀᴇᴀᴛ ᴅᴀʏ 🌻</b>\n\n{mention}",
    "➠ <b>ᴄʜᴀɪ ᴘᴇᴇᴛᴇ ʜᴜᴇ ʙᴀᴀᴛᴇɪɴ ᴋᴀʀᴛᴇ ʜᴀɪɴ, ᴀᴀᴏ ɢʀᴏᴜᴘ ᴍᴇɪɴ ☕</b>\n\n{mention}",
    "➠ <b>ᴅᴏᴘʜᴀʀ ᴋɪ ᴄʜᴜᴛᴛɪ ʜᴏ ɢʏɪ ᴋʏᴀ, ᴛʜᴏᴅᴀ ᴀᴀʀᴀᴍ ᴋᴀʀ ʟᴏ 😌</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ɢᴀ, ɴᴀᴘ ᴛɪᴍᴇ ʜᴏ ɢʏɪ ʜᴀɪ 😴</b>\n\n{mention}",
    "➠ <b>ᴀᴀᴊ ᴋɪ ᴅᴏᴘʜᴀʀ ʙʜᴜᴛ ɢᴀʀᴍ ʜᴀɪ, ᴀᴄ ᴏɴ ᴋᴀʀ ʟᴏ ❄️</b>\n\n{mention}",
    "➠ <b>ɢᴀ ᴅᴇᴀʀ, ᴋᴀɪsᴇ ʜᴏ ᴀᴀᴊ 💖</b>\n\n{mention}",
    "➠ <b>ᴀғᴛᴇʀɴᴏᴏɴ ᴡᴀʟᴋ ᴘᴇ ᴄʜᴀʟᴇɴɢᴇ, ᴛʜᴏᴅɪ ᴅʜᴜᴘ sᴇᴋᴇɴɢᴇ 🌳</b>\n\n{mention}"
]

GN_MESSAGES = [
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ 🌚</b>\n\n{mention}",
    "➠ <b>ᴄʜᴜᴘ ᴄʜᴀᴘ sᴏ ᴊᴀ 🙊</b>\n\n{mention}",
    "➠ <b>ᴘʜᴏɴᴇ ʀᴀᴋʜ ᴋᴀʀ sᴏ ᴊᴀ, ɴᴀʜɪ ᴛᴏ ʙʜᴏᴏᴛ ᴀᴀ ᴊᴀʏᴇɢᴀ..👻</b>\n\n{mention}",
    "➠ <b>ᴀᴡᴇᴇ ʙᴀʙᴜ sᴏɴᴀ ᴅɪɴ ᴍᴇɪɴ ᴋᴀʀ ʟᴇɴᴀ ᴀʙʜɪ sᴏ ᴊᴀᴏ..?? 🥲</b>\n\n{mention}",
    "➠ <b>ᴍᴜᴍᴍʏ ᴅᴇᴋʜᴏ ʏᴇ ᴀᴘɴᴇ ɢғ sᴇ ʙᴀᴀᴛ ᴋʀ ʀʜᴀ ʜ ʀᴀᴊᴀɪ ᴍᴇ ɢʜᴜs ᴋᴀʀ, sᴏ ɴᴀʜɪ ʀᴀʜᴀ 😜</b>\n\n{mention}",
    "➠ <b>ᴘᴀᴘᴀ ʏᴇ ᴅᴇᴋʜᴏ ᴀᴘɴᴇ ʙᴇᴛᴇ ᴋᴏ ʀᴀᴀᴛ ʙʜᴀʀ ᴘʜᴏɴᴇ ᴄʜᴀʟᴀ ʀʜᴀ ʜᴀɪ 🤭</b>\n\n{mention}",
    "➠ <b>ɢɴ sᴅ ᴛᴄ.. 🙂</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ sᴡᴇᴇᴛ ᴅʀᴇᴀᴍ ᴛᴀᴋᴇ ᴄᴀʀᴇ..?? ✨</b>\n\n{mention}",
    "➠ <b>ʀᴀᴀᴛ ʙʜᴜᴛ ʜᴏ ɢʏɪ ʜᴀɪ sᴏ ᴊᴀᴏ, ɢɴ..?? 🌌</b>\n\n{mention}",
    "➠ <b>ᴍᴜᴍᴍʏ ᴅᴇᴋʜᴏ 11 ʙᴀᴊɴᴇ ᴡᴀʟᴇ ʜᴀɪ ʏᴇ ᴀʙʜɪ ᴛᴀᴋ ᴘʜᴏɴᴇ ᴄʜᴀʟᴀ ʀʜᴀ ɴᴀʜɪ sᴏ ɴᴀʜɪ ʀᴀʜᴀ 🕦</b>\n\n{mention}",
    "➠ <b>ᴋᴀʟ sᴜʙʜᴀ sᴄʜᴏᴏʟ ɴᴀʜɪ ᴊᴀɴᴀ ᴋʏᴀ, ᴊᴏ ᴀʙʜɪ ᴛᴀᴋ ᴊᴀɢ ʀʜᴇ ʜᴏ 🏫</b>\n\n{mention}",
    "➠ <b>ʙᴀʙᴜ, ɢᴏᴏᴅ ɴɪɢʜᴛ sᴅ ᴛᴄ..?? 😊</b>\n\n{mention}",
    "➠ <b>ᴀᴀᴊ ʙʜᴜᴛ ᴛʜᴀɴᴅ ʜᴀɪ, ᴀᴀʀᴀᴍ sᴇ ᴊᴀʟᴅɪ sᴏ ᴊᴀᴛɪ ʜᴏᴏɴ 🌼</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ 🌷</b>\n\n{mention}",
    "➠ <b>ᴍᴇ ᴊᴀ ʀᴀʜɪ sᴏɴᴇ, ɢɴ sᴅ ᴛᴄ 🏵️</b>\n\n{mention}",
    "➠ <b>ʜᴇʟʟᴏ ᴊɪ ɴᴀᴍᴀsᴛᴇ, ɢᴏᴏᴅ ɴɪɢʜᴛ 🍃</b>\n\n{mention}",
    "➠ <b>ʜᴇʏ, ᴋᴋʀʜ..? sᴏɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ ☃️</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ ᴊɪ, ʙʜᴜᴛ ʀᴀᴀᴛ ʜᴏ ɢʏɪ..? ⛄</b>\n\n{mention}",
    "➠ <b>ᴍᴇ ᴊᴀ ʀᴀʜɪ ʀᴏɴᴇ, ɪ ᴍᴇᴀɴ sᴏɴᴇ ɢᴏᴏᴅ ɴɪɢʜᴛ ᴊɪ 😁</b>\n\n{mention}",
    "➠ <b>ᴍᴀᴄʜʜᴀʟɪ ᴋᴏ ᴋᴇʜᴛᴇ ʜᴀɪ ғɪsʜ, ɢᴏᴏᴅ ɴɪɢʜᴛ ᴅᴇᴀʀ ᴍᴀᴛ ᴋʀɴᴀ ᴍɪss, ᴊᴀ ʀʜɪ sᴏɴᴇ 🌄</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ ʙʀɪɢʜᴛғᴜʟʟ ɴɪɢʜᴛ 🤭</b>\n\n{mention}",
    "➠ <b>ᴛʜᴇ ɴɪɢʜᴛ ʜᴀs ғᴀʟʟᴇɴ, ᴛʜᴇ ᴅᴀʏ ɪs ᴅᴏɴᴇ,, ᴛʜᴇ ᴍᴏᴏɴ ʜᴀs ᴛᴀᴋᴇɴ ᴛʜᴇ ᴘʟᴀᴄᴇ ᴏғ ᴛʜᴇ sᴜɴ... 😊</b>\n\n{mention}",
    "➠ <b>ᴍᴀʏ ᴀʟʟ ʏᴏᴜʀ ᴅʀᴇᴀᴍs ᴄᴏᴍᴇ ᴛʀᴜᴇ ❤️</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ sᴘʀɪɴᴋʟᴇs sᴡᴇᴇᴛ ᴅʀᴇᴀᴍ 💚</b>\n\n{mention}",
    "➠ <b>ɢᴏᴏᴅ ɴɪɢʜᴛ, ɴɪɴᴅ ᴀᴀ ʀʜɪ ʜᴀɪ 🥱</b>\n\n{mention}",
    "➠ <b>ᴅᴇᴀʀ ғʀɪᴇɴᴅ ɢᴏᴏᴅ ɴɪɢʜᴛ 💤</b>\n\n{mention}",
    "➠ <b>ɪᴛɴɪ ʀᴀᴀᴛ ᴍᴇ ᴊᴀɢ ᴋᴀʀ ᴋʏᴀ ᴋᴀʀ ʀʜᴇ ʜᴏ sᴏɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ 😜</b>\n\n{mention}",
    "➠ <b>ᴄʟᴏsᴇ ʏᴏᴜʀ ᴇʏᴇs sɴᴜɢɢʟᴇ ᴜᴘ ᴛɪɢʜᴛ,, ᴀɴᴅ ʀᴇᴍᴇᴍʙᴇʀ ᴛʜᴀᴛ ᴀɴɢᴇʟs, ᴡɪʟʟ ᴡᴀᴛᴄʜ ᴏᴠᴇʀ ʏᴏᴜ ᴛᴏɴɪɢʜᴛ... 💫</b>\n\n{mention}"
]

VC_MESSAGES = [
    "➠ <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴋᴀʀʟᴏ ʏᴀᴀʀᴏ, ʙᴏʀᴇ ʜᴏ ʀʜᴇ ʜᴏɴɢᴇ 🎙️</b>\n\n{mention}",
    "➠ <b>ᴠᴄ ᴘᴇ ᴀᴀᴏ ɴᴀ, ɢᴀɴᴇ sᴜɴᴀᴛᴇ ʜᴀɪɴ 🎵</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ᴠᴄ ᴘᴇ ᴀᴀᴏ, ʙᴀᴀᴛᴇɪɴ ᴋᴀʀᴇɴɢᴇ 💬</b>\n\n{mention}",
    "➠ <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴍᴇ ᴊᴏɪɴ ᴋᴀʀᴏ, ᴍᴀᴢᴀ ᴀᴀ ʏᴀᴇɢᴀ 🎧</b>\n\n{mention}",
    "➠ <b>ᴠᴄ ᴘᴇ ᴀᴀᴊᴀᴏ, ɢᴀᴍᴇ ᴋʜᴇʟᴛᴇ ʜᴀɪɴ 🎮</b>\n\n{mention}",
    "➠ <b>ʏᴀᴀʀ ᴠᴄ ᴘᴇ ᴀᴀᴏ ɴᴀ, ʙᴏʀᴇ ʜᴏ ʀʜᴇ ʜᴀɪɴ 😴</b>\n\n{mention}",
    "➠ <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴍᴇ ᴊᴏɪɴ ᴋᴀʀᴏ, sᴏɴɢ ʀᴇǫᴜᴇsᴛ ʟᴇᴛᴇ ʜᴀɪɴ 🎶</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ᴠᴄ ᴘᴇ ᴀᴀᴏ, ᴍᴜᴊʜᴇ ᴛᴀɢ ᴋᴀʀᴏ 🤗</b>\n\n{mention}",
    "➠ <b>ᴠᴄ ᴘᴇ ᴀᴀᴊᴀᴏ, ɢʀᴏᴜᴘ ᴋᴏ ʟɪᴠᴇ ᴋᴀʀᴛᴇ ʜᴀɪɴ 🔴</b>\n\n{mention}",
    "➠ <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴍᴇ ᴊᴏɪɴ ᴋᴀʀᴏ, sᴛᴏʀʏ ᴛɪᴍᴇ 📖</b>\n\n{mention}",
    "➠ <b>ʏᴀᴀʀ ᴠᴄ ᴘᴇ ᴀᴀᴏ, ɢᴜᴘ sʜᴜᴘ ᴋᴀʀᴛᴇ ʜᴀɪɴ 🤫</b>\n\n{mention}",
    "➠ <b>ᴠᴄ ᴘᴇ ᴀᴀᴊᴀᴏ, ᴍᴇᴍᴇs sʜᴀʀᴇ ᴋᴀʀᴛᴇ ʜᴀɪɴ 😂</b>\n\n{mention}",
    "➠ <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴍᴇ ᴊᴏɪɴ ᴋᴀʀᴏ, ɢʀᴏᴜᴘ ᴄᴀʟʟ ʜᴏ ʀʜɪ ʜᴀɪ 📞</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ᴠᴄ ᴘᴇ ᴀᴀᴏ, sɪɴɢɪɴɢ sᴇssɪᴏɴ ʜᴀɪ 🎤</b>\n\n{mention}",
    "➠ <b>ᴠᴄ ᴘᴇ ᴀᴀᴊᴀᴏ, ʙᴀᴀᴛᴇɪɴ ʜᴏ ʀʜɪ ʜᴀɪɴ ᴍᴀsᴛ 💃</b>\n\n{mention}",
    "➠ <b>ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴍᴇ ᴊᴏɪɴ ᴋᴀʀᴏ, ɴᴇᴡ ғʀɪᴇɴᴅs ʙᴀɴᴀᴛᴇ ʜᴀɪɴ 👥</b>\n\n{mention}"
]

RANDOM_MESSAGES = [
    "➠ <b>ʜᴇʏ, ᴋʏᴀ ʜᴀᴀʟ ʜᴀɪ 😊</b>\n\n{mention}",
    "➠ <b>ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ ᴅᴏɪɴɢ ᴛᴏᴅᴀʏ? 🌟</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ, ᴊᴀɢ ʀᴀʜᴇ ʜᴏ ᴋʏᴀ? 😇</b>\n\n{mention}",
    "➠ <b>ᴋʏᴀ ᴄʜᴀʟ ʀʜᴀ ʜᴀɪ ʙʀᴏ? 🤔</b>\n\n{mention}",
    "➠ <b>ᴛᴀɢ ʜᴏ ɢʏᴇ ʜᴏ ᴀᴀᴘ, ʀᴇᴘʟʏ ᴛᴏ ᴅᴏ 🎯</b>\n\n{mention}",
    "➠ <b>ʜᴇʟʟᴏ ᴊɪ ɴᴀᴍᴀsᴛᴇ, ᴋᴀɪsᴇ ʜᴏ? 🙏</b>\n\n{mention}",
    "➠ <b>ʏᴏ ᴍʏ ғʀɪᴇɴᴅ, ʜᴏᴡ's ɪᴛ ɢᴏɪɴɢ? 👋</b>\n\n{mention}",
    "➠ <b>ᴀᴀᴘᴋᴏ ᴛᴀɢ ᴋᴀʀɴᴇ ᴋᴀ ᴛɪᴍᴇ ᴀᴀ ɢʏᴀ ʜᴀɪ ⏰</b>\n\n{mention}",
    "➠ <b>ʙᴀʙʏ ʀᴇᴘʟʏ ᴛᴏ ᴅᴏ, ʙᴏʀᴇ ʜᴏ ʀʜᴇ ʜᴏɴɢᴇ 😉</b>\n\n{mention}",
    "➠ <b>ᴊᴀɴᴇᴍᴀɴ, ᴋʏᴀ ᴋᴀʀ ʀʜᴇ ʜᴏ? 💖</b>\n\n{mention}",
    "➠ <b>ʜᴇʏ ᴛʜᴇʀᴇ, ʟᴇᴛ's ᴄʜᴀᴛ! 💬</b>\n\n{mention}",
    "➠ <b>ᴛᴀɢ ʜᴏ ɢʏᴇ, ᴀʙ ʀᴇᴘʟʏ ᴋᴀʀᴏ 🎁</b>\n\n{mention}",
    "➠ <b>ʙʀᴏ, ᴊᴀɢ ᴋᴇ ᴋʏᴀ ᴋᴀʀ ʀʜᴇ ʜᴏ? 🤗</b>\n\n{mention}",
    "➠ <b>ʜᴇʟʟᴏ ʙᴇᴀᴜᴛɪғᴜʟ, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ? 🌸</b>\n\n{mention}",
    "➠ <b>ʏᴀᴀʀ ᴛᴜᴍʜᴇ ᴛᴀɢ ᴋᴀʀɴᴀ ʜɪ ᴘᴀᴅᴛᴀ ʜᴀɪ ❤️</b>\n\n{mention}",
    "➠ <b>ᴛᴀɢ ʜᴏ ɢʏᴇ, ᴀʙ ʙᴀᴛᴀᴏ ᴋʏᴀ ᴄʜᴀʟ ʀʜᴀ ʜᴀɪ? 🚀</b>\n\n{mention}"
]

# Helper function to get all non-bot, non-deleted users from a chat
async def get_chat_users(chat_id):
    """Get all valid users from a chat (excluding bots and deleted accounts)"""
    users = []
    async for member in app.get_chat_members(chat_id):
        if member.user.is_bot or member.user.is_deleted:
            continue
        users.append(member.user)
    return users

# Generic tagging function - Modified to tag one user at a time
async def tag_users(chat_id, messages, tag_type):
    """Generic function to tag users one by one with specified messages"""
    users = await get_chat_users(chat_id)
    
    for user in users:
        # Check if tagging was stopped
        if chat_id not in active_chats:
            break
            
        # Create bold mention for single user
        mention = f"<b><a href='tg://user?id={user.id}'>{user.first_name}</a></b>"
        msg = random.choice(messages).format(mention=mention)
        
        # HTML formatting will be applied automatically due to default setting
        await app.send_message(chat_id, msg, disable_web_page_preview=True)
        await asyncio.sleep(3)  # 3 second delay between each user
    
    # Clean up and send completion message
    active_chats.pop(chat_id, None)
    await app.send_message(chat_id, f"✅ <b>{tag_type} Tᴀɢɢɪɴɢ Dᴏɴᴇ!</b>")

# =================== GOOD MORNING COMMANDS ===================

@app.on_message(filters.command("gmtag") & filters.group)
@adminsOnly("can_delete_messages")
async def gmtag(_, message: Message):
    """Start Good Morning tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        return await message.reply("⚠️ <b>Gᴏᴏᴅ Mᴏʀɴɪɴɢ Tᴀɢɢɪɴɢ Aʟʀᴇᴀᴅʏ Rᴜɴɴɪɴɢ.</b>")
    
    active_chats[chat_id] = True
    await message.reply("☀️ <b>Gᴏᴏᴅ Mᴏʀɴɪɴɢ Tᴀɢɢɪɴɢ Sᴛᴀʀᴛᴇᴅ...</b>")
    
    await tag_users(chat_id, GM_MESSAGES, "Gᴏᴏᴅ Mᴏʀɴɪɴɢ")

@app.on_message(filters.command("gmstop") & filters.group)
@adminsOnly("can_delete_messages")
async def gmstop(_, message: Message):
    """Stop Good Morning tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        del active_chats[chat_id]
        await message.reply("🛑 <b>Gᴏᴏᴅ Mᴏʀɴɪɴɢ Tᴀɢɢɪɴɢ Sᴛᴏᴘᴘᴇᴅ.</b>")
    else:
        await message.reply("❌ <b>Nᴏᴛʜɪɴɢ Rᴜɴɴɪɴɢ.</b>")

# =================== GOOD AFTERNOON COMMANDS ===================

@app.on_message(filters.command("gatag") & filters.group)
@adminsOnly("can_delete_messages")
async def gatag(_, message: Message):
    """Start Good Afternoon tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        return await message.reply("⚠️ <b>Aғᴛᴇʀɴᴏᴏɴ Tᴀɢɢɪɴɢ Aʟʀᴇᴀᴅʏ Oɴ.</b>")
    
    active_chats[chat_id] = True
    await message.reply("☀️ <b>Aғᴛᴇʀɴᴏᴏɴ Tᴀɢɢɪɴɢ Sᴛᴀʀᴛᴇᴅ...</b>")
    
    await tag_users(chat_id, GA_MESSAGES, "Aғᴛᴇʀɴᴏᴏɴ")

@app.on_message(filters.command("gastop") & filters.group)
@adminsOnly("can_delete_messages")
async def gastop(_, message: Message):
    """Stop Good Afternoon tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        del active_chats[chat_id]
        await message.reply("🛑 <b>Aғᴛᴇʀɴᴏᴏɴ Tᴀɢɢɪɴɢ Sᴛᴏᴘᴘᴇᴅ.</b>")
    else:
        await message.reply("❌ <b>Nᴏᴛʜɪɴɢ Rᴜɴɴɪɴɢ.</b>")

# =================== GOOD NIGHT COMMANDS ===================

@app.on_message(filters.command("gntag") & filters.group)
@adminsOnly("can_delete_messages")
async def gntag(_, message: Message):
    """Start Good Night tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        return await message.reply("⚠️ <b>Nɪɢʜᴛ Tᴀɢɢɪɴɢ Aʟʀᴇᴀᴅʏ Oɴ.</b>")
    
    active_chats[chat_id] = True
    await message.reply("🌙 <b>Nɪɢʜᴛ Tᴀɢɢɪɴɢ Sᴛᴀʀᴛᴇᴅ...</b>")
    
    await tag_users(chat_id, GN_MESSAGES, "Gᴏᴏᴅ Nɪɢʜᴛ")

@app.on_message(filters.command("gnstop") & filters.group)
@adminsOnly("can_delete_messages")
async def gnstop(_, message: Message):
    """Stop Good Night tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        del active_chats[chat_id]
        await message.reply("🛑 <b>Nɪɢʜᴛ Tᴀɢɢɪɴɢ Sᴛᴏᴘᴘᴇᴅ.</b>")
    else:
        await message.reply("❌ <b>Nᴏᴛʜɪɴɢ Rᴜɴɴɪɴɢ.</b>")

# =================== VC TAG COMMANDS ===================

@app.on_message(filters.command("vctag") & filters.group)
@adminsOnly("can_delete_messages")
async def vctag(_, message: Message):
    """Start VC tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        return await message.reply("⚠️ <b>VC Tᴀɢɢɪɴɢ Aʟʀᴇᴀᴅʏ Rᴜɴɴɪɴɢ.</b>")
    
    active_chats[chat_id] = True
    await message.reply("🎙️ <b>VC Tᴀɢɢɪɴɢ Sᴛᴀʀᴛᴇᴅ...</b>")
    
    await tag_users(chat_id, VC_MESSAGES, "VC")

@app.on_message(filters.command("vcstop") & filters.group)
@adminsOnly("can_delete_messages")
async def vcstop(_, message: Message):
    """Stop VC tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        del active_chats[chat_id]
        await message.reply("🛑 <b>VC Tᴀɢɢɪɴɢ Sᴛᴏᴘᴘᴇᴅ.</b>")
    else:
        await message.reply("❌ <b>Nᴏᴛʜɪɴɢ Rᴜɴɴɪɴɢ.</b>")

# =================== RANDOM TAG COMMANDS ===================

@app.on_message(filters.command("randtag") & filters.group)
@adminsOnly("can_delete_messages")
async def randtag(_, message: Message):
    """Start Random tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        return await message.reply("⚠️ <b>Rᴀɴᴅᴏᴍ Tᴀɢɢɪɴɢ Aʟʀᴇᴀᴅʏ Rᴜɴɴɪɴɢ.</b>")
    
    active_chats[chat_id] = True
    await message.reply("🎲 <b>Rᴀɴᴅᴏᴍ Tᴀɢɢɪɴɢ Sᴛᴀʀᴛᴇᴅ...</b>")
    
    await tag_users(chat_id, RANDOM_MESSAGES, "Rᴀɴᴅᴏᴍ")

@app.on_message(filters.command("randstop") & filters.group)
@adminsOnly("can_delete_messages")
async def randstop(_, message: Message):
    """Stop Random tagging"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        del active_chats[chat_id]
        await message.reply("🛑 <b>Rᴀɴᴅᴏᴍ Tᴀɢɢɪɴɢ Sᴛᴏᴘᴘᴇᴅ.</b>")
    else:
        await message.reply("❌ <b>Nᴏᴛʜɪɴɢ Rᴜɴɴɪɴɢ.</b>")

# =================== UTILITY COMMANDS ===================

@app.on_message(filters.command("stopall") & filters.group)
@adminsOnly("can_delete_messages")
async def stopall(_, message: Message):
    """Stop all active tagging in current chat"""
    chat_id = message.chat.id
    
    if chat_id in active_chats:
        del active_chats[chat_id]
        await message.reply("🛑 <b>Aʟʟ Tᴀɢɢɪɴɢ Sᴛᴏᴘᴘᴇᴅ.</b>")
    else:
        await message.reply("❌ <b>Nᴏ Aᴄᴛɪᴠᴇ Tᴀɢɢɪɴɢ Fᴏᴜɴᴅ.</b>")

@app.on_message(filters.command("taghelp") & (filters.private | filters.group))
async def taghelp(_, message: Message):
    """Show help message for tagging commands"""
    help_text = """
🏷️ <b>Tagging Commands Help</b>

🌻 /gmtag - Start Good Morning tagging
🛑 /gmstop - Stop Good Morning tagging

☀️ /gatag - Start Good Afternoon tagging
🚫 /gastop - Stop Good Afternoon tagging

🌟 /gntag - Start Good Night tagging
⏹️ /gnstop - Stop Good Night tagging

🎤 /vctag - Start VC tagging
⏹️ /vcstop - Stop VC tagging

🎲 /randtag - Start Random tagging
⏹️ /randstop - Stop Random tagging

🛠️ /stopall - Stop all active tagging
📄 /taghelp - Show this help message

<b>Note:</b> Only admins with <code>can_delete_messages</code> permission can use these commands.
"""
    await message.reply(help_text)


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================

# ❤️ Love From ShrutiBots
