from pyrogram import filters
from pyrogram.types import ChatPrivileges, Message

from ShrutiMusic import app
from ShrutiMusic.utils.permissions import adminsOnly


@app.on_message(filters.command("spromote") & filters.group)
@adminsOnly("can_promote_members")
async def silent_promote(client, message: Message):
    try:
        if len(message.command) < 2:
            return await message.reply_text(
                "<b>Usage:</b> <code>/spromote [userid/username] [admin_tag]</code>\n"
                "<b>Example:</b> <code>/spromote @user ᴍᴏᴅᴇʀᴀᴛᴏʀ</code>"
            )
        
        user_input = message.command[1]
        admin_tag = " ".join(message.command[2:]) if len(message.command) > 2 else "ᴀᴅᴍɪɴ"
        
        try:
            if user_input.isdigit():
                user = await client.get_users(int(user_input))
            else:
                user = await client.get_users(user_input)
        except Exception:
            return await message.reply_text("❌ User not found!")
        
        chat = await client.get_chat(message.chat.id)
        
        if chat.type == "channel":
            privileges = ChatPrivileges(
                can_manage_chat=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                is_anonymous=False
            )
        else:
            privileges = ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=True,
                is_anonymous=False
            )
        
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            privileges=privileges
        )
        
        try:
            await client.set_administrator_title(
                chat_id=message.chat.id,
                user_id=user.id,
                title=admin_tag
            )
        except Exception:
            pass
        
        await message.delete()
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command("sfullpromote") & filters.group)
@adminsOnly("can_promote_members")
async def silent_full_promote(client, message: Message):
    try:
        if len(message.command) < 2:
            return await message.reply_text(
                "<b>Usage:</b> <code>/sfullpromote [userid/username] [admin_tag]</code>\n"
                "<b>Example:</b> <code>/sfullpromote @user ᴏᴡɴᴇʀ</code>"
            )
        
        user_input = message.command[1]
        admin_tag = " ".join(message.command[2:]) if len(message.command) > 2 else "ᴀᴅᴍɪɴ"
        
        try:
            if user_input.isdigit():
                user = await client.get_users(int(user_input))
            else:
                user = await client.get_users(user_input)
        except Exception:
            return await message.reply_text("❌ User not found!")
        
        chat = await client.get_chat(message.chat.id)
        
        if chat.type == "channel":
            privileges = ChatPrivileges(
                can_manage_chat=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=False,
                is_anonymous=False
            )
        else:
            privileges = ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=True,
                is_anonymous=False
            )
        
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            privileges=privileges
        )
        
        try:
            await client.set_administrator_title(
                chat_id=message.chat.id,
                user_id=user.id,
                title=admin_tag
            )
        except Exception:
            pass
        
        await message.delete()
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
