from aiogram import F, Bot, types, Router
from aiogram.filters import Command

from filters.chat_types import ChatFilter
from common.bot_cmds_list import admin


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))


@user_group.message(Command("add_admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)

    #просмотреть все данные и свойства полученных объектов
    #print(admins_list)
    # Код ниже это генератор списка
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()
        await bot.set_my_commands(
            commands=admin, scope=types.BotCommandScopeAllPrivateChats()
    )
    # print(admins_list)
