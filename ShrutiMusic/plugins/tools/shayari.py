import random
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShrutiMusic import app
from ShrutiMusic.utils.database import get_served_chats

# Dictionary to track user command usage for anti-spam
user_last_command_time = {}
user_command_count = {}
# Anti-spam settings
SPAM_THRESHOLD = 3  # Maximum commands allowed in time window
SPAM_WINDOW_SECONDS = 10  # Time window in seconds
COOLDOWN_TIME = 15  # Cooldown time in seconds

# Beautiful emojis and dividers for decoration
DECORATIVE_EMOJIS = ["✨", "💫", "🌟", "⭐", "🌠", "🌸", "🌺", "🌹", "💮", "🏵️", "🌻", "🥀", "💐"]
DIVIDERS = [
    "•✦───────────•✧•───────────✦•",
    "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
    "❃───•*¨*•.¸¸❁¸¸.•*¨*•───❃",
    "╭────────────────────╮",
    "ღ¸.•´.¸.•´¯`•.¸¸.•❤",
    "•° ★ °•",
    "═════════════",
    "─────※ ·❆· ※─────",
]

# Improved Shayari collection with better formatting
SHAYRI = [
    f"""╔══════════════════╗
☘️ <b>बहुत अच्छा लगता है तुझे सताना और फिर प्यार से तुझे मनाना।</b> ☘️

🥀 <b>Bahut aacha lagta hai tujhe satana Aur fir pyar se tujhe manana.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>मेरी जिंदगी मेरी जान हो तुम मेरे सुकून का दुसरा नाम हो तुम।</b> ☘️

🥀 <b>Meri zindagi Meri jaan ho tum Mere sukoon ka Dusra naam ho tum.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>तुम मेरी वो खुशी हो जिसके बिना, मेरी सारी खुशी अधूरी लगती है।</b> ☘️

🥀 <b>Tum Meri Wo Khushi Ho Jiske Bina, Meri Saari Khushi Adhuri Lagti Ha.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>काश वो दिन जल्दी आए, जब तू मेरे साथ सात फेरो में बन्ध जाए।</b> ☘️

🥀 <b>Kash woh din jldi aaye Jb tu mere sath 7 feron me bndh jaye.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>अपना हाथ मेरे दिल पर रख दो और अपना दिल मेरे नाम कर दो।</b> ☘️

🥀 <b>Apna hath mere dil pr rakh do aur apna dil mere naam kar do.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>महादेव ना कोई गाड़ी ना कोई बंगला चाहिए सलामत रहे मेरा प्यार बस यही दुआ चाहिए।</b> ☘️

🥀 <b>Mahadev na koi gadi na koi bangla chahiye salamat rhe mera pyar bas yahi dua chahiye.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>फिक्र तो होगी ना तुम्हारी इकलौती मोहब्बत हो तुम मेरी।</b> ☘️

🥀 <b>Fikr to hogi na tumhari ikloti mohabbat ho tum meri.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>सुनो जानू आप सिर्फ किचन संभाल लेना आप को संभालने के लिए मैं हूं ना।</b> ☘️

🥀 <b>Suno jaanu aap sirf kitchen sambhal lena ap ko sambhlne ke liye me hun naa.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>सौ बात की एक बात मुझे चाहिए बस तेरा साथ।</b> ☘️

🥀 <b>So bat ki ek bat mujhe chahiye bas tera sath.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>बहुत मुश्किलों से पाया हैं तुम्हें, अब खोना नहीं चाहते, कि तुम्हारे थे तुम्हारे हैं अब किसी और के होना नहीं चाहते।</b> ☘️

🥀 <b>Bahut muskilon se paya hai tumhe Ab khona ni chahte ki tumhare they tumhare hai ab kisi or k hona nhi chahte.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>बेबी बातें तो रोज करते है चलो आज रोमांस करते है。</b> ☘️

🥀 <b>Baby baten to roj karte hai chalo aaj romance karte hai..</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>सुबह शाम तुझे याद करते है हम और क्या बताएं की तुमसे कितना प्यार करते है हम。</b> ☘️

🥀 <b>Subha sham tujhe yad karte hai hum aur kya batayen ki tumse kitna pyar karte hai hum.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>किसी से दिल लग जाने को मोहब्बत नहीं कहते जिसके बिना दिल न लगे उसे मोहब्बत कहते हैं。</b> ☘️

🥀 <b>Kisi se dil lag jane ko mohabbat nahi kehte jiske nina dil na lage use mohabbat kehte hai.</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>मेरे दिल के लॉक की चाबी हो तुम क्या बताएं जान मेरे जीने की एकलौती वजह हो तुम。</b> ☘️

🥀 <b>Mere dil ke lock ki chabi ho tum kya batayen jaan mere jeene ki eklauti wajah ho tum..</b> 🥀
╚══════════════════╝""",
    
    f"""╔══════════════════╗
☘️ <b>हम आपकी हर चीज़ से प्यार कर लेंगे, आपकी हर बात पर ऐतबार कर लेंगे, बस एक बार कह दो कि तुम सिर्फ मेरे हो, हम ज़िन्दगी भर आपका इंतज़ार कर लेंगे。</b> ☘️

🥀 <b>Hum apki har cheez se pyar kar lenge apki har baat par etvar kar lenge bas ek bar keh do ki tum sirf mere ho hum zindagi bhar apka intzaar kar lenge..</b> 🥀
╚══════════════════╝""",
]

# Command
SHAYRI_COMMAND = ["gf", "bf", "shayri", "sari", "shari", "love", "shayari"]

# Random emoji selector function
def get_random_emoji_pair():
    emoji = random.choice(DECORATIVE_EMOJIS)
    return emoji, emoji

# Random divider selector function
def get_random_divider():
    return random.choice(DIVIDERS)

# Anti-spam function
def is_spam(user_id):
    current_time = time.time()
    
    # Initialize if user not in dictionary
    if user_id not in user_last_command_time:
        user_last_command_time[user_id] = current_time
        user_command_count[user_id] = 1
        return False
    
    # Check if user is in cooldown
    time_diff = current_time - user_last_command_time[user_id]
    
    # Reset if window has passed
    if time_diff > SPAM_WINDOW_SECONDS:
        user_last_command_time[user_id] = current_time
        user_command_count[user_id] = 1
        return False
    
    # Increment command count
    user_command_count[user_id] += 1
    
    # Check if spam threshold reached
    if user_command_count[user_id] > SPAM_THRESHOLD:
        user_last_command_time[user_id] = current_time  # Start cooldown
        return True
    
    return False

# Command handlers with enhanced visual output
@app.on_message(filters.command(SHAYRI_COMMAND) & filters.group)
async def shayari_group(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check for spam
    if is_spam(user_id):
        cooldown_msg = f"<b>⚠️ Spam detected!</b> Please wait {COOLDOWN_TIME} seconds before using this command again."
        await message.reply_text(cooldown_msg)
        return
    
    # Get stylish components
    divider = get_random_divider()
    start_emoji, end_emoji = get_random_emoji_pair()
    
    # Create stylish header
    header = f"{divider}\n{start_emoji} <b>𝓢𝓱𝓪𝔂𝓪𝓻𝓲 𝓕𝓸𝓻 𝓨𝓸𝓾</b> {end_emoji}\n{divider}"
    
    # Get random shayari
    selected_shayari = random.choice(SHAYRI)
    
    # Create footer
    footer = f"{divider}\n💌 <b>𝓢𝓱𝓪𝓻𝓮𝓭 𝓦𝓲𝓽𝓱 𝓛𝓸𝓿𝓮</b> 💌\n{divider}"
    
    # Combine all components
    complete_message = f"{header}\n\n{selected_shayari}\n\n{footer}"
    
    # Create stylish inline keyboard
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❣️ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❣️", url="https://t.me/ShrutiBotSupport"),
                InlineKeyboardButton("💖 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 💖", url="https://t.me/ShrutiBots")
            ],
            [
                InlineKeyboardButton("🎁 𝐌𝐨𝐫𝐞 𝐒𝐡𝐚𝐲𝐚𝐫𝐢 🎁", callback_data="more_shayari")
            ]
        ]
    )
    
    await message.reply_text(
        text=complete_message,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@app.on_message(filters.command(SHAYRI_COMMAND) & filters.private)
async def shayari_private(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check for spam
    if is_spam(user_id):
        cooldown_msg = f"<b>⚠️ Spam detected!</b> Please wait {COOLDOWN_TIME} seconds before using this command again."
        await message.reply_text(cooldown_msg)
        return
    
    # Get stylish components
    divider = get_random_divider()
    start_emoji, end_emoji = get_random_emoji_pair()
    
    # Create stylish header
    header = f"{divider}\n{start_emoji} <b>Shayri For You</b> {end_emoji}\n{divider}"
    
    # Get random shayari
    selected_shayari = random.choice(SHAYRI)
    
    # Create footer
    footer = f"{divider}\n💌 <b>Shared with Love</b> 💌\n{divider}"
    
    # Combine all components
    complete_message = f"{header}\n\n{selected_shayari}\n\n{footer}"
    
    # Create stylish inline keyboard
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❣️ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❣️", url="https://t.me/ShrutiBotSupport"),
                InlineKeyboardButton("💖 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 💖", url="https://t.me/ShrutiBots")
            ],
            [
                InlineKeyboardButton("🎁 𝐌𝐨𝐫𝐞 𝐒𝐡𝐚𝐲𝐚𝐫𝐢 🎁", callback_data="more_shayari")
            ]
        ]
    )
    
    await message.reply_text(
        text=complete_message,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# Callback handler for "More Shayari" button
@app.on_callback_query(filters.regex("more_shayari"))
async def more_shayari_callback(client, callback_query):
    user_id = callback_query.from_user.id
    
    # Check for spam
    if is_spam(user_id):
        await callback_query.answer("Please wait a moment before requesting more shayari.", show_alert=True)
        return
    
    # Get stylish components
    divider = get_random_divider()
    start_emoji, end_emoji = get_random_emoji_pair()
    
    # Create stylish header
    header = f"{divider}\n{start_emoji} <b>New Shayri For You</b> {end_emoji}\n{divider}"
    
    # Get random shayari (different from previous)
    selected_shayari = random.choice(SHAYRI)
    
    # Create footer
    footer = f"{divider}\n💌 <b>Shared with Love</b> 💌\n{divider}"
    
    # Combine all components
    complete_message = f"{header}\n\n{selected_shayari}\n\n{footer}"

    # Create stylish inline keyboard
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❣️ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 ❣️", url="https://t.me/ShrutiBotSupport"),
                InlineKeyboardButton("💖 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 💖", url="https://t.me/ShrutiBots")
            ],
            [
                InlineKeyboardButton("🎁 𝐌𝐨𝐫𝐞 𝐒𝐡𝐚𝐲𝐚𝐫𝐢 🎁", callback_data="more_shayari")
            ]
        ]
    )
    
    try:
        await callback_query.edit_message_text(
            text=complete_message,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        await callback_query.answer("Enjoy your new shayari! ❤️")
    except Exception as e:
        await callback_query.answer("Something went wrong. Please try again.")

# Module info
__MODULE__ = "Shayari"
__HELP__ = """
/gf, /bf, /shayri, /shayari, /sari, /shari, /love: 

✨ <b>Get a beautifully formatted random Shayari</b> ✨

📋 <b>Features:</b>
• Stylish formatting with decorative elements
• "More Shayari" button to get a new shayari instantly
• Works in both private and group chats
• Anti-spam protection to prevent abuse

💫 <b>Usage:</b> Simply send any of the commands listed above and enjoy a beautiful shayari!
"""
