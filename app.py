import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from filters.chat_types import ChatFilter, IsAdmin
from handlers.user_private import user_router
from handlers.user_group import user_group
from handlers.admin_private import admin_router
from common.bot_cmds_list import private, admin

ALLOWED_UPDATES = ['message, edited_message']

bot = Bot(token=os.getenv('TOKEN'))
db = Dispatcher()

db.include_router(user_router)
db.include_router(user_group)
db.include_router(admin_router)

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await db.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


asyncio.run(main())