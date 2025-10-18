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

from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from ..logging import LOGGER


class Aviax(Client):
    def __init__(self):
        LOGGER(__name__).info("🚀 Initializing Bot...")
        super().__init__(
            name="ShrutiMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        # Inline buttons
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Add Me To Group",
                        url=f"https://t.me/{self.username}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton("📢 Support", url=config.SUPPORT_GROUP),
                    InlineKeyboardButton("💻 Repo", url="https://github.com/NoxxOP/ShrutiMusic"),
                ],
            ]
        )

        try:
            await self.send_message(
                chat_id=config.LOG_GROUP_ID,
                text=(
                    f"<b>✨ ʙᴏᴛ ɪs ɴᴏᴡ ʟɪᴠᴇ ✨</b>\n\n"
                    f"🚀 <b>{self.mention}</b> ʜᴀs sᴜᴄᴄᴇssғᴜʟʟʏ sᴛᴀʀᴛᴇᴅ!\n\n"
                    f"<u><b>🛠 ʙᴏᴛ ᴅᴇᴛᴀɪʟs :</b></u>\n"
                    f"• 🆔 <b>ID:</b> <code>{self.id}</code>\n"
                    f"• 👤 <b>Name:</b> {self.name}\n"
                    f"• 🔗 <b>Username:</b> @{self.username}\n\n"
                    f"<i>✅ Everything is set! Bot is online and ready to groove 🎶</i>"
                ),
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "❌ Bot failed to access the log group/channel. Add your bot to log group/channel first."
            )
            exit()
        except Exception as ex:
            LOGGER(__name__).error(
                f"❌ Unexpected error while accessing log group.\nReason: {type(ex).__name__}."
            )
            exit()

        # Admin check
        a = await self.get_chat_member(config.LOG_GROUP_ID, self.id)
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error("⚠️ Please promote your bot as admin in the log group/channel.")
            exit()

        LOGGER(__name__).info(f"🎶 Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
