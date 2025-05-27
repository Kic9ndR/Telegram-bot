import asyncio
import os
from aiogram.client.bot import DefaultBotProperties

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode

from dotenv import load_dotenv, find_dotenv

from middleware.photo import AlbumMiddleware

load_dotenv(find_dotenv())

from middleware.db import DateBaseSession
from database.engine import create_db, drop_db, session_maker

from handlers.user_private import user_router
from handlers.user_group import user_group
from handlers.admin_private import admin_router

from common.bot_cmds_list import private

# ----------------------------------------------------------------------------------

bot = Bot(token=os.getenv("TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
    await create_db()

async def on_shutdown(bot):
    print("Бот упал :(")

async def delete_webhook_with_retry(bot, max_retries=5):
    for attempt in range(max_retries):
        try:
            # Сначала получаем информацию о текущем вебхуке
            webhook_info = await bot.get_webhook_info()
            print(f"Текущий статус вебхука: {webhook_info.url}")
            
            if webhook_info.url:
                # Если вебхук активен, пытаемся его удалить
                await bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(2)  # Ждем 2 секунды
                
                # Проверяем, удалился ли вебхук
                webhook_info = await bot.get_webhook_info()
                if not webhook_info.url:
                    print("Вебхук успешно удален")
                    return True
                else:
                    print(f"Попытка {attempt + 1}: Вебхук все еще активен")
            else:
                print("Вебхук не активен")
                return True
                
        except Exception as e:
            print(f"Попытка {attempt + 1}: Ошибка при удалении вебхука: {e}")
        
        await asyncio.sleep(3)  # Ждем 3 секунды перед следующей попыткой
    
    return False

async def main():
    db.startup.register(on_startup)
    db.shutdown.register(on_shutdown)

    db.update.middleware(DateBaseSession(session_pool = session_maker))
    db.message.middleware(AlbumMiddleware())
    await create_db()
    
    # Принудительное удаление вебхука
    webhook_deleted = await delete_webhook_with_retry(bot)
    if not webhook_deleted:
        print("Не удалось удалить вебхук после всех попыток")
        return
    
    await bot.set_my_commands(
        commands=private, scope=types.BotCommandScopeAllPrivateChats()
    )

    try:
    await db.start_polling(bot, allowed_updates=db.resolve_used_update_types(), polling_timeout=30)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        await asyncio.sleep(5)
        await main()  # Рекурсивный перезапуск

if __name__ == '__main__':
asyncio.run(main())
