import os
from sre_parse import State
from turtle import down
from aiogram import F, Bot, types, Router
from aiogram.filters import Command, StateFilter
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile


from database.orm_query import orm_add_admin, orm_get_admin_info, orm_get_user, orm_get_user_info
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
        


class SendWork(StatesGroup):
    doc = State()
    user_name = State()


@user_group.message(StateFilter('*'), Command("отмена"))
@user_group.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены")


@user_group.message(StateFilter(None), F.document)
async def check_work(message: types.Message, bot: Bot, state: FSMContext):
    if message.reply_to_message:
        await state.set_state(SendWork.doc)
        await state.update_data(doc=message.document)
        await state.set_state(SendWork.user_name)
        await bot.send_message(chat_id=chat_id, text="Напишите @username исполнителя")

@user_group.message(SendWork.user_name, F.text.contains('@'))
async def check_work(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
    user_n = message.text.split('@')[-1]
    await state.update_data(user_name=user_n)
    work = await orm_get_user_info(session)
    for i in work:
        if user_n in i.username:
            await bot.send_message(chat_id=chat_id, text="Отправил правки")
            data = await state.get_data()
            print(data['doc'])
            file = data['doc']
            await bot.send_document(chat_id=i.user_id, document=file.file_id, caption=
                                    f'Вам отправили правки по вашей работе - {i.current_work}')
            break
    await state.clear()


@user_group.message(F.text)
async def check_work(message: types.Message, bot: Bot, session: AsyncSession):
    if message.reply_to_message and message.text.lower().startswith('прин'):
        await bot.send_message(chat_id=chat_id, text="Отлично, работу принял")


