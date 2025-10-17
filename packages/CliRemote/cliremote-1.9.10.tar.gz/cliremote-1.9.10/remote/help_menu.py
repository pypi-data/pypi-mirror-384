# antispam_core/help_menu.py
from pyrogram import filters
from . import admin_manager


async def start_handler_cmd(message,text):
    """نمایش منوی راهنما (start command)"""
    await message.reply(text)
