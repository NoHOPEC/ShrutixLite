from ShrutiMusic import app
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter
from html import escape

def full_name(user):
    name = user.first_name or ""
    if getattr(user, "last_name", None):
        name += f" {user.last_name}"
    return name.strip() or "User"

def mention_html(user):
    name = escape(full_name(user))
    return f"<a href='tg://user?id={user.id}'>{name}</a>"

def admin_tag(member):
    status = getattr(member, "status", "")
    if status in ["creator", "owner"]:
        return "<b>Owner</b>"
    if status == "administrator":
        custom = getattr(member, "custom_title", None)
        if getattr(member, "is_anonymous", False):
            return "<b>Admin</b> (Anonymous)"
        if custom:
            return f"<b>Admin</b> (<i>{escape(custom)}</i>)"
        return "<b>Admin</b>"
    return "<b>Admin</b>"

@app.on_message(filters.command(["adminlist", "listadmins", "admin"]) & ~filters.private)
async def admin_list(_, message: Message):
    try:
        admins = []
        async for m in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
            admins.append(m)
    except Exception:
        await message.reply_text(
            "<b>⚠️ Failed to fetch admin list.</b>\n"
            "Ensure I'm in the group and can view members."
        )
        return

    if not admins:
        await message.reply_text("<b>No admins found or access denied.</b>")
        return

    title = escape(message.chat.title or "this chat")
    text = f"<b>Admins of {title}:</b>\n\n"
    for i, mem in enumerate(admins, start=1):
        user = getattr(mem, "user", None)
        if not user:
            continue
        text += f"{i}. {mention_html(user)} — {admin_tag(mem)}\n"

    await message.reply_text(text, disable_web_page_preview=True)

@app.on_message(filters.command(["adminlist", "listadmins", "admin"]) & filters.private)
async def admin_list_private(_, message: Message):
    await message.reply_text(
        "<b>This command only works in groups.</b>\n"
        "Use it inside a group to display its admins."
    )
