import os
import json
import time
import asyncio
import requests
import logging
from datetime import datetime

from pyrogram import filters
from ShrutiMusic import app

# ---- Config ----
API_KEY = "83d3286180063306e0a9417f93612b6184b739732433bd42a286072f16299b17"

# ---- Logging ----
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---- Animation Frames ----
LOADING_FRAMES = [
    "🎨 Creating your masterpiece ⚪⚪⚪⚪⚪",
    "🎨 Creating your masterpiece 🔴⚪⚪⚪⚪",
    "🎨 Creating your masterpiece 🔴🔴⚪⚪⚪",
    "🎨 Creating your masterpiece 🔴🔴🔴⚪⚪",
    "🎨 Creating your masterpiece 🔴🔴🔴🔴⚪",
    "🎨 Creating your masterpiece 🔴🔴🔴🔴🔴",
    "✨ Almost ready... 🎭",
    "🌟 Final touches... 🖼️",
]

# ---- Sample Prompts ----
SAMPLE_PROMPTS = {
    "spiritual": [
        "Beautiful Radhe Krishna in divine garden, golden light, peaceful atmosphere",
        "Lord Ganesha blessing, lotus flowers, divine aura, vibrant colors",
        "Goddess Durga riding lion, powerful stance, celestial background"
    ],
    "nature": [
        "Sunset over mountains, golden hour, serene lake reflection",
        "Cherry blossom tree, pink petals falling, peaceful garden",
        "Northern lights dancing over snowy landscape"
    ],
    "fantasy": [
        "Magical fairy in enchanted forest, glowing wings, mystical light",
        "Dragon soaring through clouds, majestic wings spread",
        "Crystal castle floating in the sky, rainbow bridge"
    ],
    "anime": [
        "Cute anime girl with blue hair, school uniform, cherry blossoms",
        "Powerful anime warrior with glowing sword, action pose",
        "Peaceful anime character meditating under waterfall"
    ]
}

# ---- Helper Functions ----
async def animate_loading(message, prompt):
    for frame in LOADING_FRAMES:
        try:
            await message.edit_text(f"{frame}\n\n🖼️ <b>Prompt:</b> <code>{prompt[:50]}{'...' if len(prompt) > 50 else ''}</code>")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Animation error: {e}")
            break

# ---- Rate Limiting ----
user_last_request = {}
REQUEST_COOLDOWN = 30

def check_rate_limit(user_id):
    current_time = time.time()
    if user_id in user_last_request:
        if current_time - user_last_request[user_id] < REQUEST_COOLDOWN:
            remaining = REQUEST_COOLDOWN - (current_time - user_last_request[user_id])
            return False, remaining
    user_last_request[user_id] = current_time
    return True, 0

# ---- Main Generate Function ----
@app.on_message(filters.command(["gen", "generate"]))
async def generate(_, message):
    # Delete the user's command message immediately
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

    can_proceed, remaining = check_rate_limit(message.from_user.id)
    if not can_proceed:
        error_msg = await message.reply_text(
            f"⏳ <b>Please wait {remaining:.1f} seconds before generating another image!</b>\n\n"
            f"🕐 <i>Cooldown helps maintain server stability</i>"
        )
        await asyncio.sleep(5)
        try:
            await error_msg.delete()
        except:
            pass
        return
    
    if len(message.command) < 2:
        help_text = """
❌ <b>Please provide a prompt!</b>

📝 <b>Usage:</b> <code>/gen your prompt here</code>

💡 <b>Example Prompts:</b>
🕉️ <b>Spiritual:</b> <code>/gen Beautiful Radhe Krishna in divine garden</code>
🌸 <b>Nature:</b> <code>/gen Sunset over mountains, golden hour</code>
🧚 <b>Fantasy:</b> <code>/gen Magical fairy in enchanted forest</code>
🎌 <b>Anime:</b> <code>/gen Cute anime girl with blue hair</code>

✨ <b>Tips for better results:</b>
• Be descriptive and specific
• Include colors, lighting, style
• Mention atmosphere/mood
• Add artistic style if needed

🤖 <b>Powered by @ShrutiBots</b>
        """
        help_msg = await message.reply_text(help_text)
        await asyncio.sleep(10)
        try:
            await help_msg.delete()
        except:
            pass
        return

    prompt = " ".join(message.command[1:])
    
    start_time = time.time()
    m = await message.reply_text(
        f"🎨 Starting generation...\n\n🖼️ <b>Prompt:</b> <code>{prompt}</code>", quote=True
    )

    try:
        animation_task = asyncio.create_task(animate_loading(m, prompt))
        url = "https://api.wavespeed.ai/api/v3/wavespeed-ai/flux-dev"
        headers = {"Content-Type": "application/json","Authorization": f"Bearer {API_KEY}"}
        payload = {
            "prompt": prompt,"size": "1024*1024","num_inference_steps": 28,
            "guidance_scale": 3.5,"num_images": 1,"output_format": "jpeg",
            "enable_base64_output": False,"enable_safety_checker": True,"enable_sync_mode": False,
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code != 200:
            animation_task.cancel()
            error_msg = await m.edit_text(f"❌ <b>API Error:</b> {response.status_code}")
            await asyncio.sleep(5)
            try:
                await error_msg.delete()
            except:
                pass
            return

        result = response.json()["data"]
        request_id = result["id"]
        result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
        headers = {"Authorization": f"Bearer {API_KEY}"}

        poll_count = 0
        while poll_count < 60:
            poll = requests.get(result_url, headers=headers, timeout=10)
            if poll.status_code != 200:
                animation_task.cancel()
                error_msg = await m.edit_text(f"❌ <b>Polling Error:</b> {poll.status_code}")
                await asyncio.sleep(5)
                try:
                    await error_msg.delete()
                except:
                    pass
                return
            
            res = poll.json()["data"]
            status = res["status"]
            poll_count += 1

            if status == "completed":
                animation_task.cancel()
                img_url = res["outputs"][0]
                # Simple caption with user mention only
                caption = f"Generated By {message.from_user.mention}"
                await message.reply_photo(photo=img_url, caption=caption)
                try: 
                    await m.delete()
                except: 
                    pass
                break
            elif status == "failed":
                animation_task.cancel()
                error_msg = await m.edit_text(f"❌ <b>Generation Failed:</b> <code>{res.get('error','Unknown error')}</code>")
                await asyncio.sleep(5)
                try:
                    await error_msg.delete()
                except:
                    pass
                return
            else:
                if poll_count % 5 == 0:
                    try:
                        await m.edit_text(
                            f"🔄 <b>Status:</b> {status.title()}\n\n🖼️ <b>Prompt:</b> <code>{prompt[:50]}{'...' if len(prompt) > 50 else ''}</code>\n\n⏱️ Elapsed: {time.time() - start_time:.1f}s"
                        )
                    except: 
                        pass
                await asyncio.sleep(1)
        else:
            animation_task.cancel()
            error_msg = await m.edit_text("⏰ <b>Generation timeout!</b>\n\n🔄 Try again with a simpler prompt.")
            await asyncio.sleep(5)
            try:
                await error_msg.delete()
            except:
                pass
    except Exception as e:
        logger.error("Error in generate(): %s", e, exc_info=True)
        try: 
            animation_task.cancel()
        except: 
            pass
        error_msg = await m.edit_text("⚠️ <b>Unexpected error occurred!</b>\n\n🔄 Please try again later.")
        await asyncio.sleep(5)
        try:
            await error_msg.delete()
        except:
            pass

# ---- Help Command ----
@app.on_message(filters.command(["genhelp", "prompthelp"]))
async def gen_help(_, message):
    help_text = "🎨 <b>Image Generation Guide - @ShrutiBots</b>\n\n📝 <b>Usage:</b>\n<code>/gen your detailed prompt</code>\n\n"
    for category, prompts in SAMPLE_PROMPTS.items():
        help_text += f"🎯 <b>{category.title()}:</b>\n"
        for i, prompt in enumerate(prompts, 1):
            help_text += f"{i}. <code>/gen {prompt}</code>\n"
        help_text += "\n"
    await message.reply_text(help_text)

# ---- Random Prompt ----
@app.on_message(filters.command(["randomprompt", "randgen"]))
async def random_prompt(_, message):
    import random
    category = random.choice(list(SAMPLE_PROMPTS.keys()))
    prompt = random.choice(SAMPLE_PROMPTS[category])
    await message.reply_text(
        f"🎲 <b>Random Prompt Suggestion:</b>\n\n<code>/gen {prompt}</code>\n\n🏷️ <b>Category:</b> {category.title()}"
    )

# ---- Stats ----
@app.on_message(filters.command(["genstats"]))
async def gen_stats(_, message):
    total_users = len(user_last_request)
    await message.reply_text(
        f"📊 <b>Generation Stats</b>\n👥 Users: {total_users}\n🎨 Status: Active\n⚡ API: Connected\n\n🤖 <b>@ShrutiBots</b>"
    )
