import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ParseMode
from pyrogram.errors import FloodWait, ChatWriteForbidden, UserIsBlocked, PeerIdInvalid
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from ShrutiMusic.utils.decorators.language import language
from ShrutiMusic.utils.formatters import alpha_to_int
from config import adminlist

IS_BROADCASTING = False

class BroadcastStats:
    def __init__(self):
        self.total_targets = 0
        self.successful = 0
        self.failed = 0
        self.pinned = 0
        self.errors = {}
        
    def add_error(self, error_type):
        if error_type in self.errors:
            self.errors[error_type] += 1
        else:
            self.errors[error_type] = 1
            
    def get_report(self):
        error_report = "\n".join([f"• {err}: {count}" for err, count in self.errors.items()])
        return f"✅ Successful: {self.successful}\n❌ Failed: {self.failed}\n📌 Pinned: {self.pinned}\n\n<b>Error Breakdown:</b>\n{error_report if self.errors else 'No errors'}"

async def copy_message_with_entities(client, chat_id, original_message):
    """Copy message with all formatting including clickable links and usernames"""
    text = original_message.text or original_message.caption or ""
    entities = original_message.entities or original_message.caption_entities or []
    
    kwargs = {
        "chat_id": chat_id,
        "reply_markup": original_message.reply_markup if original_message.reply_markup else None
    }

    try:
        if original_message.photo:
            return await client.send_photo(
                photo=original_message.photo.file_id,
                caption=text,
                caption_entities=entities,
                **kwargs
            )
        elif original_message.video:
            return await client.send_video(
                video=original_message.video.file_id,
                caption=text,
                caption_entities=entities,
                **kwargs
            )
        elif original_message.audio:
            return await client.send_audio(
                audio=original_message.audio.file_id,
                caption=text,
                caption_entities=entities,
                **kwargs
            )
        elif original_message.document:
            return await client.send_document(
                document=original_message.document.file_id,
                caption=text,
                caption_entities=entities,
                **kwargs
            )
        elif original_message.animation:
            return await client.send_animation(
                animation=original_message.animation.file_id,
                caption=text,
                caption_entities=entities,
                **kwargs
            )
        elif original_message.sticker:
            sent = await client.send_sticker(
                chat_id=chat_id,
                sticker=original_message.sticker.file_id
            )
            if text:
                await client.send_message(
                    chat_id=chat_id,
                    text=text,
                    entities=entities,
                    disable_web_page_preview=True
                )
            return sent
        else:
            return await client.send_message(
                chat_id=chat_id,
                text=text,
                entities=entities,
                disable_web_page_preview=True,
                **kwargs
            )
    except Exception as e:
        print(f"Error in copy_message: {str(e)} for chat_id {chat_id}")
        raise e

async def send_progress_message(message, stats, title="Broadcast Progress"):
    progress_text = f"<b>{title}</b>\n\n"
    progress_text += f"🎯 Total targets: {stats.total_targets}\n"
    progress_text += f"✅ Sent successfully: {stats.successful}\n"
    progress_text += f"❌ Failed: {stats.failed}\n"
    progress_text += f"📊 Progress: {stats.successful + stats.failed}/{stats.total_targets}"
    
    try:
        return await message.edit_text(progress_text, parse_mode=ParseMode.HTML)
    except:
        return await message.reply_text(progress_text, parse_mode=ParseMode.HTML)

@app.on_message(filters.command(["broadcast", "bcast"]) & SUDOERS)
@language
async def broadcast_message(client, message, _):
    global IS_BROADCASTING
    
    if IS_BROADCASTING:
        return await message.reply_text("⚠️ A broadcast is already in progress. Please wait until it completes.")
    
    flags = {
        "-wfchat": False,
        "-wfuser": False,
        "-nobot": False,
        "-pin": False,
        "-pinloud": False,
        "-assistant": False,
        "-user": False,
        "-noforward": False,
        "-preview": False,
        "-silent": False,
        "-dryrun": False
    }
    
    for flag in flags:
        if flag in message.text:
            flags[flag] = True
            
    assistant_num = None
    command_text = message.text.lower()
    for part in command_text.split():
        if part.startswith("-assistant="):
            try:
                assistant_num = int(part.split("=")[1])
                flags["-assistant"] = True
            except ValueError:
                pass
    
    if flags["-wfchat"] or flags["-wfuser"]:
        if not message.reply_to_message:
            return await message.reply_text("❌ Please reply to a message for broadcasting.")

        IS_BROADCASTING = True
        await message.reply_text(_["broad_1"])

        if flags["-wfchat"]:
            stats = BroadcastStats()
            chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
            stats.total_targets = len(chats)
            
            progress_msg = await message.reply_text("📊 Preparing broadcast to chats...")
            
            for i in chats:
                try:
                    if flags["-noforward"]:
                        await copy_message_with_entities(app, i, message.reply_to_message)
                    else:
                        await message.reply_to_message.forward(i)
                    stats.successful += 1
                except FloodWait as fw:
                    await asyncio.sleep(fw.value)
                    try:
                        if flags["-noforward"]:
                            await copy_message_with_entities(app, i, message.reply_to_message)
                        else:
                            await message.reply_to_message.forward(i)
                        stats.successful += 1
                    except:
                        stats.failed += 1
                        stats.add_error("After FloodWait")
                except Exception as e:
                    stats.failed += 1
                    error_type = type(e).__name__
                    stats.add_error(error_type)
                
                if not flags["-silent"] and (stats.successful + stats.failed) % 25 == 0:
                    await send_progress_message(progress_msg, stats, "Chat Broadcast Progress")
                
                await asyncio.sleep(0.2)
            
            await message.reply_text(f"✅ Broadcast to chats completed!\n\n{stats.get_report()}", parse_mode=ParseMode.HTML)

        if flags["-wfuser"]:
            stats = BroadcastStats()
            users = [int(user["user_id"]) for user in await get_served_users()]
            stats.total_targets = len(users)
            
            progress_msg = await message.reply_text("📊 Preparing broadcast to users...")
            
            for i in users:
                try:
                    if flags["-noforward"]:
                        await copy_message_with_entities(app, i, message.reply_to_message)
                    else:
                        await message.reply_to_message.forward(i)
                    stats.successful += 1
                except FloodWait as fw:
                    await asyncio.sleep(fw.value)
                    try:
                        if flags["-noforward"]:
                            await copy_message_with_entities(app, i, message.reply_to_message)
                        else:
                            await message.reply_to_message.forward(i)
                        stats.successful += 1
                    except:
                        stats.failed += 1
                        stats.add_error("After FloodWait")
                except Exception as e:
                    stats.failed += 1
                    error_type = type(e).__name__
                    stats.add_error(error_type)
                
                if not flags["-silent"] and (stats.successful + stats.failed) % 25 == 0:
                    await send_progress_message(progress_msg, stats, "User Broadcast Progress")
                
                await asyncio.sleep(0.2)
            
            await message.reply_text(f"✅ Broadcast to users completed!\n\n{stats.get_report()}", parse_mode=ParseMode.HTML)

        IS_BROADCASTING = False
        return

    x = None
    y = None
    query = None
    
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
        
        if flags["-dryrun"]:
            return await message.reply_text(
                "🧪 DRY RUN MODE\n\n"
                f"Would broadcast the replied message with these flags:\n"
                f"{', '.join([flag for flag in flags if flags[flag]])}\n\n"
                "No actual broadcast will be performed."
            )
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        
        query = message.text.split(None, 1)[1]
        
        for flag in flags:
            query = query.replace(flag, "")
        
        if assistant_num is not None:
            query = query.replace(f"-assistant={assistant_num}", "")
            
        query = query.strip()
        
        if not query:
            return await message.reply_text(_["broad_8"])
        
        if flags["-dryrun"]:
            return await message.reply_text(
                "🧪 DRY RUN MODE\n\n"
                f"Would broadcast this message:\n\n{query}\n\n"
                f"With these flags: {', '.join([flag for flag in flags if flags[flag]])}\n\n"
                "No actual broadcast will be performed."
            )

    IS_BROADCASTING = True
    status_message = await message.reply_text(_["broad_1"])

    if not flags["-nobot"]:
        sent = pin = 0
        chats_stats = BroadcastStats()
        chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
        chats_stats.total_targets = len(chats)
        
        progress_msg = await message.reply_text("📊 Preparing broadcast to chats...")
        
        for chat_id in chats:
            try:
                if message.reply_to_message:
                    if flags["-noforward"]:
                        m = await copy_message_with_entities(app, chat_id, message.reply_to_message)
                    else:
                        m = await app.forward_messages(chat_id, y, x)
                else:
                    m = await app.send_message(
                        chat_id, 
                        text=query,
                        disable_web_page_preview=not flags["-preview"],
                        parse_mode=ParseMode.HTML
                    )
                
                if flags["-pin"] or flags["-pinloud"]:
                    try:
                        await m.pin(disable_notification=not flags["-pinloud"])
                        pin += 1
                        chats_stats.pinned += 1
                    except Exception as e:
                        chats_stats.add_error(f"Pin failed: {type(e).__name__}")
                
                sent += 1
                chats_stats.successful += 1
                
                if not flags["-silent"] and chats_stats.successful % 25 == 0:
                    await send_progress_message(progress_msg, chats_stats, "Chat Broadcast Progress")
                    
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                try:
                    if message.reply_to_message:
                        if flags["-noforward"]:
                            m = await copy_message_with_entities(app, chat_id, message.reply_to_message)
                        else:
                            m = await app.forward_messages(chat_id, y, x)
                    else:
                        m = await app.send_message(
                            chat_id, 
                            text=query,
                            disable_web_page_preview=not flags["-preview"],
                            parse_mode=ParseMode.HTML
                        )
                    chats_stats.successful += 1
                except Exception as e:
                    chats_stats.failed += 1
                    chats_stats.add_error(type(e).__name__)
            except ChatWriteForbidden:
                chats_stats.failed += 1
                chats_stats.add_error("Bot not admin/No permission")
            except PeerIdInvalid:
                chats_stats.failed += 1
                chats_stats.add_error("Invalid chat ID")
            except Exception as e:
                chats_stats.failed += 1
                chats_stats.add_error(type(e).__name__)
        
        try:
            await message.reply_text(
                f"✅ Broadcast to chats completed!\n\n"
                f"📊 Stats:\n"
                f"- Sent: {sent}\n"
                f"- Pinned: {pin}\n\n"
                f"{chats_stats.get_report()}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

    if flags["-user"]:
        user_stats = BroadcastStats()
        susr = 0
        users = [int(user["user_id"]) for user in await get_served_users()]
        user_stats.total_targets = len(users)
        
        progress_msg = await message.reply_text("📊 Preparing broadcast to users...")
        
        for user_id in users:
            try:
                if message.reply_to_message:
                    if flags["-noforward"]:
                        m = await copy_message_with_entities(app, user_id, message.reply_to_message)
                    else:
                        m = await app.forward_messages(user_id, y, x)
                else:
                    m = await app.send_message(
                        user_id,
                        text=query,
                        disable_web_page_preview=not flags["-preview"],
                        parse_mode=ParseMode.HTML
                    )
                susr += 1
                user_stats.successful += 1
                
                if not flags["-silent"] and user_stats.successful % 25 == 0:
                    await send_progress_message(progress_msg, user_stats, "User Broadcast Progress")
                    
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                try:
                    if message.reply_to_message:
                        if flags["-noforward"]:
                            m = await copy_message_with_entities(app, user_id, message.reply_to_message)
                        else:
                            m = await app.forward_messages(user_id, y, x)
                    else:
                        m = await app.send_message(
                            user_id,
                            text=query,
                            disable_web_page_preview=not flags["-preview"],
                            parse_mode=ParseMode.HTML
                        )
                    user_stats.successful += 1
                except:
                    user_stats.failed += 1
            except UserIsBlocked:
                user_stats.failed += 1
                user_stats.add_error("User blocked bot")
            except PeerIdInvalid:
                user_stats.failed += 1
                user_stats.add_error("Invalid user ID")
            except Exception as e:
                user_stats.failed += 1
                user_stats.add_error(type(e).__name__)
        
        try:
            await message.reply_text(
                f"✅ Broadcast to users completed!\n\n"
                f"📊 Stats:\n"
                f"- Successfully sent: {susr}\n\n"
                f"{user_stats.get_report()}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

    if flags["-assistant"]:
        aw = await message.reply_text(_["broad_5"])
        text = _["broad_6"]
        from ShrutiMusic.core.userbot import assistants
        
        if assistant_num is not None:
            if assistant_num in assistants:
                assistant_list = [assistant_num]
            else:
                await aw.edit_text(f"❌ Assistant {assistant_num} not found.")
                IS_BROADCASTING = False
                return
        else:
            assistant_list = assistants
            
        for num in assistant_list:
            sent = 0
            failed = 0
            client = await get_client(num)
            if not client:
                text += f"❌ Assistant {num}: Failed to get client\n"
                continue
                
            try:
                dialogs = []
                async for dialog in client.get_dialogs():
                    dialogs.append(dialog.chat.id)
                    
                for dialog_id in dialogs:
                    try:
                        if message.reply_to_message:
                            if flags["-noforward"]:
                                m = await copy_message_with_entities(client, dialog_id, message.reply_to_message)
                            else:
                                m = await client.forward_messages(dialog_id, y, x)
                        else:
                            m = await client.send_message(
                                dialog_id,
                                text=query,
                                disable_web_page_preview=not flags["-preview"],
                                parse_mode=ParseMode.HTML
                            )
                        sent += 1
                        await asyncio.sleep(0.5)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                        try:
                            if message.reply_to_message:
                                if flags["-noforward"]:
                                    m = await copy_message_with_entities(client, dialog_id, message.reply_to_message)
                                else:
                                    m = await client.forward_messages(dialog_id, y, x)
                            else:
                                m = await client.send_message(
                                    dialog_id,
                                    text=query,
                                    disable_web_page_preview=not flags["-preview"],
                                    parse_mode=ParseMode.HTML
                                )
                            sent += 1
                        except:
                            failed += 1
                    except Exception as e:
                        failed += 1
                        
                text += _["broad_7"].format(num, sent)
                if failed > 0:
                    text += f" (Failed: {failed})"
                text += "\n"
                
            except Exception as e:
                text += f"❌ Assistant {num}: Error - {str(e)}\n"
        
        try:
            await aw.edit_text(text)
        except:
            await message.reply_text(text)

    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ OK", callback_data="close")]
        ])
        await status_message.edit_text(
            "<b>✅ Broadcast completed successfully!</b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except:
        pass

    IS_BROADCASTING = False

@app.on_message(filters.command("broadcastcancel") & SUDOERS)
async def cancel_broadcast(client, message):
    global IS_BROADCASTING
    if IS_BROADCASTING:
        IS_BROADCASTING = False
        await message.reply_text("🛑 Broadcast operation has been cancelled.")
    else:
        await message.reply_text("❌ No active broadcast to cancel.")

@app.on_message(filters.command("broadcasthelp") & SUDOERS)
async def broadcast_help(client, message):
    help_text = """
<b>📡 Broadcast Command Help</b>

<b>Basic Usage:</b>
- <code>/broadcast</code> - Reply to a message to broadcast it
- <code>/broadcast [text]</code> - Broadcast text message

<b>Available Flags:</b>
- <code>-nobot</code> - Skip broadcasting to chats
- <code>-user</code> - Broadcast to users
- <code>-pin</code> - Pin message in chats (silent)
- <code>-pinloud</code> - Pin message in chats (with notification)
- <code>-assistant</code> - Broadcast via assistant accounts
- <code>-assistant=X</code> - Broadcast via specific assistant number
- <code>-noforward</code> - Send without forward tag
- <code>-preview</code> - Enable link previews
- <code>-silent</code> - Fewer progress updates
- <code>-dryrun</code> - Test broadcast without sending

<b>Legacy Commands (Compatible):</b>
- <code>/broadcast -wfchat</code> - Broadcast to chats
- <code>/broadcast -wfuser</code> - Broadcast to users

<b>Admin Commands:</b>
- <code>/broadcastcancel</code> - Cancel ongoing broadcast
- <code>/broadcasthelp</code> - Show this help message
"""
    await message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges and user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except:
            continue

asyncio.create_task(auto_clean())
