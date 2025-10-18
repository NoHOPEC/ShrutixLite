from pyrogram import filters
from ShrutiMusic import app
import random

# List of alone GIF URLs
alone_gifs = [
    "https://envs.sh/kHZ.mp4",
    "https://envs.sh/kHc.mp4",
    "https://envs.sh/kmC.mp4",
    "https://envs.sh/km4.mp4",
    "https://envs.sh/kml.mp4",
    "https://envs.sh/kmk.mp4",
    "https://envs.sh/kmJ.mp4",
    "https://envs.sh/kmo.mp4",
    "https://envs.sh/kms.mp4",
    "https://envs.sh/km9.mp4",
    "https://envs.sh/kmN.mp4",

]

# List of sad GIF URLs
sad_gifs = [
    "https://envs.sh/kma.mp4",
    "https://envs.sh/kHC.mp4",
    "https://envs.sh/kmy.mp4",
    "https://envs.sh/kmx.mp4",
    "https://envs.sh/km-.mp4",
    "https://envs.sh/kMQ.mp4",
    "https://envs.sh/kM2.mp4",
    "https://envs.sh/kMF.mp4",
    "https://envs.sh/kMb.mp4",

]

# List of happy GIF URLs
happy_gifs = [
    "https://envs.sh/kMG.mp4",
    "https://envs.sh/kMz.mp4",
    "https://envs.sh/kMY.mp4",
    "https://envs.sh/kM4.mp4",
    "https://envs.sh/kMo.mp4",
    "https://envs.sh/kMH.mp4",
]

@app.on_message(filters.command("alone"))
async def alone(client, message):
    try:
        alone_gif_url = random.choice(alone_gifs)  # Choose a random alone GIF
        if message.reply_to_message:
            await message.reply_animation(
                alone_gif_url,
                caption=f"{message.from_user.mention} ɪs ғᴇᴇʟɪɴɢ ᴀʟᴏɴᴇ."
            )
        else:
            await message.reply_animation(alone_gif_url)
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("sad"))
async def sad(client, message):
    try:
        sad_gif_url = random.choice(sad_gifs)  # Choose a random sad GIF
        if message.reply_to_message:
            await message.reply_animation(
                sad_gif_url,
                caption=f"{message.from_user.mention} ɪs ғᴇᴇʟɪɴɢ sᴀᴅ."
            )
        else:
            await message.reply_animation(sad_gif_url)
    except Exception as e:
        await message.reply_text(f"Error: {e}")  

@app.on_message(filters.command("happy"))
async def happy(client, message):
    try:
        happy_gif_url = random.choice(happy_gifs)  # Choose a random happy GIF
        if message.reply_to_message:
            await message.reply_animation(
                happy_gif_url,
                caption=f"{message.from_user.mention} ɪs ғᴇᴇʟɪɴɢ ʜᴀᴘᴘʏ."
            )
        else:
            await message.reply_animation(happy_gif_url)
    except Exception as e:
        await message.reply_text(f"Error: {e}")          
