import os
from aiogram import F, Bot, types, Router
from aiogram.filters import Command
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_query import orm_add_admin, orm_get_admin_info
from filters.chat_types import ChatFilter
from common.bot_cmds_list import admin


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))
chat_id = os.getenv('CHAT_ID')

@user_group.message(Command("add_admin"))
async def get_admins(message: types.Message, bot: Bot, session: AsyncSession) -> None:
    admins_list = await bot.get_chat_administrators(chat_id)

    get_admins_list = await orm_get_admin_info(session)

    admins_id = [
                member.user_id 
                for member in get_admins_list 
                if member in get_admins_list
                ]
    
    for member in admins_list:
        if (member and not member.user.is_bot) and (member.user.id not in admins_id):
            await orm_add_admin(
                session, 
                user_id = member.user.id,
                first_name = member.user.first_name,
                last_name = member.user.last_name,
                username = member.user.username, 
                )
    
    bot.my_admins_list = admins_id
    if message.from_user.id in admins_id:
        await message.delete()
        await bot.set_my_commands(
            commands=admin, scope=types.BotCommandScopeAllPrivateChats()
    )
        





@user_group.message(F.text)
async def check_work(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await bot.send_message(chat_id=chat_id, text="Принял правки")
    else:
        await bot.send_message(chat_id=chat_id, text="Моя твоя не понимай")


@user_group.message(F.text.startrtswith.lower("прин"))
async def check_work(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await bot.send_message(chat_id=chat_id, text="Отлично, работу принял")

