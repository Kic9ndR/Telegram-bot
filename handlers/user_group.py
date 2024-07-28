from distutils.command.build_scripts import first_line_re
from aiogram import F, Bot, types, Router
from aiogram.filters import Command
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AdminList
from database.orm_query import orm_add_admin
from filters.chat_types import ChatFilter
from common.bot_cmds_list import admin


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))


@user_group.message(Command("add_admin"))
async def get_admins(message: types.Message, bot: Bot, session: AsyncSession) -> None:
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)

    #просмотреть все данные и свойства полученных объектов
    print(admins_list)
    # Код ниже это генератор списка

    # arr = []  # абстрактный массив с юзер_айди
    # for user_id in arr:
    #     await user_router.send_message(chat_id=user_id)
    #     await asyncio.sleep(1)
    # user_id=message.from_user.id
    # print(user_id)

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
        
    # await orm_add_admin(
    #     session,
    #     id=admins_list.id,
    #     first_name=admins_list.first_name,
    #     last_name=admins_list.last_name,
    # )
    # await session.commit()
    # await message.answer(f"Вы успешно добавили админа в список админов")

