import os
from sre_parse import State
from aiogram import F, Bot, types, Router
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from database.orm_query import *
from filters.chat_types import ChatFilter
from common.bot_cmds_list import admin


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))

user_chat = os.getenv('USER_CHAT')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')
# chat_id = -1002165307959
# message_thread = 2


@user_group.message(Command("add_admin"))
async def add_admins(message: types.Message, bot: Bot, session: AsyncSession) -> None:
    get_admins_list = await orm_get_admin_info(session)
    admins = []
    for i in get_admins_list:
        admins.append(i.user_id)

    message_id = message.message_id

    if message.chat.id == int(admin_chat):
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
            await bot.delete_message(chat_id=int(admin_chat), message_id=message_id, request_timeout=1)
            await bot.set_my_commands(
                commands=admin, scope=types.BotCommandScopeAllPrivateChats()
        )
    else:
        await message.answer('Ай-ай-ай, Вам сюда нельзя!')


####################################################################################################################

@user_group.callback_query(F.data.startswith('accept_'))
async def send_accepted_work(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    user_id = callback.data.split('_')[-1]
    user_info = await orm_get_user(session, user_id)
    await callback.answer('Работу принял')
    await bot.send_message(chat_id=int(admin_chat), text=
                    "Отлично, работу принял", message_thread_id=int(admin_message_thread)
                )
    await bot.send_message(chat_id=user_info.user_id, text=f'Вашу работу:\n{user_info.current_work}\nПриняли!')
    await orm_delete_user_work(session, user_info.current_work)


####################################################################################################################

class SendWork(StatesGroup):
    user_name = State()
    doc = State()


@user_group.message(StateFilter('*'), Command("отмена"))
@user_group.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены")


@user_group.callback_query(StateFilter(None), F.data.startswith('edits_'))
async def send_edits(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split('_')[-1]

    await state.set_state(SendWork.user_name)
    await state.update_data(user_name=user_id)
    await state.set_state(SendWork.doc)

    await callback.answer()
    await callback.message.answer('Загрузите файл')


@user_group.message(SendWork.doc, F.document)
async def add_doc(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
    await state.update_data(doc=message.document)

    data = await state.get_data()
    file = data['doc']
    user = data['user_name']
    work = await orm_get_user(session, user)
    await bot.send_message(chat_id=int(admin_chat), text="Отправил правки", message_thread_id=int(admin_message_thread))
    await bot.send_document(chat_id=user, document=file.file_id, caption=
                        f'Вам отправили правки по вашей работе - {work.current_work}')

    await state.clear()

@user_group.message(SendWork.doc)
async def add_doc2(message: types.Message):
    await message.answer("Неправильно.\nЗагрузите, пожалуйста, файл 🙏")