import asyncio
import os
from datetime import datetime
from sre_parse import State
from aiogram import F, Bot, types, Router
from aiogram.filters import Command, StateFilter, or_f
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from database.orm_query import *
from filters.chat_types import ChatFilter
from common.bot_cmds_list import admin
from googlesheets.table import GoogleTable
from kbrd import reply


user_group = Router()
user_group.message.filter(ChatFilter(['group', 'supergroup']))

work_check = os.getenv('WORK_CHECK')
user_chat = os.getenv('USER_CHAT')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')


@user_group.message(Command("add_admin"))
async def add_admins(message: types.Message, bot: Bot, session: AsyncSession) -> None:
    get_admins_list = await orm_get_admins(session)
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
                name = message.from_user.first_name,
                username = message.from_user.username, 
                )
            admins.append(admin_id)


        bot.my_admins_list = admins
        if message.from_user.id in admins:
            print('Добавил админов')
            await bot.delete_message(chat_id=int(admin_chat), message_id=message_id, request_timeout=1)
            await bot.set_my_commands(
                commands=admin, scope=types.BotCommandScopeAllPrivateChats()
        )
    else:
        await message.answer('Ай-ай-ай, Вам сюда нельзя!')


####################################################################################################################
"""
Взаимодействие с отправленными работами ============================================================================
"""
####################################################################################################################
@user_group.callback_query(F.data.startswith('accept_'))
async def send_accepted_work(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    user_id = callback.data.split('_')[-1]
    work_title = callback.data.split('_')[1]
    user_info = await orm_get_one_user(session, user_id)
    work = await orm_get_one_work(session, work_title)
    await callback.answer('Работу принял')
    await callback.message.reply("Отлично, работу принял")

    await bot.send_message(chat_id=user_info.user_id, text=f'Вашу работу {work_title} <b>Приняли</b>!', parse_mode='HTML')

    # Редактирования сообщение в групповом чате
    mes_id = await orm_get_user_id_message(session, work_title, user_id)
    await orm_delete_id_message(session, mes_id.id)                 # Удаление id сообщения для редактирования
    await orm_delete_user_work(session, mes_id.work_id)             # Удаление работы в назначенных работах пользователя

    # Изменения в группе проверки работ
    try:
        await bot.edit_message_caption(
            chat_id=int(work_check), 
            message_id=mes_id.id, 
            caption=f'Работу <i>{mes_id.title}</i> <b>Приняли</b> у @{user_info.username}\n\nСсылка на отправленные файлы: {mes_id.work_link}',
        )
    except:
        await bot.edit_message_text(
            chat_id=int(work_check), 
            message_id=mes_id.id,
            text=f'Работу <i>{mes_id.title}</i> <b>Приняли</b> у @{user_info.username}\n\nСсылка на отправленные файлы: {mes_id.work_link}',
            disable_web_page_preview=True,
        )
    # Изменения в общей группе
    try:
        await bot.edit_message_caption(
            chat_id=int(work_check), 
            message_id=mes_id.mes_id, 
            caption=f'Работу <i>{mes_id.title}</i> <b>Приняли</b> у @{user_info.username}\n\nСсылка на отправленные файлы: {mes_id.work_link}',
        )
    except:
        await bot.edit_message_text(
            chat_id=int(work_check), 
            message_id=mes_id.mes_id, 
            text=f'Работу <i>{mes_id.title}</i> <b>Приняли</b> у @{user_info.username}\n\nСсылка на отправленные файлы: {mes_id.work_link}',
            disable_web_page_preview=True,
        )

    # Отправка нового статуса в GoogleSheet
    title = user_info.name          # Название листа
    google_table = GoogleTable()
    google_table.update_status(title=title, work=work_title, new_status="Выполнено")
    
    if work.complexity is None:
        await orm_delete_work(session, work_title)

####################################################################################################################

class CheckWork(StatesGroup):
    user_name = State()
    doc = State()

    load_file = None
    message_id = None
    work_title = None
    user_id = None

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

@user_group.callback_query(StateFilter(None), F.data.startswith('edits_'))
async def send_edits(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.data.split('_')[-1]
    work_title = callback.data.split('_')[1]

    CheckWork.user_id = user_id
    CheckWork.work_title = work_title
    CheckWork.message_id = callback.message.message_id

    await state.set_state(CheckWork.user_name)
    await state.update_data(user_name=user_id)
    await state.set_state(CheckWork.doc)

    await callback.answer()
    msg = await callback.message.answer(
        'Загрузите файл или напишите комментарий в <u>ответ на это сообщение</u>', 
        reply_to_message_id=CheckWork.message_id, reply_markup=reply.cancel
    )

    await asyncio.sleep(180)
    await bot.delete_message(chat_id=int(work_check), message_id=msg.message_id)
    await state.clear()

#____________________________________________________________________________________________________________________
@user_group.message(CheckWork.doc, or_f(F.document, F.text))
async def add_doc(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    if message.reply_to_message and message.text:
        await state.update_data(doc=message.text)
    elif message.document:
        await state.update_data(doc=message.document)
    else:
        return await state.set_state(CheckWork.doc)
    
    work_title = CheckWork.work_title
    user_info = await orm_get_one_user(session, int(CheckWork.user_id))

    try:
        data = await state.get_data()
        file = data['doc']
        if message.text:
            await bot.send_message(
                chat_id=int(CheckWork.user_id),
                text=f'Вам отправили правки по вашей работе -- {CheckWork.work_title}\n\nКомментарий: {message.text}'
            )
        else:
            await bot.send_document(
                chat_id=int(CheckWork.user_id), document=file.file_id, 
                caption=f'Вам отправили правки по вашей работе -- {CheckWork.work_title}'
            )
            
        await message.answer(text="Отправил правки", reply_to_message_id=CheckWork.message_id, reply_markup=reply.del_kb)
    except Exception as e:
        await message.answer(f"Ошибка при отправке правок сотруднику:\n{e}\nОбратись к @Kic9ndr")

    # Редактирования сообщения в групповом чате
    mes_id = await orm_get_user_id_message(session, work_title, int(CheckWork.user_id))

    if message.text:
        # Изменения в группе проверки работ
        await bot.edit_message_caption(
            chat_id=int(work_check), 
            message_id=CheckWork.message_id,
            caption=f'Отправлены <b>правки</b> по работе <i>{work_title}</i> к @{user_info.username}\n\nКомментарий к правкам: {message.text}',
        )
    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # Изменения в общей группе
        await bot.edit_message_caption(
            chat_id=int(admin_chat),
            message_id=mes_id.mes_id, 
            caption=f'Отправлены <b>правки</b> по работе <i>{work_title}</i> к @{user_info.username}\n\nКомментарий к правкам: {message.text}',
        )
    else:
        # Изменения в группе проверки работ
        await bot.edit_message_media(media=types.InputMediaDocument(media=file.file_id), chat_id=int(work_check), message_id=CheckWork.message_id)
        await bot.edit_message_caption(
            chat_id=int(work_check), 
            message_id=CheckWork.message_id,
            caption=f'Отправлены <b>правки</b> по работе <i>{work_title}</i> к @{user_info.username}\n\nСсылка на отправленные файлы: {mes_id.work_link}',
        )
        #/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # Изменения в общей группе
        await bot.edit_message_media(media=types.InputMediaDocument(media=file.file_id), chat_id=int(admin_chat), message_id=mes_id.mes_id)
        await bot.edit_message_caption(
            chat_id=int(admin_chat),
            message_id=mes_id.mes_id, 
            caption=f'Отправлены <b>правки</b> по работе <i>{work_title}</i> к @{user_info.username}\n\nСсылка на отправленные файлы: {mes_id.work_link}',
        )

    await orm_delete_id_message(session, mes_id.id)
    await orm_update_user_date(session, mes_id.work_id, datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour))
    await state.clear()

    # Отправка нового статуса в GoogleSheet
    title = user_info.name
    google_table = GoogleTable()
    google_table.update_status(title=title, work=work_title, new_status="Правки")
