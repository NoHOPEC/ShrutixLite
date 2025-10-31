import os
from unidecode import unidecode
from PIL import ImageDraw, Image, ImageFont, ImageChops
from pyrogram import *
from pyrogram.types import *
from logging import getLogger
from ShrutiMusic import LOGGER
from pyrogram.types import Message
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic import app
from ShrutiMusic.utils.database import *
from ShrutiMusic.utils.database import db
from ShrutiMusic.core.mongo import mongodb

# Welcome collection
try:
    wlcm = db.welcome
except:
    # Alternative database import
    from ShrutiMusic.utils.database import welcome as wlcm

# Custom welcome messages collection
welcome_db = mongodb.welcome_messages

LOGGER = getLogger(__name__)

class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None

def circle(pfp, size=(450, 450)):
    pfp = pfp.resize(size, Image.LANCZOS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

def welcomepic(pic, user, chat, id, uname):
    background = Image.open("ShrutiMusic/assets/welcome.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((450, 450)) 
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype('ShrutiMusic/assets/font.ttf', size=45)
    font2 = ImageFont.truetype('ShrutiMusic/assets/font.ttf', size=90)
    draw.text((65, 250), f'NAME : {unidecode(user)}', fill="white", font=font)
    draw.text((65, 340), f'ID : {id}', fill="white", font=font)
    draw.text((65, 430), f"USERNAME : {uname}", fill="white", font=font)
    pfp_position = (767, 133)  
    background.paste(pfp, pfp_position, pfp)  
    background.save(f"downloads/welcome#{id}.png")
    return f"downloads/welcome#{id}.png"

def format_welcome_message(text, user, chat):
    """Format welcome message with variables"""
    replacements = {
        '{mention}': user.mention,
        '{first_name}': user.first_name or "User",
        '{last_name}': user.last_name or "",
        '{username}': f"@{user.username}" if user.username else "No Username",
        '{user_id}': str(user.id),
        '{chat_title}': chat.title,
        '{chat_id}': str(chat.id)
    }
    
    for key, value in replacements.items():
        text = text.replace(key, value)
    
    return text

# Default welcome message
DEFAULT_WELCOME_MESSAGE = """
🌟 <b>ᴡᴇʟᴄᴏᴍᴇ {mention}!</b>

📋 <b>ɢʀᴏᴜᴘ:</b> {chat_title}
🆔 <b>ʏᴏᴜʀ ɪᴅ:</b> <code>{user_id}</code>
👤 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {username}

<u>ʜᴏᴘᴇ ʏᴏᴜ ғɪɴᴅ ɢᴏᴏᴅ ᴠɪʙᴇs, ɴᴇᴡ ғʀɪᴇɴᴅs, ᴀɴᴅ ʟᴏᴛs ᴏғ ғᴜɴ ʜᴇʀᴇ!</u> 🌟"""

# ✅ `/welcome` Command: Enable/Disable Special Welcome
@app.on_message(filters.command("welcome") & ~filters.private)
async def auto_state(_, message):
    usage = "<b>❖ ᴜsᴀɢᴇ ➥</b> /welcome [on|off]"
    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)

    if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        A = await wlcm.find_one({"chat_id": chat_id})
        state = message.text.split(None, 1)[1].strip().lower()

        if state == "on":
            if A and not A.get("disabled", False):
                return await message.reply_text("✦ Special Welcome Already Enabled")
            await wlcm.update_one({"chat_id": chat_id}, {"$set": {"disabled": False}}, upsert=True)
            await message.reply_text(f"✦ Enabled Special Welcome in {message.chat.title}")

        elif state == "off":
            if A and A.get("disabled", False):
                return await message.reply_text("✦ Special Welcome Already Disabled")
            await wlcm.update_one({"chat_id": chat_id}, {"$set": {"disabled": True}}, upsert=True)
            await message.reply_text(f"✦ Disabled Special Welcome in {message.chat.title}")

        else:
            await message.reply_text(usage)
    else:
        await message.reply("✦ Only Admins Can Use This Command")

# ✅ Set Custom Welcome Message
@app.on_message(filters.command("setwelcome") & ~filters.private)
async def set_welcome_message(_, message):
    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("✦ Only Admins Can Use This Command")
    
    if len(message.command) == 1:
        # Show help with formatting and usage info
        help_text = """
<b>✨ Custom Welcome Message Setup</b>

<b>📝 Usage:</b>
<code>/setwelcome Your custom welcome message here</code>

<b>🔗 Available Variables:</b>
• <code>{mention}</code> - Mention the user
• <code>{first_name}</code> - User's first name
• <code>{last_name}</code> - User's last name
• <code>{username}</code> - User's username
• <code>{user_id}</code> - User's ID
• <code>{chat_title}</code> - Group name
• <code>{chat_id}</code> - Group ID

<b>🎨 HTML Formatting Options:</b>
• <code>&lt;b&gt;bold&lt;/b&gt;</code> - <b>Bold text</b>
• <code>&lt;i&gt;italic&lt;/i&gt;</code> - <i>Italic text</i>
• <code>&lt;u&gt;underline&lt;/u&gt;</code> - <u>Underline text</u>
• <code>&lt;s&gt;strikethrough&lt;/s&gt;</code> - <s>Strikethrough</s>
• <code>&lt;code&gt;monospace&lt;/code&gt;</code> - <code>Monospace</code>
• <code>&lt;blockquote&gt;quote&lt;/blockquote&gt;</code> - Quote text
• <code>&lt;a href="URL"&gt;Text&lt;/a&gt;</code> - Links

<b>🔘 Inline Buttons:</b>
Use this format for buttons:
<code>[Button Text](buttonurl:https://example.com)</code>

<b>Multiple buttons:</b>
<code>[Button 1](buttonurl:https://example.com)
[Button 2](buttonurl:https://t.me/username)</code>

<b>Example:</b>
<code>🎉 Welcome {mention} to {chat_title}!

Your ID: {user_id}
Username: {username}

Enjoy your stay! 😊

[Group Rules](buttonurl:https://example.com/rules)
[Support](buttonurl:https://t.me/support)</code>
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Formatting Help", callback_data=f"format_help_{chat_id}"),
                InlineKeyboardButton("🔧 Usage Examples", callback_data=f"usage_help_{chat_id}")
            ],
            [InlineKeyboardButton("❌ Close", callback_data=f"close_help_{chat_id}")]
        ])
        
        return await message.reply(help_text, reply_markup=keyboard)
    
    # Get the welcome message (everything after /setwelcome)
    welcome_text = message.text.split(None, 1)[1]
    
    # Save to database
    await welcome_db.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "chat_id": chat_id,
                "message": welcome_text,
                "set_by": message.from_user.id,
                "chat_title": message.chat.title
            }
        },
        upsert=True
    )
    
    await message.reply(
        f"✅ <b>Custom welcome message set successfully!</b>\n\n"
        f"<b>Preview:</b>\n{format_welcome_message(welcome_text, message.from_user, message.chat)}\n\n"
        f"Use <code>/resetwelcome</code> to reset to default message."
    )

# ✅ Reset Welcome Message
@app.on_message(filters.command("resetwelcome") & ~filters.private)
async def reset_welcome_message(_, message):
    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("✦ Only Admins Can Use This Command")
    
    await welcome_db.delete_one({"chat_id": chat_id})
    await message.reply("✅ Welcome message reset to default!")

# ✅ Get Current Welcome Message
@app.on_message(filters.command("getwelcome") & ~filters.private)
async def get_welcome_message(_, message):
    chat_id = message.chat.id
    
    # Get custom welcome message
    custom_welcome = await welcome_db.find_one({"chat_id": chat_id})
    
    if custom_welcome:
        welcome_text = custom_welcome["message"]
        preview = format_welcome_message(welcome_text, message.from_user, message.chat)
        await message.reply(
            f"<b>📋 Current Welcome Message:</b>\n\n{preview}\n\n"
            f"<b>🔧 Raw Text:</b>\n<code>{welcome_text}</code>"
        )
    else:
        preview = format_welcome_message(DEFAULT_WELCOME_MESSAGE, message.from_user, message.chat)
        await message.reply(
            f"<b>📋 Current Welcome Message (Default):</b>\n\n{preview}"
        )

# ✅ Callback Query Handler for Help Buttons - FIXED BACK BUTTON
@app.on_callback_query(filters.regex(r"format_help_|usage_help_|close_help_|back_help_"))
async def help_callback(_, callback_query):
    data = callback_query.data
    chat_id = int(data.split("_")[-1])
    
    # Check if user is admin
    try:
        user = await app.get_chat_member(chat_id, callback_query.from_user.id)
        if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
            return await callback_query.answer("❌ Only admins can use this!", show_alert=True)
    except:
        return await callback_query.answer("❌ Error checking permissions!", show_alert=True)
    
    if "format_help" in data:
        format_help = """
<b>🎨 Advanced Formatting Guide</b>

<b>HTML Text Styles:</b>
• <code>&lt;b&gt;bold&lt;/b&gt;</code> → <b>Bold</b>
• <code>&lt;i&gt;italic&lt;/i&gt;</code> → <i>Italic</i>
• <code>&lt;u&gt;underline&lt;/u&gt;</code> → <u>Underline</u>
• <code>&lt;s&gt;strike&lt;/s&gt;</code> → <s>Strike</s>
• <code>&lt;code&gt;monospace&lt;/code&gt;</code> → <code>Code</code>
• <code>&lt;blockquote&gt;quote&lt;/blockquote&gt;</code> → Quote

<b>Links:</b>
• <code>&lt;a href="URL"&gt;Text&lt;/a&gt;</code> → HTML link

<b>Buttons:</b>
• <code>[Button](buttonurl:URL)</code> → Single button
• Multiple buttons on same line: <code>[Btn1](buttonurl:URL1) [Btn2](buttonurl:URL2)</code>

<b>⚠️ Note:</b> Only use HTML formatting, no markdown supported!
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔧 Usage Examples", callback_data=f"usage_help_{chat_id}")],
            [InlineKeyboardButton("◀️ Back", callback_data=f"back_help_{chat_id}")]
        ])
        
        await callback_query.edit_message_text(format_help, reply_markup=keyboard)
    
    elif "usage_help" in data:
        usage_examples = """
<b>🔧 Usage Examples</b>

<b>Example 1 - Simple:</b>
<code>Hello {mention}! 
Welcome to {chat_title} 🎉
Your ID: {user_id}</code>

<b>Example 2 - With HTML Formatting:</b>
<code>🌟 &lt;b&gt;Welcome {mention}!&lt;/b&gt;

📋 &lt;b&gt;Group:&lt;/b&gt; {chat_title}
🆔 &lt;b&gt;Your ID:&lt;/b&gt; &lt;code&gt;{user_id}&lt;/code&gt;
👤 &lt;b&gt;Username:&lt;/b&gt; {username}

&lt;u&gt;Enjoy your stay!&lt;/u&gt; 😊</code>

<b>Example 3 - With Buttons:</b>
<code>🎉 Welcome {mention} to our family!

Thanks for joining &lt;b&gt;{chat_title}&lt;/b&gt;

[📜 Rules](buttonurl:https://example.com/rules)
[💬 Chat](buttonurl:https://t.me/mainchat) [📢 Channel](buttonurl:https://t.me/channel)</code>

<b>Example 4 - Advanced:</b>
<code>&lt;blockquote&gt;🎊 New member alert!&lt;/blockquote&gt;

&lt;b&gt;Hello {mention}!&lt;/b&gt; 👋

You're member number &lt;b&gt;#{user_id}&lt;/b&gt; in &lt;u&gt;{chat_title}&lt;/u&gt;!

&lt;code&gt;Tip: Read our rules first!&lt;/code&gt;

[🤖 Bot Commands](buttonurl:https://t.me/botusername?start=help)</code>
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Formatting", callback_data=f"format_help_{chat_id}")],
            [InlineKeyboardButton("◀️ Back", callback_data=f"back_help_{chat_id}")]
        ])
        
        await callback_query.edit_message_text(usage_examples, reply_markup=keyboard)
    
    elif "close_help" in data:
        await callback_query.message.delete()
    
    elif "back_help" in data:
        # Return to main help - FIXED BACK BUTTON
        help_text = """
<b>✨ Custom Welcome Message Setup</b>

<b>📝 Usage:</b>
<code>/setwelcome Your custom welcome message here</code>

<b>🔗 Available Variables:</b>
• <code>{mention}</code> - Mention the user
• <code>{first_name}</code> - User's first name
• <code>{last_name}</code> - User's last name
• <code>{username}</code> - User's username
• <code>{user_id}</code> - User's ID
• <code>{chat_title}</code> - Group name
• <code>{chat_id}</code> - Group ID

<b>🎨 HTML Formatting Options:</b>
• <code>&lt;b&gt;bold&lt;/b&gt;</code> - <b>Bold text</b>
• <code>&lt;i&gt;italic&lt;/i&gt;</code> - <i>Italic text</i>
• <code>&lt;u&gt;underline&lt;/u&gt;</code> - <u>Underline text</u>
• <code>&lt;s&gt;strikethrough&lt;/s&gt;</code> - <s>Strikethrough</s>
• <code>&lt;code&gt;monospace&lt;/code&gt;</code> - <code>Monospace</code>
• <code>&lt;blockquote&gt;quote&lt;/blockquote&gt;</code> - Quote text
• <code>&lt;a href="URL"&gt;Text&lt;/a&gt;</code> - Links

<b>🔘 Inline Buttons:</b>
Use this format for buttons:
<code>[Button Text](buttonurl:https://example.com)</code>

Use the buttons below for detailed help!
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Formatting Help", callback_data=f"format_help_{chat_id}"),
                InlineKeyboardButton("🔧 Usage Examples", callback_data=f"usage_help_{chat_id}")
            ],
            [InlineKeyboardButton("❌ Close", callback_data=f"close_help_{chat_id}")]
        ])
        
        await callback_query.edit_message_text(help_text, reply_markup=keyboard)

    await callback_query.answer()  # Important: Answer the callback query

def parse_buttons(text):
    """Parse buttons from welcome message"""
    import re
    
    # Find all button patterns
    button_pattern = r'\[([^\]]+)\]\(buttonurl:([^)]+)\)'
    buttons = re.findall(button_pattern, text)
    
    # Remove button syntax from text
    clean_text = re.sub(button_pattern, '', text).strip()
    
    if not buttons:
        return clean_text, None
    
    # Create keyboard
    keyboard = []
    row = []
    
    for button_text, button_url in buttons:
        row.append(InlineKeyboardButton(button_text.strip(), url=button_url.strip()))
        
        # Check if we should start a new row (you can customize this logic)
        if len(row) >= 2:  # Max 2 buttons per row
            keyboard.append(row)
            row = []
    
    # Add remaining buttons
    if row:
        keyboard.append(row)
    
    # Add default "Add Me" button
    keyboard.append([InlineKeyboardButton(f"ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ", url=f"https://t.me/{app.username}?startgroup=True")])
    
    return clean_text, InlineKeyboardMarkup(keyboard)

# ✅ Special Welcome Message (By Default ON)
@app.on_chat_member_updated(filters.group, group=-3)
async def greet_group(_, member: ChatMemberUpdated):
    chat_id = member.chat.id
    A = await wlcm.find_one({"chat_id": chat_id})

    # ✅ Default ON: Lekin agar disable kiya gaya hai to OFF rahe
    if A and A.get("disabled", False):  
        return  # Agar OFF hai, to kuch mat karo

    if (
        not member.new_chat_member
        or member.new_chat_member.status in {"banned", "left", "restricted"}
        or member.old_chat_member
    ):
        return

    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    try:
        pic = await app.download_media(
            user.photo.big_file_id, file_name=f"pp{user.id}.png"
        )
    except AttributeError:
        pic = "ShrutiMusic/assets/upic.png"

    if (temp.MELCOW).get(f"welcome-{member.chat.id}") is not None:
        try:
            await temp.MELCOW[f"welcome-{member.chat.id}"].delete()
        except Exception as e:
            LOGGER.error(e)

    try:
        # Get custom welcome message or use default
        custom_welcome = await welcome_db.find_one({"chat_id": chat_id})
        
        if custom_welcome:
            welcome_text = custom_welcome["message"]
        else:
            welcome_text = DEFAULT_WELCOME_MESSAGE
        
        # Format the message
        formatted_message = format_welcome_message(welcome_text, user, member.chat)
        
        # Parse buttons from message
        final_message, keyboard = parse_buttons(formatted_message)
        
        # If no custom keyboard, use default
        if keyboard is None:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ", url=f"https://t.me/{app.username}?startgroup=True")]
            ])
        
        welcomeimg = welcomepic(
            pic, user.first_name, member.chat.title, user.id, user.username
        )
        
        temp.MELCOW[f"welcome-{member.chat.id}"] = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=final_message,
            reply_markup=keyboard,
        )

    except Exception as e:
        LOGGER.error(f"Welcome error: {e}")

    try:
        os.remove(f"downloads/welcome#{user.id}.png")
        os.remove(f"downloads/pp{user.id}.png")
    except Exception:
        pass

# ✅ Welcome Commands Help
@app.on_message(filters.command("welcomehelp") & ~filters.private)
async def welcome_help(_, message):
    help_text = """
<b>🎉 Welcome System Commands</b>

<b>👥 For Admins:</b>
• <code>/welcome on</code> - Enable welcome messages
• <code>/welcome off</code> - Disable welcome messages
• <code>/setwelcome &lt;message&gt;</code> - Set custom welcome
• <code>/resetwelcome</code> - Reset to default
• <code>/getwelcome</code> - View current message
• <code>/welcomehelp</code> - Show this help

<b>🔧 Custom Message Features:</b>
✅ Custom text with variables
✅ HTML formatting support  
✅ Custom inline buttons
✅ Per-group settings
✅ Easy setup with help buttons

Use <code>/setwelcome</code> without parameters to see detailed setup guide!
    """
    
    await message.reply(help_text)
