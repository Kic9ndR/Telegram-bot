from aiogram import F, types, Router
from aiogram.filters import Command
from filters.chat_types import ChatFilter


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))


@user_group.message(Command('about'))
async def about_cmd(message: types.Message):
    await message.answer('Я умею и могу...')

