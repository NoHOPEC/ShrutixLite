from ShrutiMusic.core.userbot import assistants
from ShrutiMusic import userbot as us, app
from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic.misc import SUDOERS
from config import BANNED_USERS, OWNER_ID

@app.on_message(filters.command(["asspfp", "setpfp"]) & filters.user(OWNER_ID))
async def set_pfp(_, message: Message):
    if message.reply_to_message.photo:
        fuk = await message.reply_text("<b>ɴᴏ ᴄʜᴀɴɢɪɴɢ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ᴘʀᴏꜰɪʟᴇ ᴘɪᴄ...</b>")
        img = await message.reply_to_message.download()
        if 1 in assistants:
            ubot = us.one
        try:
            await ubot.set_profile_photo(photo=img)
            return await fuk.edit_text(
                f"<b>» {ubot.me.mention} ᴘʀᴏꜰɪʟᴇ ᴘɪᴄ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ..</b>"
            )
        except:
            return await fuk.edit_text("<b>ꜰᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ᴘʀᴏꜰɪʟᴇ ᴘɪᴄ.</b>")
    else:
        await message.reply_text(
            "<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ꜰᴏʀ ᴄʜᴀɴɢɪɴɢ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ᴘʀᴏꜰɪʟᴇ ᴘɪᴄ..</b>"
        )

@app.on_message(filters.command(["delpfp", "delasspfp"]) & filters.user(OWNER_ID))
async def del_pfp(_, message: Message):
    try:
        if 1 in assistants:
            ubot = us.one
        pfp = [p async for p in ubot.get_chat_photos("me")]
        await ubot.delete_profile_photos(pfp[0].file_id)
        return await message.reply_text("<b>ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ᴘʀᴏꜰɪʟᴇ ᴘɪᴄ.</b>")
    except Exception as ex:
        await message.reply_text("<b>ꜰᴀɪʟᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ᴘʀᴏꜰɪʟᴇ ᴘɪᴄ.</b>")

@app.on_message(filters.command(["assbio", "setbio"]) & filters.user(OWNER_ID))
async def set_bio(_, message: Message):
    msg = message.reply_to_message
    if msg and msg.text:
        newbio = msg.text
        if 1 in assistants:
            ubot = us.one
        await ubot.update_profile(bio=newbio)
        return await message.reply_text(f"<b>» {ubot.me.mention} ʙɪᴏ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ.</b>")
    elif len(message.command) != 1:
        newbio = message.text.split(None, 1)[1]
        if 1 in assistants:
            ubot = us.one
        await ubot.update_profile(bio=newbio)
        return await message.reply_text(f"<b>» {ubot.me.mention} ʙɪᴏ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ.</b>")
    else:
        return await message.reply_text(
            "<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ sᴇᴛ ɪᴛ ᴀꜱ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ʙɪᴏ.</b>"
        )

@app.on_message(filters.command(["assname", "setname"]) & filters.user(OWNER_ID))
async def set_name(_, message: Message):
    msg = message.reply_to_message
    if msg and msg.text:
        name = msg.text
        if 1 in assistants:
            ubot = us.one
        await ubot.update_profile(first_name=name)
        return await message.reply_text(f"<b>» {ubot.me.mention} ɴᴀᴍᴇ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇssꜰᴜʟʟʏ.</b>")
    elif len(message.command) != 1:
        name = message.text.split(None, 1)[1]
        if 1 in assistants:
            ubot = us.one
        await ubot.update_profile(first_name=name, last_name="")
        return await message.reply_text(f"<b>» {ubot.me.mention} ɴᴀᴍᴇ ᴄʜᴀɴɢᴇᴅ ꜱᴜᴄᴄᴇssꜰᴜʟʏ.</b>")
    else:
        return await message.reply_text(
            "<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ sᴇᴛ ɪᴛ ᴀꜱ ᴀꜱꜱɪꜱᴛᴀɴᴛ'ꜱ ɴᴇᴡ ɴᴀᴍᴇ.</b>"
        )
