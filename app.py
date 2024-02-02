import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

bot = Bot(token='6110800697:AAHKgy43mk1nk6-DY9kVgb2L2d9QGpkFMIg')
db = Dispatcher()


@db.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Это команда старт')


@db.message()
async def echo(message: types.Message, bot: Bot):
    await bot.send_message(message.from_user.id, 'Ответ')
    await message.answer(message.text)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await db.start_polling(bot)

asyncio.run(main())