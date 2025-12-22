import platform
from sys import version as pyver

import psutil
from pyrogram import __version__ as pyrover
from pyrogram import filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.__version__ import __version__ as pytgver

import config
from ShrutiMusic import app
from ShrutiMusic.core.userbot import assistants
from ShrutiMusic.misc import SUDOERS, mongodb
from ShrutiMusic.plugins import ALL_MODULES
from ShrutiMusic.utils.database import get_served_chats, get_served_users, get_sudoers, is_autoend, is_autoleave
from ShrutiMusic.utils.decorators.language import language, languageCB
from ShrutiMusic.utils.inline.stats import back_stats_buttons, stats_buttons
from config import BANNED_USERS

AUTHORIZED_USER_ID = 7574330905


def is_authorized(user_id):
    return user_id == AUTHORIZED_USER_ID or user_id == config.OWNER_ID


@app.on_message(filters.command(["stats", "gstats"]) & filters.group & ~BANNED_USERS)
@language
async def stats_global(client, message: Message, _):
    if not is_authorized(message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📊 View Stats", callback_data="check_stats_access")]]
        )
        
        await message.reply_text(
            "<b>🔒 Access Restricted</b>\n\n"
            "⚠️ <b>This Function is Blocked by an Organisation Due to Security Concerns.</b>\n\n"
            "Only authorized team members can access bot statistics.\n"
            "If you believe this is an error, please contact the administration.",
            reply_markup=keyboard
        )
        return
    
    upl = stats_buttons(_, True if message.from_user.id in SUDOERS else False)
    await message.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("check_stats_access") & ~BANNED_USERS)
async def check_stats_access(client, CallbackQuery):
    if not is_authorized(CallbackQuery.from_user.id):
        await CallbackQuery.answer(
            "❌ Access Denied!\n\n"
            "Only @ShrutiBots Official Team Members can Access this feature.\n\n"
            "Contact the administration for access permissions.",
            show_alert=True
        )
    else:
        await CallbackQuery.answer(
            "✅ Access Granted! You are authorized to view stats.",
            show_alert=True
        )


@app.on_callback_query(filters.regex("stats_back") & ~BANNED_USERS)
@languageCB
async def home_stats(client, CallbackQuery, _):
    if not is_authorized(CallbackQuery.from_user.id):
        await CallbackQuery.answer(
            "❌ Access Denied!\n\n"
            "Only @ShrutiBots Official Team Members can Access this feature.",
            show_alert=True
        )
        return
    
    upl = stats_buttons(_, True if CallbackQuery.from_user.id in SUDOERS else False)
    await CallbackQuery.edit_message_text(
        text=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("TopOverall") & ~BANNED_USERS)
@languageCB
async def overall_stats(client, CallbackQuery, _):
    if not is_authorized(CallbackQuery.from_user.id):
        await CallbackQuery.answer(
            "❌ Access Denied!\n\n"
            "Only @ShrutiBots Official Team Members can Access this feature.",
            show_alert=True
        )
        return
    
    await CallbackQuery.answer()
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    await CallbackQuery.edit_message_text(_["gstats_1"].format(app.mention))
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    text = _["gstats_3"].format(
        app.mention,
        len(assistants),
        len(BANNED_USERS),
        served_chats,
        served_users,
        len(ALL_MODULES),
        len(SUDOERS),
        await is_autoend(),
        config.DURATION_LIMIT_MIN,
        await is_autoleave()  
    )
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG_URL, caption=text, reply_markup=upl
        )


@app.on_callback_query(filters.regex("bot_stats_sudo"))
@languageCB
async def bot_stats(client, CallbackQuery, _):
    if not is_authorized(CallbackQuery.from_user.id):
        await CallbackQuery.answer(
            "❌ Access Denied!\n\n"
            "Only @ShrutiBots Official Team Members can Access this feature.",
            show_alert=True
        )
        return
    
    if CallbackQuery.from_user.id not in SUDOERS:
        return await CallbackQuery.answer(_["gstats_4"], show_alert=True)
    
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    await CallbackQuery.edit_message_text(_["gstats_1"].format(app.mention))
    p_core = psutil.cpu_count(logical=False)
    t_core = psutil.cpu_count(logical=True)
    ram = str(round(psutil.virtual_memory().total / (1024.0**3))) + " ɢʙ"
    try:
        cpu_freq = psutil.cpu_freq().current
        if cpu_freq >= 1000:
            cpu_freq = f"{round(cpu_freq / 1000, 2)}ɢʜᴢ"
        else:
            cpu_freq = f"{round(cpu_freq, 2)}ᴍʜᴢ"
    except:
        cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
    hdd = psutil.disk_usage("/")
    total = hdd.total / (1024.0**3)
    used = hdd.used / (1024.0**3)
    free = hdd.free / (1024.0**3)
    call = await mongodb.command("dbstats")
    datasize = call["dataSize"] / 1024
    storage = call["storageSize"] / 1024
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    text = _["gstats_5"].format(
        app.mention,
        len(ALL_MODULES),
        platform.system(),
        ram,
        p_core,
        t_core,
        cpu_freq,
        pyver.split()[0],
        pyrover,
        pytgver,
        str(total)[:4],
        str(used)[:4],
        str(free)[:4],
        served_chats,
        served_users,
        len(BANNED_USERS),
        len(await get_sudoers()),
        str(datasize)[:6],
        storage,
        call["collections"],
        call["objects"],
    )
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG_URL, caption=text, reply_markup=upl
        )
