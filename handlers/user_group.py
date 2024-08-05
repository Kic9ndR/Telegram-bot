import os
from sre_parse import State
from aiogram import F, Bot, types, Router
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext



from database.orm_query import orm_add_admin, orm_delete_user_work, orm_get_admin_info, orm_get_user_info
from filters.chat_types import ChatFilter
from common.bot_cmds_list import admin


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))
chat_id = -1002165307959
message_thread = 2


@user_group.message(Command("add_admin"))
async def add_admins(message: types.Message, bot: Bot, session: AsyncSession) -> None:
    get_admins_list = await orm_get_admin_info(session)
    admins = []
    for i in get_admins_list:
        admins.append(i.user_id)

    if message.chat.id == chat_id:
        admin_id = message.from_user.id        

        if admin_id not in admins:    
            await orm_add_admin(
                session, 
                user_id = message.from_user.id,
                first_name = message.from_user.first_name,
                username = message.from_user.username, 
                )
            admins.append(admin_id)


        bot.my_admins_list = admins
        if message.from_user.id in admins:
            print('Добавил')
            await bot.set_my_commands(
                commands=admin, scope=types.BotCommandScopeAllPrivateChats()
        )
    else:
        await message.answer('Ай-ай-ай, Вам сюда нельзя!')



####################################################################################################################

class SendWork(StatesGroup):
    doc = State()
    user_name = State()

####################################################################################################################

@user_group.message(StateFilter('*'), Command("отмена"))
@user_group.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены")


####################################################################################################################

@user_group.message(StateFilter(None), F.document)
async def check_work(message: types.Message, bot: Bot, state: FSMContext):
    if message.reply_to_message:
        await state.set_state(SendWork.doc)
        await state.update_data(doc=message.document)
        await state.set_state(SendWork.user_name)
        await bot.send_message(chat_id=chat_id, text="Напишите @username исполнителя", message_thread_id=message_thread)


####################################################################################################################

@user_group.message(SendWork.user_name, F.text.contains('@'))
async def check_work(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
    if message.reply_to_message:
        user_n = message.text.split('@')[-1]
        await state.update_data(user_name=user_n)
        work = await orm_get_user_info(session)
        for i in work:
            if user_n in i.username:
                await bot.send_message(chat_id=chat_id, text="Отправил правки", message_thread_id=message_thread)
                data = await state.get_data()
                file = data['doc']
                await bot.send_document(chat_id=i.user_id, document=file.file_id, caption=
                                            f'Вам отправили правки по вашей работе - {i.current_work}')
                break
        await state.clear()


####################################################################################################################

class AcceptWork(StatesGroup):
    username = State()

@user_group.message(StateFilter(None), F.text)
async def user_name(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
    if message.reply_to_message and message.text.lower().startswith('прин'):
        await bot.send_message(chat_id=chat_id, text=
                               'Введите @username в ответ на сообщение', message_thread_id=message_thread)
        await state.set_state(AcceptWork.username)
    if message.reply_to_message:
        await bot.send_message(chat_id=chat_id, text=
                "Для отправки правок ответьте на данное сообщение приложенным файлом\n\nЕсли хотите принять работу, то ответьте на сообщение 'Принял'", message_thread_id='2'
                )

@user_group.message(AcceptWork.username, F.text.contains('@'))
async def send_accepted_work(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
    if message.reply_to_message:
        user_n = message.text.split('@')[-1]
        await state.update_data(username=user_n)
        work = await orm_get_user_info(session)
        for i in work:
            if user_n in i.username:
                await bot.send_message(chat_id=chat_id, text="Отлично, работу принял", message_thread_id=message_thread)
                await bot.send_message(chat_id=i.user_id, text=f'Вашу работу:\n{i.current_work}\nПриняли!')
                await orm_delete_user_work(session, i.current_work)
        await state.clear()


