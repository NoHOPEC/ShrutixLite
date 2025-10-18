from pyrogram import filters
from pyrogram.types import Message
import os

from ShrutiMusic import app


def check_python_syntax(code: str):
    """Check Python code syntax using compile()"""
    try:
        compile(code, "<string>", "exec")
        return True, None
    except SyntaxError as e:
        # Error msg with line + column + code context
        err_line = e.text.strip() if e.text else ""
        return False, f"<b>{e.msg}</b> at line <b>{e.lineno}</b>, column <b>{e.offset}</b>\n<code>{err_line}</code>"


@app.on_message(filters.command("syntax"))
async def syntax_func(client, message: Message):
    # Get code from reply or command
    if message.reply_to_message:
        if message.reply_to_message.text:
            code_text = message.reply_to_message.text
        elif message.reply_to_message.document:
            doc = message.reply_to_message.document
            if not doc.file_name.endswith((".txt", ".py")):
                return await message.reply("❌ Only Python/text files are supported.")
            file_path = await message.reply_to_message.download()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code_text = f.read()
            except Exception as e:
                return await message.reply(f"❌ Unable to read file:\n<code>{e}</code>")
            os.remove(file_path)
        else:
            return await message.reply("❌ Reply to a Python code or text file.")
    else:
        if len(message.command) < 2:
            return await message.reply("⚡ Reply to a Python code or give code with command:\n<code>/syntax &lt;code&gt;</code>")
        code_text = message.text.split(None, 1)[1]

    # Check Python syntax
    ok, error = check_python_syntax(code_text)

    if ok:
        return await message.reply(
            f"✅ <b>Code syntax looks fine!</b>\n\n<code>{code_text}</code>", quote=True
        )
    else:
        return await message.reply(
            f"❌ <b>Syntax Error:</b>\n{error}", quote=True
        )
