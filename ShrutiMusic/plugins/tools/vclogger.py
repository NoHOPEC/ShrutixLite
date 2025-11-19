import asyncio
from logging import getLogger
from typing import Dict, Set

from pyrogram import filters
from pyrogram.types import Message
from pytgcalls import GroupCallFactory
from pytgcalls.implementation.group_call import GroupCallAction

from ShrutiMusic import app
from ShrutiMusic.utils.database import get_assistant

LOGGER = getLogger(__name__)


active_group_calls: Dict[int, object] = {}
vc_participants: Dict[int, Set[int]] = {}


async def send_and_delete(chat_id: int, text: str, delay: int = 3):
    try:
        msg = await app.send_message(chat_id, text)
        await asyncio.sleep(delay)
        await msg.delete()
    except Exception as e:
        LOGGER.error(f"Error in send_and_delete: {e}")


async def start_vc_monitoring(chat_id: int):
    if chat_id in active_group_calls:
        return
    
    try:
        userbot = await get_assistant(chat_id)
        if not userbot:
            LOGGER.error(f"No assistant found for chat {chat_id}")
            return
        
        factory = GroupCallFactory(
            userbot,
            GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM
        )
        
        group_call = factory.get_file_group_call()
        
        @group_call.on_participant_list_updated
        async def on_participants_update(gc, participants):
            try:
                current_participants = vc_participants.get(chat_id, set())
                
                for participant in participants:
                    if hasattr(participant, 'peer'):
                        peer = participant.peer
                        user_id = None
                        
                        if hasattr(peer, 'user_id'):
                            user_id = peer.user_id
                        elif hasattr(peer, 'channel_id'):
                            continue
                        elif hasattr(peer, 'chat_id'):
                            continue
                        
                        if not user_id:
                            continue
                        
                        is_left = getattr(participant, 'left', False)
                        just_joined = getattr(participant, 'just_joined', False)
                        
                        if just_joined and user_id not in current_participants:
                            current_participants.add(user_id)
                            asyncio.create_task(handle_user_join(chat_id, user_id, userbot))
                        
                        elif is_left and user_id in current_participants:
                            current_participants.discard(user_id)
                            asyncio.create_task(handle_user_leave(chat_id, user_id, userbot))
                
                vc_participants[chat_id] = current_participants
            
            except Exception as e:
                LOGGER.error(f"Error in participant update handler: {e}")
        
        try:
            await group_call.start(chat_id, enable_action=False)
            await group_call.set_is_mute(True)
            active_group_calls[chat_id] = group_call
            vc_participants[chat_id] = set()
            LOGGER.info(f"Started VC monitoring for chat {chat_id}")
        except Exception as e:
            LOGGER.error(f"Error starting group call for {chat_id}: {e}")
            pass
    
    except Exception as e:
        LOGGER.error(f"Error in start_vc_monitoring: {e}")


async def stop_vc_monitoring(chat_id: int):
    if chat_id in active_group_calls:
        try:
            group_call = active_group_calls[chat_id]
            await group_call.stop()
            del active_group_calls[chat_id]
            if chat_id in vc_participants:
                del vc_participants[chat_id]
            LOGGER.info(f"Stopped VC monitoring for chat {chat_id}")
        except Exception as e:
            LOGGER.error(f"Error stopping VC monitoring: {e}")


async def handle_user_join(chat_id: int, user_id: int, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "Unknown User"
        username = f"@{user.username}" if user.username else "No Username"
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'
        
        join_message = f"""🎤 <b>ᴜsᴇʀ ᴊᴏɪɴᴇᴅ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</b>

👤 <b>ɴᴀᴍᴇ :-</b> {mention}
🔗 <b>ᴜsᴇʀɴᴀᴍᴇ :-</b> {username}
🆔 <b>ɪᴅ :-</b> <code>{user_id}</code>

<b>❖ ᴛʜᴀɴᴋs ғᴏʀ ᴊᴏɪɴɪɴɢ 😁</b>"""
        
        await send_and_delete(chat_id, join_message, 3)
    except Exception as e:
        LOGGER.error(f"Error sending join message for {user_id}: {e}")


async def handle_user_leave(chat_id: int, user_id: int, userbot):
    try:
        user = await userbot.get_users(user_id)
        name = user.first_name or "Unknown User"
        username = f"@{user.username}" if user.username else "No Username"
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'
        
        leave_message = f"""🚪 <b>ᴜsᴇʀ ʟᴇғᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</b>

👤 <b>ɴᴀᴍᴇ :-</b> {mention}
🔗 <b>ᴜsᴇʀɴᴀᴍᴇ :-</b> {username}
🆔 <b>ɪᴅ :-</b> <code>{user_id}</code>

<b>❖ ʙʏᴇ ʙʏᴇ ᴠɪsɪᴛ ᴀɢᴀɪɴ 👋</b>"""
        
        await send_and_delete(chat_id, leave_message, 3)
    except Exception as e:
        LOGGER.error(f"Error sending leave message for {user_id}: {e}")


@app.on_message(filters.group)
async def auto_start_vc_logging(_, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in active_group_calls:
        asyncio.create_task(start_vc_monitoring(chat_id))
