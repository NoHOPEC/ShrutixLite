# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com

import time
import asyncio
import random
from typing import Final

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from py_yt import VideosSearch

import config
from ShrutiMusic import app
from ShrutiMusic.misc import _boot_
from ShrutiMusic.plugins.sudo.sudoers import sudoers_list
from ShrutiMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from ShrutiMusic.utils import bot_sys_stats
from ShrutiMusic.utils.decorators.language import LanguageStart
from ShrutiMusic.utils.formatters import get_readable_time
from ShrutiMusic.utils.inline import help_pannel_page1, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string

SUCCESS_EFFECT_IDS: Final[list[str]] = [
    "5104841245755180586",
    "5107584321108051014",
    "5046509860389126442",
    "5104858069142078462",
    "5046589136895476101",
    "5159385139981059251",
    "5159394597140101489",
    "5046644244653319351",
    "5104845240685599858",
    "5104846560096133612",
    "5046658325095782976",
    "5104847456131440700",
    "5046663133331366464",
    "5104842446547815936",
    "5104843735244210688",
]

SAFE_REACTION_EMOJIS: Final[list[str]] = [
    "👍",
    "👎",
    "❤️",
    "🔥",
    "🎉",
    "🤩",
    "😱",
    "😁",
    "😢",
    "💩",
    "🤮",
    "🥰",
    "🤯",
    "🤔",
    "🤬",
    "👏",
    "😂",
    "😍",
    "🥳",
    "🤣",
    "😎",
    "🤝",
    "🙏",
    "💯",
    "⚡",
]

def get_random_effect_id():
    return int(random.choice(SUCCESS_EFFECT_IDS))

def get_safe_random_emoji():
    return random.choice(SAFE_REACTION_EMOJIS)

async def get_user_photo(user_id, user_first_name=None):
    try:
        user_photos = []
        async for photo in app.get_chat_photos(user_id, limit=1):
            user_photos.append(photo)
        
        if user_photos:
            return user_photos[0].file_id
        else:
            return config.START_IMG_URL
    except Exception as e:
        print(f"Error getting user photo for {user_id}: {e}")
        return config.START_IMG_URL

async def send_reaction_guaranteed(message: Message):
    emoji = get_safe_random_emoji()
    success = False
    
    try:
        await app.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji=emoji,
            big=True
        )
        success = True
        print(f"Big reaction sent: {emoji}")
    except Exception as e1:
        print(f"Big reaction failed: {e1}")
        
        try:
            await app.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji=emoji
            )
            success = True
            print(f"Normal reaction sent: {emoji}")
        except Exception as e2:
            print(f"Normal reaction failed: {e2}")
            
            try:
                await message.react(emoji)
                success = True
                print(f"Message react sent: {emoji}")
            except Exception as e3:
                print(f"All reaction methods failed: {e3}")
    
    if not success:
        try:
            fallback_emoji = "👍"
            await app.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji=fallback_emoji
            )
            print(f"Fallback reaction sent: {fallback_emoji}")
        except:
            print("Complete reaction failure")

async def send_message_with_effect_guaranteed(chat_id, photo, caption, reply_markup=None, reply_to_message_id=None):
    effect_id = get_random_effect_id()
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            result = await app.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
                reply_to_message_id=reply_to_message_id,
                message_effect_id=effect_id,
                protect_content=True
            )
            return result
        except:
            if attempt < max_attempts - 1:
                effect_id = get_random_effect_id()
                await asyncio.sleep(0.1)
                continue
            
            try:
                result = await app.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    reply_markup=reply_markup,
                    reply_to_message_id=reply_to_message_id,
                    protect_content=True
                )
                return result
            except:
                return None

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    await send_reaction_guaranteed(message)

    user_photo = await get_user_photo(message.from_user.id, message.from_user.first_name)

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = help_pannel_page1(_)
            result = await send_message_with_effect_guaranteed(
                chat_id=message.chat.id,
                photo=user_photo,
                caption=_["help_1"].format(config.SUPPORT_GROUP),
                reply_markup=keyboard
            )
            if not result:
                try:
                    return await message.reply_photo(
                        photo=user_photo,
                        caption=_["help_1"].format(config.SUPPORT_GROUP),
                        protect_content=True,
                        reply_markup=keyboard,
                    )
                except Exception:
                    pass

        elif name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} just started sudo check.\n"
                         f"User ID: <code>{message.from_user.id}</code>\n"
                         f"Username: @{message.from_user.username}",
                )
            return

        elif name.startswith("inf"):
            m = await message.reply_text("🔎")
            query = name.replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=_["S_B_8"], url=link),
                 InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_GROUP)],
            ])
            await m.delete()
            result = await send_message_with_effect_guaranteed(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched,
                reply_markup=key
            )
            if not result:
                try:
                    await message.reply_photo(
                        photo=thumbnail,
                        caption=searched,
                        reply_markup=key,
                    )
                except Exception:
                    pass
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} requested track info.\n"
                         f"User ID: <code>{message.from_user.id}</code>\n"
                         f"Username: @{message.from_user.username}",
                )

    else:
        out = private_panel(_)
        UP, CPU, RAM, DISK = await bot_sys_stats()

        result = await send_message_with_effect_guaranteed(
            chat_id=message.chat.id,
            photo=user_photo,
            caption=_["start_2"].format(
                message.from_user.mention, app.mention, UP, DISK, CPU, RAM
            ),
            reply_markup=InlineKeyboardMarkup(out)
        )
        
        if not result:
            try:
                await message.reply_photo(
                    photo=user_photo,
                    caption=_["start_2"].format(
                        message.from_user.mention, app.mention, UP, DISK, CPU, RAM
                    ),
                    reply_markup=InlineKeyboardMarkup(out)
                )
            except Exception:
                pass
                
        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOG_GROUP_ID,
                text=f"{message.from_user.mention} just started the bot.\n"
                     f"User ID: <code>{message.from_user.id}</code>\n"
                     f"Username: @{message.from_user.username}",
            )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    await send_reaction_guaranteed(message)

    user_photo = await get_user_photo(message.from_user.id, message.from_user.first_name)

    out = start_panel(_)
    uptime = int(time.time() - _boot_)

    result = await send_message_with_effect_guaranteed(
        chat_id=message.chat.id,
        photo=user_photo,
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out)
    )
    
    if not result:
        try:
            await message.reply_photo(
                photo=user_photo,
                caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
                reply_markup=InlineKeyboardMarkup(out)
            )
        except Exception:
            pass

    await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await send_reaction_guaranteed(message)
                    try:
                        await app.send_message(chat_id=message.chat.id, text=_["start_4"])
                    except:
                        await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await send_reaction_guaranteed(message)
                    try:
                        await app.send_message(
                            chat_id=message.chat.id,
                            text=_["start_5"].format(
                                app.mention,
                                f"https://t.me/{app.username}?start=sudolist",
                                config.SUPPORT_GROUP,
                            ),
                            disable_web_page_preview=True
                        )
                    except:
                        await message.reply_text(
                            _["start_5"].format(
                                app.mention,
                                f"https://t.me/{app.username}?start=sudolist",
                                config.SUPPORT_GROUP,
                            ),
                            disable_web_page_preview=True,
                        )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                await send_reaction_guaranteed(message)
                
                user_photo = await get_user_photo(message.from_user.id, message.from_user.first_name)
                
                result = await send_message_with_effect_guaranteed(
                    chat_id=message.chat.id,
                    photo=user_photo,
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out)
                )
                
                if not result:
                    try:
                        await message.reply_photo(
                            photo=user_photo,
                            caption=_["start_3"].format(
                                message.from_user.first_name,
                                app.mention,
                                message.chat.title,
                                app.mention,
                            ),
                            reply_markup=InlineKeyboardMarkup(out),
                        )
                    except Exception:
                        pass
                        
                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print(ex)
