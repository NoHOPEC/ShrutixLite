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


import asyncio

from pyrogram import enums, filters
from pyrogram.errors import FloodWait

from ShrutiMusic import app


@app.on_message(filters.command("bots") & filters.group)
async def bots(client, message):
    try:
        botList = []
        async for bot in app.get_chat_members(
            message.chat.id, filter=enums.ChatMembersFilter.BOTS
        ):
            botList.append(bot.user)
        lenBotList = len(botList)

        if lenBotList == 0:
            await app.send_message(
                message.chat.id,
                f"<b>🤖 {message.chat.title} me koi bot nahi hai!</b>"
            )
            return

        text3 = f"<b>🌟 ʙᴏᴛ ʟɪsᴛ - {message.chat.title} 🌟</b>\n\n"
        text3 += "<b>🤖 Bots:</b>\n"

        while len(botList) > 1:
            bot = botList.pop(0)
            username = f"@{bot.username}" if bot.username else bot.first_name
            text3 += f"├ {username}\n"
        else:
            bot = botList.pop(0)
            username = f"@{bot.username}" if bot.username else bot.first_name
            text3 += f"└ {username}\n\n"

        text3 += f"<b>✨ Total Bots:</b> {lenBotList}"
        await app.send_message(message.chat.id, text3)

    except FloodWait as e:
        await asyncio.sleep(e.value)


__MODULE__ = "Bᴏᴛs"
__HELP__ = """
<b>ʙᴏᴛs</b>

• /bots - Get a stylish list of all bots in the group.
"""
