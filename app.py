import asyncio
from email import message
import os

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from middleware.db import DateBaseSession
from database.engine import create_db, drop_db, session_maker

from handlers.user_private import user_router
from handlers.user_group import user_group
from handlers.admin_private import admin_router

from common.bot_cmds_list import private, admin

# ----------------------------------------------------------------------------------

bot = Bot(token=os.getenv("TOKEN"))
db = Dispatcher()

db.include_router(user_router)
db.include_router(user_group)
db.include_router(admin_router)

"""
Получение ID группы с пользователями
"""
user_chat = os.getenv('USER_CHAT')
user_message_thread = os.getenv('USER_MESSAGE_THREAD')

"""
Получение ID группы с администраторами
"""
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')


# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------

async def on_startup(bot):
    run_param = False
    if run_param:
        await drop_db()
    await bot.send_message(chat_id=int(admin_chat), text=
            f'Бот был перезапущен.\nДля прав администратора нажмите: /add_admin', message_thread_id=int(admin_message_thread))
    await create_db()

async def on_shutdown(bot):
    print("Бот упал :(")


async def main():
    db.startup.register(on_startup)
    db.shutdown.register(on_shutdown)

    db.update.middleware(DateBaseSession(session_pool = session_maker))
    await create_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=private, scope=types.BotCommandScopeAllPrivateChats()
    )

    await db.start_polling(bot, allowed_updates=db.resolve_used_update_types(), polling_timeout=30)



asyncio.run(main())
