from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import ChatJoinRequest
from pyrogram.errors.exceptions.bad_request_400 import UserAlreadyParticipant
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.utils.keyboard import ikb
from ShrutiMusic.utils.permissions import adminsOnly, member_permissions

approvaldb = mongodb.autoapprove


@app.on_message(filters.command("autoapprove") & filters.group)
@adminsOnly("can_change_info")
async def approval_command(client, message):
    chat_id = message.chat.id
    chat = await approvaldb.find_one({"chat_id": chat_id})
    if chat and not chat.get("disabled", False):
        mode = chat.get("mode", "manual")
        if mode == "automatic":
            switch = "manual"
            label = "🔄 sᴡɪᴛᴄʜ ᴛᴏ ᴍᴀɴᴜᴀʟ"
            current = "✅ ᴀᴜᴛᴏᴀᴘᴘʀᴏᴠᴀʟ: ᴀᴜᴛᴏᴍᴀᴛɪᴄ"
        else:
            switch = "automatic"
            label = "🔄 sᴡɪᴛᴄʜ ᴛᴏ ᴀᴜᴛᴏᴍᴀᴛɪᴄ"
            current = "✅ ᴀᴜᴛᴏᴀᴘᴘʀᴏᴠᴀʟ: ᴍᴀɴᴜᴀʟ"

        buttons = {
            "❌ ᴛᴜʀɴ ᴏғғ": "approval_off",
            label: f"approval_{switch}",
        }
        keyboard = ikb(buttons, 1)
        await message.reply(f"<b>{current}</b>", reply_markup=keyboard)

    else:
        buttons = {"✅ ᴛᴜʀɴ ᴏɴ": "approval_on"}
        keyboard = ikb(buttons, 1)
        await message.reply(
            "<b>ᴀᴜᴛᴏᴀᴘᴘʀᴏᴠᴀʟ ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ: ᴅɪsᴀʙʟᴇᴅ.</b>", reply_markup=keyboard
        )


@app.on_callback_query(filters.regex("approval(.*)"))
async def approval_cb(client, cb):
    chat_id = cb.message.chat.id
    from_user = cb.from_user
    permissions = await member_permissions(chat_id, from_user.id)
    if "can_restrict_members" not in permissions and from_user.id not in SUDOERS:
        return await cb.answer(
            "ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ (ᴄᴀɴ_ʀᴇsᴛʀɪᴄᴛ_ᴍᴇᴍʙᴇʀs).",
            show_alert=True,
        )

    option = cb.data.split("_", 1)[1]

    if option == "off":
        # 🔧 FIXED: instead of deleting doc, mark disabled = True
        await approvaldb.update_one(
            {"chat_id": chat_id},
            {"$set": {"disabled": True, "mode": "manual"}},
            upsert=True,
        )
        buttons = {"✅ ᴛᴜʀɴ ᴏɴ": "approval_on"}
        keyboard = ikb(buttons, 1)
        return await cb.edit_message_text(
            "<b>ᴀᴜᴛᴏᴀᴘᴘʀᴏᴠᴀʟ ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ: ᴅɪsᴀʙʟᴇᴅ.</b>", reply_markup=keyboard
        )

    if option == "on":
        # 🔧 FIXED: Re-enable properly
        mode = "automatic"
        switch = "manual"
        label = "🔄 sᴡɪᴛᴄʜ ᴛᴏ ᴍᴀɴᴜᴀʟ"
        await approvaldb.update_one(
            {"chat_id": chat_id},
            {"$set": {"disabled": False, "mode": mode}},
            upsert=True,
        )

    elif option == "automatic":
        mode = "automatic"
        switch = "manual"
        label = "🔄 sᴡɪᴛᴄʜ ᴛᴏ ᴍᴀɴᴜᴀʟ"
        await approvaldb.update_one(
            {"chat_id": chat_id},
            {"$set": {"mode": mode}},
            upsert=True,
        )
    else:
        mode = "manual"
        switch = "automatic"
        label = "🔄 sᴡɪᴛᴄʜ ᴛᴏ ᴀᴜᴛᴏᴍᴀᴛɪᴄ"
        await approvaldb.update_one(
            {"chat_id": chat_id},
            {"$set": {"mode": mode}},
            upsert=True,
        )

    current = "✅ ᴀᴜᴛᴏᴀᴘᴘʀᴏᴠᴀʟ: ᴀᴜᴛᴏᴍᴀᴛɪᴄ" if mode == "automatic" else "✅ ᴀᴜᴛᴏᴀᴘᴘʀᴏᴠᴀʟ: ᴍᴀɴᴜᴀʟ"
    buttons = {"❌ ᴛᴜʀɴ ᴏғғ": "approval_off", label: f"approval_{switch}"}
    keyboard = ikb(buttons, 1)
    await cb.edit_message_text(f"<b>{current}</b>", reply_markup=keyboard)


@app.on_chat_join_request(filters.group)
async def accept(client, message: ChatJoinRequest):
    chat = message.chat
    user = message.from_user

    try:
        chat_data = await approvaldb.find_one({"chat_id": chat.id})

        # 🔧 FIXED: If disabled=True, skip everything (fully manual)
        if chat_data and chat_data.get("disabled", False):
            return  # no auto action

        if chat_data and chat_data.get("mode") == "automatic":
            try:
                await app.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
                return
            except Exception:
                pass  # fallback to manual mode

        # Manual or fallback mode
        is_user_in_pending = await approvaldb.count_documents(
            {"chat_id": chat.id, "pending_users": int(user.id)}
        )

        if is_user_in_pending == 0:
            await approvaldb.update_one(
                {"chat_id": chat.id},
                {"$addToSet": {"pending_users": int(user.id)}},
                upsert=True,
            )

            buttons = {
                "✅ ᴀᴄᴄᴇᴘᴛ": f"manual_approve_{user.id}",
                "❌ ᴅᴇᴄʟɪɴᴇ": f"manual_decline_{user.id}",
            }
            keyboard = ikb(buttons, 2)
            text = (
                f"<b>🔔 ɴᴇᴡ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ</b>\n\n"
                f"<b>ᴜsᴇʀ:</b> {user.mention}\n"
                f"<b>ᴜsᴇʀɴᴀᴍᴇ:</b> @{user.username or 'ɴᴏɴᴇ'}\n"
                f"<b>ᴜsᴇʀ ɪᴅ:</b> <code>{user.id}</code>\n\n"
                f"<i>ᴀᴅᴍɪɴs ᴄᴀɴ ᴀᴘᴘʀᴏᴠᴇ ᴏʀ ᴅᴇᴄʟɪɴᴇ ʙᴇʟᴏᴡ:</i>"
            )

            try:
                admin_data = [
                    i
                    async for i in app.get_chat_members(
                        chat_id=chat.id,
                        filter=ChatMembersFilter.ADMINISTRATORS,
                    )
                ]
                for admin in admin_data:
                    if admin.user.is_bot or admin.user.is_deleted:
                        continue
                    text += f'<a href="tg://user?id={admin.user.id}">\u200b</a>'
            except Exception:
                pass

            await app.send_message(chat.id, text, reply_markup=keyboard)

    except Exception:
        pass
