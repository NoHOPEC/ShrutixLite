from pyrogram import filters
from pyrogram.types import Message
import os

from ShrutiMusic import app
from ShrutiMusic.platforms.Carbon import CarbonAPI, UnableToFetchCarbon


carbon = CarbonAPI()


@app.on_message(filters.command("carbon"))
async def carbon_func(client, message: Message):
    user_id = message.from_user.id if message.from_user else 0

    # Check if reply or text given
    if message.reply_to_message:
        if message.reply_to_message.text:
            code_text = message.reply_to_message.text
        elif message.reply_to_message.document:
            # File case (text file only)
            doc = message.reply_to_message.document
            if not doc.file_name.endswith((".txt", ".py", ".js", ".html", ".css")):
                return await message.reply("❌ Only text/code files are supported.")
            file_path = await message.reply_to_message.download()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code_text = f.read()
            except Exception as e:
                return await message.reply(f"❌ Unable to read file:\n{e}")
            os.remove(file_path)
        else:
            return await message.reply("❌ Reply to a code message or a text file.")
    else:
        # If user passed code after /carbon
        if len(message.command) < 2:
            return await message.reply("⚡ Reply to a code or give code with command:\n`/carbon <code>`")
        code_text = message.text.split(None, 1)[1]

    m = await message.reply("🎨 Generating Carbon image...")

    try:
        img_path = await carbon.generate(code_text, user_id)
    except UnableToFetchCarbon:
        return await m.edit("❌ Unable to connect Carbon API.")
    except Exception as e:
        return await m.edit(f"❌ Error: {e}")

    await message.reply_photo(img_path, caption="✅ Here is your Carbon image!")
    await m.delete()

    # Remove cached image
    if os.path.exists(img_path):
        os.remove(img_path)
