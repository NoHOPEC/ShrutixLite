import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ParseMode
from pyrogram.errors import FloodWait
import random
import re

from ShrutiMusic import app

SPAM_CHATS = []
EMOJI = [
    "🦋🦋🦋🦋🦋",
    "🧚🌸🧋🍬🫖",
    "🥀🌷🌹🌺💐",
    "🌸🌿💮🌱🌵",
    "❤️💚💙💜🖤",
    "💓💕💞💗💖",
    "🌸💐🌺🌹🦋",
    "🍔🦪🍛🍲🥗",
    "🍎🍓🍒🍑🌶️",
    "🧋🥤🧋🥛🍷",
    "🍬🍭🧁🎂🍡",
    "🍨🧉🍺☕🍻",
    "🥪🥧🍦🍥🍚",
    "🫖☕🍹🍷🥛",
    "☕🧃🍩🍦🍙",
    "🍁🌾💮🍂🌿",
    "🌨️🌥️⛈️🌩️🌧️",
    "🌷🏵️🌸🌺💐",
    "💮🌼🌻🍀🍁",
    "🧟🦸🦹🧙👸",
    "🧅🍠🥕🌽🥦",
    "🐷🐹🐭🐨🐻‍❄️",
    "🦋🐇🐀🐈🐈‍⬛",
    "🌼🌳🌲🌴🌵",
    "🥩🍋🍐🍈🍇",
    "🍴🍽️🔪🍶🥃",
    "🕌🏰🏩⛩️🏩",
    "🎉🎊🎈🎂🎀",
    "🪴🌵🌴🌳🌲",
    "🎄🎋🎍🎑🎎",
    "🦅🦜🕊️🦤🦢",
    "🦤🦩🦚🦃🦆",
    "🐬🦭🦈🐋🐳",
    "🐔🐟🐠🐡🦐",
    "🦩🦀🦑🐙🦪",
    "🐦🦂🕷️🕸️🐚",
    "🥪🍰🥧🍨🍨",
    "🥬🍉🧁🧇🤍",
]

async def is_admin(chat_id, user_id):
    admin_ids = [
        admin.user.id
        async for admin in app.get_chat_members(
            chat_id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]
    return user_id in admin_ids

async def process_members(chat_id, members, text=None, replied=None):
    tagged_members = 0
    usernum = 0
    usertxt = ""
    emoji_sequence = random.choice(EMOJI)
    emoji_index = 0
    
    # Filter out deleted and bot accounts first
    valid_members = []
    for member in members:
        if not member.user.is_deleted and not member.user.is_bot:
            valid_members.append(member)
    
    total_valid_members = len(valid_members)
    
    for member in valid_members:
        # Check if tagging is still active
        if chat_id not in SPAM_CHATS:
            break
            
        tagged_members += 1
        usernum += 1
        
        # Get emoji from current sequence
        emoji = emoji_sequence[emoji_index % len(emoji_sequence)]
        usertxt += f'<a href="tg://user?id={member.user.id}">{emoji}</a> '
        emoji_index += 1
        
        # Send message when we reach 5 users OR it's the last batch
        if usernum == 5 or tagged_members == total_valid_members:
            try:
                if replied:
                    await replied.reply_text(
                        usertxt,
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    separator = "\n‎\n"
                    message_content = f"<b>{text}</b>{separator}{usertxt}" if text else usertxt
                    await app.send_message(
                        chat_id,
                        message_content,
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML
                    )
                
                # Reset for next batch
                usernum = 0
                usertxt = ""
                emoji_sequence = random.choice(EMOJI)
                emoji_index = 0
                
                # Add delay to prevent flooding
                await asyncio.sleep(3)
                
            except FloodWait as e:
                await asyncio.sleep(e.value + 3)
            except Exception as e:
                await app.send_message(chat_id, f"Error while tagging: {str(e)}")
                continue
    
    return tagged_members

@app.on_message(
    filters.command(["all", "allmention", "mentionall", "tagall"], prefixes=["/", "@"])
)
async def tag_all_users(_, message):
    admin = await is_admin(message.chat.id, message.from_user.id)
    if not admin:
        return await message.reply_text("Only admins can use this command.")

    if message.chat.id in SPAM_CHATS:  
        return await message.reply_text("Tagging process is already running. Use /cancel to stop it.")  
    
    replied = message.reply_to_message  
    if len(message.command) < 2 and not replied:  
        return await message.reply_text("Give some text to tag all, like: `@all Hi Friends`")  
    
    try:  
        # Get all members
        members = []
        async for m in app.get_chat_members(message.chat.id):
            members.append(m)
        
        # Count valid members (non-deleted, non-bot)
        valid_members = [m for m in members if not m.user.is_deleted and not m.user.is_bot]
        total_members = len(members)
        valid_count = len(valid_members)
        
        SPAM_CHATS.append(message.chat.id)
        
        text = None
        if not replied:
            text = message.text.split(None, 1)[1].strip()
        
        # Send initial message
        start_msg = f"🔄 Starting to tag {valid_count} valid members..."
        await app.send_message(message.chat.id, start_msg)
        
        tagged_members = await process_members(
            message.chat.id,
            members,
            text=text,
            replied=replied
        )
        
        # Send completion summary
        summary_msg = f"""
✅ Tagging completed!

Total members: {total_members}
Valid members: {valid_count}
Tagged members: {tagged_members}
Skipped (bots/deleted): {total_members - valid_count}
"""
        await app.send_message(message.chat.id, summary_msg)

    except FloodWait as e:  
        await asyncio.sleep(e.value + 3)  
    except Exception as e:  
        await app.send_message(message.chat.id, f"An error occurred: {str(e)}")  
    finally:  
        try:  
            SPAM_CHATS.remove(message.chat.id)  
        except Exception:  
            pass

@app.on_message(
    filters.command(["admintag", "adminmention", "admins", "report"], prefixes=["/", "@"])
)
async def tag_all_admins(_, message):
    if not message.from_user:
        return

    admin = await is_admin(message.chat.id, message.from_user.id)  
    if not admin:  
        return await message.reply_text("Only admins can use this command.")  

    if message.chat.id in SPAM_CHATS:  
        return await message.reply_text("Tagging process is already running. Use /cancel to stop it.")  
    
    replied = message.reply_to_message  
    if len(message.command) < 2 and not replied:  
        return await message.reply_text("Give some text to tag admins, like: `@admins Hi Friends`")  
    
    try:  
        # Get all admin members
        members = []
        async for m in app.get_chat_members(
            message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS  
        ):
            members.append(m)
        
        # Count valid admins (non-deleted, non-bot)
        valid_admins = [m for m in members if not m.user.is_deleted and not m.user.is_bot]
        total_admins = len(members)
        valid_count = len(valid_admins)
        
        SPAM_CHATS.append(message.chat.id)
        
        text = None
        if not replied:
            text = message.text.split(None, 1)[1].strip()
        
        # Send initial message
        start_msg = f"🔄 Starting to tag {valid_count} valid admins..."
        await app.send_message(message.chat.id, start_msg)
        
        tagged_admins = await process_members(
            message.chat.id,
            members,
            text=text,
            replied=replied
        )
        
        # Send completion summary
        summary_msg = f"""
✅ Admin tagging completed!

Total admins: {total_admins}
Valid admins: {valid_count}
Tagged admins: {tagged_admins}
Skipped (bots/deleted): {total_admins - valid_count}
"""
        await app.send_message(message.chat.id, summary_msg)

    except FloodWait as e:  
        await asyncio.sleep(e.value + 3)  
    except Exception as e:  
        await app.send_message(message.chat.id, f"An error occurred: {str(e)}")  
    finally:  
        try:  
            SPAM_CHATS.remove(message.chat.id)  
        except Exception:  
            pass

@app.on_message(
    filters.command(
        [
            "stopmention",
            "cancel",
            "cancelmention",
            "offmention",
            "mentionoff",
            "cancelall",
        ],
        prefixes=["/", "@"],
    )
)
async def cancelcmd(_, message):
    chat_id = message.chat.id
    admin = await is_admin(chat_id, message.from_user.id)
    if not admin:
        return await message.reply_text("Only admins can use this command.")

    if chat_id in SPAM_CHATS:  
        try:  
            SPAM_CHATS.remove(chat_id)  
        except Exception:  
            pass  
        return await message.reply_text("Tagging process successfully stopped!")  
    else:  
        return await message.reply_text("No tagging process is currently running!")

MODULE = "Tᴀɢᴀʟʟ"
HELP = """
@all or /all | /tagall or @tagall | /mentionall or @mentionall [text] or [reply to any message] - Tag all users in your group with random emojis (changes every 5 users)

/admintag or @admintag | /adminmention or @adminmention | /admins or @admins [text] or [reply to any message] - Tag all admins in your group with random emojis (changes every 5 users)

/stopmention or @stopmention | /cancel or @cancel | /offmention or @offmention | /mentionoff or @mentionoff | /cancelall or @cancelall - Stop any running tagging process

Note:
1. These commands can only be used by admins
2. The bot must be admin in your group
3. Users will be tagged with clickable emoji links
4. Tags exactly 5 users at a time with unique emoji sequence
5. Includes summary after completion
6. Automatically skips bots and deleted accounts
"""
