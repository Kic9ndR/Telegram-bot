import asyncio
import os
import random
from aiogram import F, Bot, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession


from common.work_output import send_booklet_output, work_output, work_output2
from database.orm_query import *
from filters.chat_types import ChatFilter, IsAdmin
from googlesheets.table import GoogleTable
from kbrd import reply
from kbrd.inline import *
from kbrd.reply import admin_kb


#----------------------------------------------------------------------------------
admin_router = Router()
admin_router.message.filter(ChatFilter(["private"]), IsAdmin())

user_chat = os.getenv('USER_CHAT')
work_check = os.getenv('WORK_CHECK')
user_message_thread = os.getenv('USER_MESSAGE_THREAD')
thread_work = os.getenv('THREAD_WORK')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')
message_thread_archive = os.getenv('MESSAGE_THREAD_ARCHIVE')


class SendUsers(StatesGroup):
    confirm = State()
    sending = State()

    message = ''
    doc = None

#_________________________________________________________________________________________________
# Рассылка пользователям информации
@admin_router.message(StateFilter(None), Command("send_users"))
async def send_to_users(message: types.Message, state: FSMContext):
    await message.answer('Напишите сообщение для <b>Всех</b> пользователей или вставьте файл', reply_markup=reply.admin_nav)
    await state.set_state(SendUsers.confirm)

#_________________________________________________________________________________________________
@admin_router.message(SendUsers.confirm)
async def send_to_users(message: types.Message, state: FSMContext):
    if message.text:
        SendUsers.message = message.text
        await message.answer(f'Отправить сообщение:\n{SendUsers.message}', reply_markup=await get_callback_btns(
            btns={
                'Да': f'YES',
                'Нет': f'NO',
                }
            )
        )
    else:
        SendUsers.doc = message.document.file_id
        await message.answer_document(caption=f'Отправить этот файл?', document=SendUsers.doc, reply_markup=await get_callback_btns(
            btns={
                'Да': f'YES',
                'Нет': f'NO',
                }
            )
        )
    await state.set_state(SendUsers.sending)

#_________________________________________________________________________________________________
@admin_router.callback_query(SendUsers.sending, F.data)
async def send_to_users(callback: types.CallbackQuery, session: AsyncSession, bot: Bot, state: FSMContext):
    await callback.message.delete()
    if callback.data == 'YES':
        await state.clear()
        for user in await orm_get_users(session):
            try:
                if SendUsers.message != '':
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=SendUsers.message
                    )
                elif SendUsers.doc != None:
                    await bot.send_document(
                        chat_id=user.user_id,
                        document=SendUsers.doc,
                        reply_markup=await get_callback_btns(
                            btns={
                                'Принять пользовательское соглашение': 'file_accept',
                            }, sizes=(1,1)
                        )
                    )
            except Exception as e:
                await callback.message.answer(f'Ошибка: {e}\nОбратись к @Kic9ndr')
        await callback.answer('Отправил сообщение пользователям')
        await callback.message.answer('Отправил сообщение пользователям')

    elif callback.data == 'NO':
        await callback.message.answer('Хорошо, вернул в начало\nНапишите сообщение для <b>Всех</b> пользователей или вставьте файл', reply_markup=reply.del_kb)
        await state.set_state(SendUsers.confirm)


###################################################################################################
class CreateTask(StatesGroup):
    title = State()
    work_comment = State()
    deadline = State()
    complexity = State()
    file_name = State()
    file = State()
    image = State()
    worker_name = State()
    format_work = State()

    title_for_change = ''
    quick_work = False
    change_work = False
    confirm = False

    texts = {
        'CreateTask:title': 'Введите работы повторно: ',
        'CreateTask:work_comment': 'Введите комментарий повторно: ',
        'CreateTask:deadline': 'Введите срок выполнения повторно: ',
        'CreateTask:complexity': 'Введите сложность работы повторно: ',
        'CreateTask:file_name': 'Введите названия файла повторно: ',
        'CreateTask:file': 'Отправьте ссылку повторно: ', 
        'CreateTask:image': 'Загрузите фото повторно: ',
    }

#_________________________________________________________________________________________________
@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=admin_kb)

#_________________________________________________________________________________________________
@admin_router.message(Command("admin"))
async def admin(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Что хотите сделать?", reply_markup=admin_kb)


#_________________________________________________________________________________________________
"""
Кнопки для списка сотрудников =====================================================================
"""
@admin_router.message(F.text == "Списки сотрудников 📋")
async def project_klnd(message: types.Message):
    await message.answer('Какой список тебе нужен?', reply_markup=await get_callback_btns(btns={
                'На правках': f"busy_",
                'Свободные': f'available_',
                'Все сотрудники': f'all_',
                }
            )
        )
    
#__________________________________________________________________________________________________
@admin_router.callback_query(F.data == "back_list")
async def project_klnd(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer('Какой список тебе нужен?', reply_markup=await get_callback_btns(btns={
                'На правках': f"busy_",
                'Свободные': f'available_',
                'Все сотрудники': f'all_',
                }
            )
        )

#_________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('busy_'))        # На правках дольше 24 ч
async def all_worker(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.delete()
    await callback.answer()
    await callback.message.answer('Сотрудники на правках дольше 24 часов', reply_markup=await choice_busy_worker_btns(session))


#_________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('available_'))       # Свободные сотрудники
async def all_worker(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    user_list = []

    works = await orm_get_users_works(session)          # Получаю всех юзеров с параметром работ
    for user in works:                                  # Цикл по строкам в бд. Получаю строку каждого юзера
        if user.work == []:
            user_list.append(f'{user.name} @{user.username}')

    if user_list != []:
        await callback.message.answer('Список свободных сотрудников', reply_markup=admin_kb)
        await callback.message.answer('\n'.join(user_list))
    else:
        await callback.message.answer('Все сотрудники заняты')


#_________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('all_'))              # Все сотрудники сотрудники
async def all_worker(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.delete()
    await callback.answer()
    await callback.message.answer('Список всех сотрудников', reply_markup=await choice_worker_btns(session))

#_________________________________________________________________________________________________
"""
Получение таблицу сотрудников с google sheets =====================================================
"""
@admin_router.message(F.text == "Таблицы 𝄜")
async def task_distrib(message: types.Message):
    await message.answer('Список всех таблиц:', reply_markup=await get_url_btns(
        btns={
                'Таблица сотрудников': 'https://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g',
                'График работы': 'https://docs.google.com/spreadsheets/d/1VTlLg0JOvnw-owN4xpzwl7Vl_5vtooEukcCH3phl6Nw',
                'График проектов': 'https://docs.google.com/spreadsheets/d/10HbRZe4bOX7UcIdb6kA5vpu-rqETZb8bGHuaU_tqhGA',
            }, sizes={1, 1, 1}
        )
    )

#__________________________________________________________________________________________________
"""
Кнопки для выбора работы ==========================================================================
"""
@admin_router.message(F.text == "Список работ 📜")
async def project_list(message: types.Message, bot: Bot):
    await bot.send_chat_action(chat_id=message.from_user.id, action='typing')
    await message.answer(
        '<b>Выберите список:</b>\n\n<b>Опубликованный список</b> -- отправлены в группу\n<b>В процессе создания</b> -- не отправлены в рабочую группу', 
        reply_markup=await get_callback_btns(btns=
            {
                'Опубликованный список': f'realized',
                'В процессе создания': f'process',
                'Архив работ': f'archive',
            }, sizes={1, 1, 1}
        ), parse_mode='HTML'
    )

#_________________________________________________________________________________________________
# Опубликованный список работ
@admin_router.callback_query(F.data == ('realized'))
async def realized_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.delete()
    await callback.answer()
    await callback.message.answer('Вот список опубликованных работ:', 
                                reply_markup=await choice_works_btns(
                                session=session, category='realized'
                            )
                    )

#_________________________________________________________________________________________________
# Список в процессе создания работы
@admin_router.callback_query(F.data == ('process'))
async def process_of_creation(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    await callback.message.delete()
    await callback.answer()
    await callback.message.answer('Работы в процессе создания:', 
                                reply_markup=await choice_works_btns(
                                session=session,
                                category='process'
                            )
                    )

#_________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('work_'))
async def get_work(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    await bot.send_chat_action(chat_id=callback.from_user.id, action='typing')
    work = callback.data.split('_')[-1]
    await callback.answer(f'Работа {work}')
    await callback.message.delete()

    await work_output(callback, session, work)                  # Вывод работы

#_________________________________________________________________________________________________
@admin_router.callback_query(F.data == 'comeback')
async def comeback_work(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        '<b>Выберите список:</b>\n\n<b>Опубликованный список</b> -- отправлены в группу\n<b>В процессе создания</b> -- не отправлены в рабочую группу', 
        reply_markup=await get_callback_btns(btns=
            {
                'Опубликованный список': f'realized',
                'В процессе создания': f'process',
                'Архив работ': f'archive',
            }, sizes={1, 1, 1}
        ), parse_mode='HTML'
    )

#_____________________________________________________________________________________________________________
@admin_router.callback_query(ChoiceWork.filter())
async def work_pagination_handler(call: types.CallbackQuery, callback_data: ChoiceWork, session: AsyncSession):
    """ Навигация по списку работ """
    page = callback_data.page
    category = callback_data.category
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=await choice_works_btns(session, page=page, category=category))  # Обновление клавиатуры при нажатии кнопок навигации

#_____________________________________________________________________________________________________________
@admin_router.callback_query(AllWorkers.filter())
async def worker_pagination_handler(call: types.CallbackQuery, callback_data: AllWorkers, session: AsyncSession):
    """ Навигация для списка сотрудников """
    page = callback_data.page
    category = callback_data.category

    await call.answer()
    if category == "worker_skills":
        await call.message.edit_reply_markup(reply_markup=await choice_worker_btns(session, page=page))  # Обновление клавиатуры при нажатии кнопок навигации
    elif category == 'choice_worker':
        await call.message.edit_reply_markup(reply_markup=await choice_worker_btns2(session, page=page))  # Обновление клавиатуры при нажатии кнопок навигации
    elif category == 'several_emp':
        await call.message.edit_reply_markup(reply_markup=await choice_workers_btns(session, page=page))  # Обновление клавиатуры при нажатии кнопок навигации        

#_________________________________________________________________________________________________
"""
Отправка работы в архив ===========================================================================
"""
@admin_router.callback_query(F.data.startswith('sendarchive_'))
async def send_work_archive(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    title_id = callback.data.split('_')[-1]
    await callback.answer()
    work = await orm_get_one_work(session, title_id)
    if work.ready_status == True:
        await orm_add_archive_work(
            session, 
            work.title,
            work.work_comment,
            work.deadline,
            work.file_name,
            work.file,
            work.worker_name,
            work.image
        )
        await callback.message.answer('Работа отправлена в архив')
        await orm_delete_work(session, title_id)

    if work.image is None:
        await bot.send_message(chat_id=int(user_chat), text=
            f"💰 - <b>{work.title}</b>\n💬 - {work.work_comment}\n🗓 - {work.deadline}\n{work.worker_name}", 
            message_thread_id=int(message_thread_archive), parse_mode='HTML',
        )
    else:
        await bot.send_photo(chat_id=int(user_chat), photo=work.image, caption=
            f"💰 - <b>{work.title}</b>\n💬 - {work.work_comment}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 <a href='{work.file}'> Work Files </a>\n{work.worker_name}", 
            message_thread_id=int(message_thread_archive), parse_mode='HTML',
        )
    for user_work in await orm_get_one_user_works2(session, work.title):
        await orm_delete_user_work(session, user_work.work_id)           # Удаление работы в назначенных работах пользователя
        
    for mess_id in await orm_get_id_message(session, work.title):
        await orm_delete_id_message(session, mess_id.id)                 # Удаление id сообщения для редактирования

    # Редактирование работы в группе
    for i in await orm_get_all_id_send_work(session):
        if str(work.title) in str(i.title):
            await bot.delete_message(chat_id=int(user_chat), message_id=i.id)
            await orm_delete_id_send_work(session, i.id)

#_________________________________________________________________________________________________
"""
Получение работ из архива =======================================================================================================================================
"""
@admin_router.callback_query(F.data == 'archive')
async def archive_cmd(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.delete()
    await callback.answer()
    await callback.message.answer('Вот список архивных работ:', 
                                reply_markup=await choice_works_btns(
                                session=session, category='archive'
                            )
                    )
#_________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('archive_'))
async def archive_work(callback: types.CallbackQuery, session: AsyncSession):
    work = callback.data.split('_')[-1]
    await callback.message.delete()
    title = await orm_get_one_archive_work(session, work)
    await callback.message.answer_photo(
            title.image,
            caption=f'{title.title}\n<b>Комментарий</b>: {title.work_comment}\n<b>Срок выполнения:</b> {title.deadline}\n<b>Ссылка на файл:</b> <a href="{title.file}"> Work Files </a>\n<b>Назначены:</b>\n{title.worker_name}',
    )
    
###################################################################################################
"""
Удаление работы ===================================================================================================================================================
"""
class DeleteWork(StatesGroup):
    title_id = State()
    approve = State()

#_________________________________________________________________________________________________
@admin_router.callback_query(StateFilter(None), F.data.startswith('delete_work_'))
async def change_work(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    title_id = callback.data.split('_')[-1]
    await state.set_state(DeleteWork.title_id)
    await state.update_data(title_id=title_id)
    await callback.message.answer('Вы уверены что хотите удалить работу?\n(Да или Нет)')
    await state.set_state(DeleteWork.approve)

#_________________________________________________________________________________________________
@admin_router.message(DeleteWork.approve, F.text)
async def change_work(message: types.Message, session: AsyncSession, state: FSMContext, bot: Bot):
    await state.update_data(approve=message.text)
    data = await state.get_data()
    title = data['title_id']
    if data['approve'] == 'Да':
        for i in await orm_get_user_works(session):     
            if i.current_work == title:
                await orm_delete_user_work(session, i.work_id)
        await orm_delete_work(session, title)

        id_send_work = await orm_get_id_send_work(session, title)
        if id_send_work is not None:
            await bot.delete_message(chat_id=user_chat, message_id=id_send_work)
            await orm_delete_id_send_work(session, id_send_work.id)
        await message.answer('Работа удалена')
    else:
        await message.answer('Хух, ну и хорошо\n')
        await asyncio.sleep(2)
        await message.answer('Ой. Дай пару секунд, а то я перепугался уже 😰')
        await asyncio.sleep(4)
        await message.answer('Ладно, выбери какой список тебе нужен')
        await asyncio.sleep(1)
        await project_list(message, bot)

    await state.clear()

#_________________________________________________________________________________________________
"""
Отправка работы в группу и назначенным сотрудникам ================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('send_'))
async def send_work(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    title_id = callback.data.split('_')[-1]
    work = await orm_get_one_work(session, title_id)
    await orm_update_work_status(session, title_id, True)

    # Отправка работы в группу
    work_id = await bot.send_photo(chat_id=int(admin_chat), photo=work.image, caption=
            f"💰 - {work.title}\n💬 - {work.work_comment}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 <a href='{work.file}'> Work Files </a>\n{work.worker_name}",
            message_thread_id=int(thread_work), parse_mode='HTML'
        )
    
    await orm_add_id_send_work(
            session,
            id=work_id.message_id,
            title=work.title,
        )

    await callback.answer()
    await callback.message.answer('Работа отправлена!')

#_________________________________________________________________________________________________
"""
Вход в состояние изменения работы =================================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('select_'))
async def select_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    title_id = callback.data.split('_')[-1]
    title_for_change = await orm_get_one_work(session, title_id)
    CreateTask.title_for_change = title_for_change
    await callback.message.answer('Хотите изменить работу или исполнителей?', reply_markup=await get_callback_btns(
            btns={
                f'Изменить работу': f'change_work',
                f'Сменить исполнителей': f'change_worker',
            }, sizes=(1,1)
        )
    )
#__________________________________________________________________________________________________
@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    title = callback.data.split('_')[-1]
    await callback.answer()
    if title == "work":
        CreateTask.change_work = True
        await callback.answer('Изменение работы')
        await callback.message.answer(
            'Введите название работы\nОтправьте "." если не хотите вносить изменения', reply_markup=reply.admin_nav
        )
        await state.set_state(CreateTask.title)
    else:
        await callback.answer('Вы уверены?')
        await callback.message.answer('При изменении список удаляется и необходимо назначить <b>Всех</b> повторно\n<b>Вы уверены?</b>',
                                      reply_markup=await get_callback_btns(
                                          btns={
                                              'ДА!': f'yes',
                                              'НЕТ!': f'no',
                                          }
                                      )
                                  )
        await state.set_state(CreateTask.worker_name)

#__________________________________________________________________________________________________
@admin_router.callback_query(CreateTask.worker_name, F.data)
async def change_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    answer = callback.data
    await callback.answer()
    title = CreateTask.title_for_change
    if answer == 'yes':
        for i in await orm_get_user_works(session):                 # Удаление работ сотрудников
            if i.current_work == title.title:
                await orm_delete_user_work(session, i.work_id)
        
        await callback.message.answer("Удалил исполнителей. Можете назначить их повторно")
        await asyncio.sleep(2)
        await bot.send_chat_action(chat_id=callback.message.from_user.id, action='typing')

        work_id = await orm_get_id_send_work(session, title.title)
        await orm_delete_worker_name(session, title=title.title)          # Удаление сотрудников в Work.worker_name
        if work_id is not None:
            await bot.edit_message_caption(chat_id=int(user_chat), message_id=work_id.id,
                    caption=f"💰 - {title.title}\n💬 - {title.work_comment}\n🗓 - {title.deadline}\n📂 - {title.file_name}\n👉 <a href='{title.file}'> Work Files </a>\n",
            )
    else:
        await callback.message.answer("Возвращаю к работе")
        await asyncio.sleep(1)
        await bot.send_chat_action(chat_id=callback.message.from_user.id, action='typing')
    
    work = orm_get_one_work(session, title)

    await work_output(callback, session, work)      # Вывод работы
    await state.clear()

################################################################################################################
################################# Код ниже для машины состояний (FSM) ##########################################
################################################################################################################

@admin_router.message(StateFilter(None), F.text == "Создание задачи ✍🏼")
async def create_task(message: types.Message, state: FSMContext):
    await message.answer('Какую задачу хотите создать?', reply_markup=await get_callback_btns(
        btns={
            "Создание проекта ✍🏼": "standard",
            "Быстрая задача 🚀": "quick",
            "Задача для проверки 🤔": "CheckingProj",
            }
        )
    )
    await state.set_state(CreateTask.format_work)

#______________________________________________________________________________________________________________________
@admin_router.callback_query(CreateTask.format_work, F.data)
async def format_work(callback: types.CallbackQuery, state: FSMContext):
    form = callback.data
    await callback.message.delete()
    CreateTask.change_work = False

    if form == "quick":
        CreateTask.quick_work = True
    elif form == "CheckingProj":
        await callback.message.answer('Введи название работы', reply_markup=reply.admin_nav)
        return await state.set_state(CheckingProj.title)

    await callback.message.answer('Введите название работы', reply_markup=reply.admin_nav)
    return await state.set_state(CreateTask.title)

################################################ Команда назад ################################################
@admin_router.message(StateFilter(CreateTask), Command("назад"))
@admin_router.message(StateFilter(CreateTask), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == CreateTask.title:
        await message.answer('Предыдущего шага нет, напишите "отмена"')
        return

    previous = None
    for step in CreateTask.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу\n{CreateTask.texts[previous.state]}")
            return
        previous = step

################################################ Ввод улицы ################################################
@admin_router.message(CreateTask.title, or_f(F.text, F.text == '.'))
async def set_title(message: types.Message, state: FSMContext):
    if len(message.text) > 26: 
        await message.answer('<b>Передумай</b>. <u>Название не должно превышать 26-ти символов</u>')
        await asyncio.sleep(1)
        await message.answer('Введите название работы повторно', reply_markup=reply.admin_nav)
        return await state.set_state(CreateTask.title)
    
    if "_" in str(message.text):
        await message.answer('<b>Передумай</b>. <u>В название не должно быть</u> "_" <u>символа</u>')
        await asyncio.sleep(1)
        await message.answer('Введите название работы повторно', reply_markup=reply.admin_nav)
        return await state.set_state(CreateTask.title)
    
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(title=CreateTask.title_for_change.title)
    else:
        await state.update_data(title=message.text)

    await message.answer('Введите комментарий или - ')
    await state.set_state(CreateTask.work_comment)

@admin_router.message(CreateTask.title)
async def set_title2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать текст ")

################################################ Комментарий к работе ################################################
@admin_router.message(CreateTask.work_comment, or_f(F.text, F.text == '.'))
async def set_work_comment(message: types.Message, state: FSMContext):
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(work_comment=CreateTask.title_for_change.work_comment)
    else:
        await state.update_data(work_comment = message.text)
    await message.answer("Введите срок выполнения: ")
    await state.set_state(CreateTask.deadline)

@admin_router.message(CreateTask.work_comment)
async def set_work_comment2(message: types.Message):
    await message.answer("Ввели данные неверно. Необходимо написать комментарий или -")

################################################ Ввод срока выполнения ################################################
@admin_router.message(CreateTask.deadline, or_f(F.text, F.text == '.'))
async def set_deadline(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(deadline = CreateTask.title_for_change.deadline)
    elif CreateTask.quick_work == True:
        await state.update_data(deadline = message.text)
        data = await state.get_data()
        title = data['title']
        CreateTask.quick_work = False
        await state.clear()

        await orm_add_work(
            session, 
            title=title,
            work_comment=data['work_comment'],
            deadline=data['deadline'],
            complexity='⭐',
            file_name=None,
            file=None,
            worker_name=None,
            image=None,
            ready_status=True,
        )
        await message.answer(
            "Задача создана, осталось назначить исполнителей", reply_markup=await get_callback_btns(
                btns={
                    'Добавить сотрудника': f'appoint_{title}',
                    'Потом добавлю': f'comeback',
                }, sizes=(1,1)
            )
        )
        return
    else:
        await state.update_data(deadline=message.text)
    await message.answer("Введите сложность работы от 1 до 6")
    await state.set_state(CreateTask.complexity)

#______________________________________________________________________________________________________________________
@admin_router.message(CreateTask.deadline)
async def set_deadline2(message: types.Message):
    await message.answer("Ввели данные неверно. Необходимо написать число ")


################################################ Ввод сложности работы ################################################
@admin_router.message(CreateTask.complexity, or_f(F.text, F.text == '.'))
async def set_complexity(message: types.Message, state: FSMContext):
    complexity = message.text
    if int(complexity) > 6 or int(complexity) < 1:
        await message.answer('Уровень сложность выставляется от 1 до 6\nНапиши сложность повторно ⬇️⬇️⬇️')
        return await state.set_state(CreateTask.complexity)

    if int(complexity) == 6:
        difficulty_lvl = '🆘🆘🆘🆘🆘🆘'
    else:
        difficulty_lvl = '⭐️' * int(complexity)

    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(complexity=CreateTask.title_for_change.complexity)
    else:
        await state.update_data(complexity=difficulty_lvl)
    await message.answer("Введите название файла: ")
    await state.set_state(CreateTask.file_name)

#______________________________________________________________________________________________________________________
@admin_router.message(CreateTask.complexity)
async def set_complexity(message: types.Message):
    await message.answer("Ввели данные неверно.\nНеобходимо выбрать уровень сложности")

################################################ Ввод названия файла ################################################
@admin_router.message(CreateTask.file_name, or_f(F.text, F.text == '.'))
async def set_file_name(message: types.Message, state: FSMContext):
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(file_name = CreateTask.title_for_change.file_name)
    else:
        await state.update_data(file_name=message.text)
    await message.answer("Добавьте ссылку на рабочие файлы ")
    await state.set_state(CreateTask.file)

#______________________________________________________________________________________________________________________
@admin_router.message(CreateTask.file_name)
async def set_file_name2(message: types.Message):
    await message.answer("Ввели данные неверно.\nНеобходимо добавить ссылку на рабочие файлы")

################################################ Ввод файла ################################################
@admin_router.message(CreateTask.file, or_f(F.text, F.text == '.'))
async def set_file(message: types.Message, state: FSMContext):
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(file=CreateTask.title_for_change.file)
    else:
        await state.update_data(file=message.text)
    await message.answer("Загрузите фото обложки задачи")
    await state.set_state(CreateTask.image)

#______________________________________________________________________________________________________________________
@admin_router.message(CreateTask.file)
async def set_file2(message: types.Message):
    await message.answer("Ввели данные неверно.\nНеобходимо загрузить фото обложки задачи ")

################################################ Загрузка фото ################################################
@admin_router.message(CreateTask.image, or_f(F.photo, F.text == '.'))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(image=CreateTask.title_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    title_id = data['title']

    try:
        if CreateTask.change_work == True:          # Если работа была обновлена, то:
            await orm_update_work(session, CreateTask.title_for_change.title, data)
            await orm_update_user_work(session, CreateTask.title_for_change.title, data['title'])
            await message.answer("Задача обновлена!", reply_markup=admin_kb)
        else:
            await orm_add_work(
                session,
                title=data['title'],
                work_comment=data['work_comment'],
                deadline=data['deadline'],
                complexity=data['complexity'],
                file_name=data['file_name'],
                file=data['file'],
                worker_name=None,
                image=data['image'],
                ready_status=False,
            )
            await message.answer("Задача добавлена!", reply_markup=admin_kb)
    except Exception as e:
        session.rollback()
        await message.answer(
                f"Ошибка: \n{str(e)}\nОбратись к программеру",
                reply_markup=admin_kb,
            )

    await state.clear()

    i = await orm_get_one_work(session, title_id)
    if i.worker_name is None:
        worker_name = 'Исполнители еще не назначены'
    else:
        worker_name = i.worker_name

    # Редактирование работы в группе
    work_id = await orm_get_id_send_work(session, i.title)
    if work_id is not None:
        await bot.edit_message_caption(
            chat_id=int(admin_chat), message_id=work_id.id,
            caption=f"💰 - {i.title}\n💬 - {i.work_comment}\n🗓 - {i.deadline}\n📂 - {i.file_name}\n👉 <a href='{i.file}'> Work Files </a>\n{worker_name}",
        )
    
    await work_output2(message, session, title_id)      # Вывод работы
  
    CreateTask.title_for_change = ''

#______________________________________________________________________________________________________________________
@admin_router.message(CreateTask.image)
async def add_image2(message: types.Message):
    await message.answer("Ввели данные неверно. Необходимо загрузить фото")

#################################################################################################################
"""
Назначение сотрудника============================================================================================
"""
#################################################################################################################

class ChoiceWorker(StatesGroup):
    work_id = State()
    task = State()
    salary = State()
    name = State()


    texts = {
    "ChoiceWorker:task": 'Введите задачу',
    "ChoiceWorker:salary": 'Введите оклад',
    "ChoiceWorker:name": 'Выберите имя',
    }

################################################ Команда назад ################################################
@admin_router.message(StateFilter(ChoiceWorker), Command("назад"))
@admin_router.message(StateFilter(ChoiceWorker), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == ChoiceWorker.task:
        await message.answer('Предыдущего шага нет, напишите "отмена"')
        return

    previous = None
    for step in ChoiceWorker.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Вернул к прошлому шагу\n{ChoiceWorker.texts[previous.state]}")
            return
        previous = step

################################################ Получение id работы ################################################

@admin_router.callback_query(StateFilter(None), F.data.startswith('appoint_'))
@admin_router.callback_query(ChoiceWorker.work_id, F.data)
async def add_work_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    title_id = callback.data.split('_')[-1]
    await state.set_state(ChoiceWorker.work_id)
    await state.update_data(work_id=title_id)
    await state.set_state(ChoiceWorker.task)
    await callback.answer('Обозначь задачу:')
    await callback.message.answer('Обозначь задачу:', reply_markup=reply.admin_nav)


################################################ Выбор задачи ################################################

@admin_router.message(ChoiceWorker.task, F.text)
async def add_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await state.set_state(ChoiceWorker.salary)
    await message.answer('Введите оклад\nЕсли работает за Спасибо, то напишите: "-"')

################################################ Ввод оклада ################################################

@admin_router.message(ChoiceWorker.salary, F.text)
async def add_salary(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(salary=message.text)
    await state.set_state(ChoiceWorker.name)
    await message.answer('Выберите команду', reply_markup = await choice_team(session))

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(F.data == 'switch_kbrd')
async def choice_epm(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.edit_reply_markup(reply_markup=await choice_worker_btns2(session))

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(F.data == 'add_emp')
async def write_emp(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer('Напиши <i>имя сотрудника</i>')
    await state.set_state(ChoiceWorker.name)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(F.data == 'back_to_teams')
async def back_to_team(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.edit_reply_markup(reply_markup=await choice_team(session))


################################################ Распределение работы ################################################
@admin_router.callback_query(ChoiceWorker.name, F.data)
async def add_name(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    await callback.message.delete()
    await state.update_data(name=callback.data)
    data = await state.get_data()
    await state.clear()

    title_id = data['work_id']
    name = data['name'].split(' @')[0]
    salary = data['salary']
    task = data['task']
    cap = await orm_get_team_captain(session, name)
    
    task_and_name = str(f"🫡 {data['task']} - {data['name']}")

    before_added = await orm_get_one_work(session, title_id)
    for users in await orm_get_users(session):
        if users.name in name:
            user = users.user_id
            user_name = users.name
            user_info = users
            
    if cap is not None:
        await bot.send_message(chat_id=cap.id, text='Вашей команде назначена новая работа\nДля распределения задач напишите /my_team')
        await orm_add_user_work(
            session,
            user_id=cap.id,
            current_work=title_id,
            task=task,
            salary='-',
            check_work=False
        )
    else:
        user_info = await orm_get_user_name(session, name)
        await bot.send_message(chat_id=user_info.user_id, text='Вам назначена новая работа\nДля просмотра напишите /current_work')
        await orm_add_user_work(
            session,
            user_id=user_info.user_id,
            current_work=title_id,
            task=task,
            salary=salary,
            check_work=False
        )

    if before_added.worker_name == None:
        await orm_add_work_worker_name(session, title_id, task_and_name)
    else:
        await orm_update_work_worker_name(session, title_id, task_and_name)
    await callback.answer('Выполнено')
    await callback.message.answer('Работа назначена', reply_markup=reply.admin_kb)

    i = await orm_get_one_work(session, title_id)
    await work_output(callback, session, title_id)      # Вывод работы

    # Изменение исполнителей в группе с работами
    work_id = await orm_get_id_send_work(session, i.title)
    if work_id is not None:
        await bot.edit_message_caption(chat_id=int(admin_chat), message_id=work_id.id,
                caption=f"💰 - {i.title}\n💬 - {i.work_comment}\n🗓 - {i.deadline}\n‼️ - {i.complexity}\n📂 - {i.file_name}\n👉 <a href='{i.file}'> Work Files </a>\n{i.worker_name}",)
    
    # Отправка информации пользователю
    if i.image is None:
            await bot.send_message(chat_id=user, text=f'💰 - {i.title}\n💬 - {i.work_comment}\n🗓 - {i.deadline}\n‼️ - {i.complexity}\n\n<b>Твоя задача</b>: {task}',
            parse_mode='HTML')
    else:
        try:
            await bot.send_photo(chat_id=cap.id, photo=i.image, caption=
                    f'💰 - {i.title}\n💬 - {i.work_comment}\n🗓 - {i.deadline}\n‼️ - {i.complexity}\n📂 - {i.file_name}\n👉 - <a href="{i.file}"> Work Files </a>\n<b>Твоя задача</b>: {task}',
                    parse_mode='HTML')
        except:
            await bot.send_photo(chat_id=user, photo=i.image, caption=
                    f'💰 - {i.title}\n💬 - {i.work_comment}\n🗓 - {i.deadline}\n‼️ - {i.complexity}\n📂 - {i.file_name}\n👉 - <a href="{i.file}"> Work Files </a>\n<b>Твоя задача</b>: {task}',
                    parse_mode='HTML')


    user_info = [title_id, task, 'В работе', i.complexity, salary]
    google_table = GoogleTable()
    try:
        google_table.add_user_work(name=cap.name, data=user_info)
    except:
        google_table.add_user_work(name=user_name, data=user_info)

#################################################################################################################################

@admin_router.callback_query(F.data.startswith('next_'))
async def user_skills(callback: types.CallbackQuery, session: AsyncSession):
    user_id = callback.data.split('_')[-1]
    await callback.answer()
    await callback.message.delete()
    user_info = await orm_get_one_user_skills(session, user_id)

    if user_info is None:
        await callback.message.answer('Навыки еще не добавлены\nВыберите пункт <b>"Добавить навыки"</b>', reply_markup=await get_callback_btns(btns={
                    'Добавить навыки': f'addskills_{user_id}', 
                    "⬅️": f'back_user:{user_id}',
                    "↩️": f"all_",
                }, sizes=(1, 2)
            )
        )
    user_spec_skill = user_info.special_skills.replace(', ', '\n• ')
    user_skill = user_info.modeling.replace(';', '\n• ')
    skill_grade = user_skill.replace(':', ' - ')
    await callback.message.answer(
        f'<b>Моделирование</b>:\n• {skill_grade}\n\n<b>Особые навыки</b>\n• {user_spec_skill}', reply_markup=await get_callback_btns(
            btns={
                'Редактировать': f'addedit_{user_info.user_id}',
                "⬅️": f'back_user:{user_info.user_id}',
                "↩️": f"all_",
            }, sizes=(1, 2)
        ),
    )

#####################################################################################################################
class Skills(StatesGroup):
    user_id = State()
    grade = State()
    modeling = State()

    special_skills = State()
    skill = None
    back_step = None
    all_skills = ''

    texts = get_callback_btns(
            btns = {
                    'LP': f'skill_LP',
                    'UCX': f'skill_UCX',
                    'HP': f'skill_HP',
                    'Ground': f'skill_Ground',
                    'Maf': f'skill_Maf',
                    'Flora': f'skill_Flora',
                    'Запекание текстур на LP': f'skill_Запекание текстур на LP',
                    'Текстурирование HP по юдим': f'skill_Текстурирование HP по юдим',
                    '❌ Отменить': f'cancel',
                    'Продолжить ➡️': f'continue',
                }, sizes=(2, 2, 2, 1, 1, 2)
            )

#________________________________________________________________________________________________________________________________
@admin_router.message(StateFilter(Skills), Command("назад"))
@admin_router.message(StateFilter(Skills), F.text.casefold() == "назад")
async def back_step_handler_skill(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == Skills.modeling:
        await message.answer('Предыдущего шага нет, напишите "отмена"')
        return

    previous = None
    for step in Skills.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            return
        previous = step

#________________________________________________________________________________________________________________________________
@admin_router.message(Skills.grade, F.text)
async def add_grade(message: types.Message, state: FSMContext):
    if Skills.all_skills != '':
        Skills.all_skills = Skills.all_skills + ";" + Skills.skill + ':' + message.text
    else:
        Skills.all_skills = Skills.skill + ':' + message.text
    print(Skills.all_skills)
    await message.answer('Выберите подходящий навык сотрудника', reply_markup=Skills.texts)
    
    await state.set_state(Skills.back_step)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(StateFilter(Skills), F.data == 'continue')
async def continue_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    previous = None

    for step in reversed(Skills.__all_states__):
        if step.state == Skills.back_step:
            await state.update_data(modeling=Skills.all_skills)
            await state.set_state(previous)
            return await callback.message.answer('Введи через запятую <i>Особые навыки</i>')

        previous = step

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(StateFilter(Skills), F.data == 'cancel')
async def continue_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    Skills.all_skills = ''
    await callback.message.answer('Удалил все значения\nВведите навыки повторно', reply_markup=Skills.texts)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(StateFilter(None), F.data.startswith('addedit_'))   # Срабатывает при нажатии на кнопку "Редактировать" скиллы
@admin_router.callback_query(StateFilter(None), F.data.startswith('addskills_'))   # Срабатывает при нажатии на кнопку "Добавить навыки"
async def add_skills(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.split('_')[0] == "addedit":
        await callback.message.answer('При редактировании удаляются все значения\nВыберите старые навыки если не хотите их менять')
    user_id = callback.data.split('_')[-1]
    await state.set_state(Skills.user_id)
    await state.update_data(user_id=user_id)
    await callback.answer()
    await callback.message.answer('Выберите подходящий навык сотрудника', reply_markup=Skills.texts)
    await state.set_state(Skills.modeling)


#________________________________________________________________________________________________________________________________
@admin_router.callback_query(Skills.modeling, F.data.startswith('skill_'))
async def add_modeling(callback: types.CallbackQuery, state: FSMContext):
    skill = callback.data.split('_')[-1]
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(f'Введи оценку навыка {skill}')
    Skills.skill = skill
    Skills.back_step = Skills.modeling
    await state.set_state(Skills.grade)


#________________________________________________________________________________________________________________________________
@admin_router.message(Skills.special_skills, F.text)
async def add_modeling(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(special_skills=message.text)
    data = await state.get_data()
    await state.clear()

    if await orm_get_one_user_skills(session, data['user_id']) is None:
        await orm_add_user_skills(
            session,
            user_id=data['user_id'],
            modeling=data['modeling'],
            special_skills=data['special_skills']
        )
    else:
        await orm_update_user_skills(
            session,
            user_id=data['user_id'],
            modeling=data['modeling'],
            special_skills=data['special_skills']
        )
    await message.answer("Успешно добавил навыки!")


#####################################################################################################################
class ProjectPreparation(StatesGroup):
    client = State()
    named = State()
    deadline = State()
    link = State()
    team = State()

#________________________________________________________________________________________________________________________________
@admin_router.message(StateFilter(None), Command("project_preparation"))
async def project_preparation(message: types.Message, state: FSMContext):
    await message.answer('Напиши заказчика', reply_markup=reply.admin_nav)
    await state.set_state(ProjectPreparation.client)

#________________________________________________________________________________________________________________________________
@admin_router.message(ProjectPreparation.client)
async def add_client(message: types.Message, state: FSMContext):
    await state.update_data(client=message.text)
    await message.answer('Напиши название проекта')
    await state.set_state(ProjectPreparation.named)

#________________________________________________________________________________________________________________________________
@admin_router.message(ProjectPreparation.named)
async def add_pj_named(message: types.Message, state: FSMContext):
    await state.update_data(named=message.text)
    await message.answer('Напиши дату сдачи проекта')
    await state.set_state(ProjectPreparation.deadline)

#________________________________________________________________________________________________________________________________
@admin_router.message(ProjectPreparation.deadline)
async def add_proj_deadline(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer('Вставь ссылку на файлы')
    await state.set_state(ProjectPreparation.link)

#________________________________________________________________________________________________________________________________
@admin_router.message(ProjectPreparation.link)
async def add_link(message: types.Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer(
        'Передать файлы для подготовки проекта', reply_markup=await get_callback_btns(
            btns={
                'Отправить': f'first_team',
            }
        )
    )
    await state.set_state(ProjectPreparation.team)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(ProjectPreparation.team, F.data)
async def add_team(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.delete_reply_markup()
    await callback.answer('Отправил данные')
    data = await state.get_data()
    await state.clear()
    NewProject.support = data
    client = data['client']
    named = data['named']
    deadline = data['deadline']
    link = data['link']

    await bot.send_message(chat_id=(285062516), text='⬇️⬇️⬇️Данные для подготовки проекта⬇️⬇️⬇️')
    await bot.send_message(chat_id=(285062516), text=(
        f'<b>Заказчик:</b>\n<i>{client}</i>\n<b>Название проекта:</b>\n<i>{named}</i>\n<b>Срок выполнения:</b> {deadline}\n<b>Ссылка на файлы:</b>\n{link}'
        ), disable_web_page_preview=True, reply_markup=await get_callback_btns(
            btns={
                'Отдать проект в работу Егору': f'help',
                'Отправить работу Эрику': 'project_880624724',
                'Отправить работу Данилу': 'project_834162337',
                }, sizes=(1,2)
        )
    )
    
    await callback.message.answer('Отправил данные', reply_markup=reply.admin_kb)


#####################################################################################################################
class CheckingProj(StatesGroup):
    title = State()
    comment = State()
    deadline = State()
    file = State()
    worker = State()

#________________________________________________________________________________________________________________________________
@admin_router.message(CheckingProj.title, F.text)
async def add_title(message: types.Message, state: FSMContext):
    if len(message.text) >= 25:
        await message.answer('❌ Сократи название работы до 25-ти символов.\n\nЖду более короткого названия ☺️', reply_markup=reply.admin_nav)
        return await state.set_state(CheckingProj.title)
    
    await state.update_data(title=message.text)
    await message.answer('Введи комментарий к работе')
    await state.set_state(CheckingProj.comment)

#________________________________________________________________________________________________________________________________
@admin_router.message(CheckingProj.comment, F.text)
async def add_comment(message: types.CallbackQuery, state: FSMContext):
    if len(message.text) >= 25:
        await message.answer('❌ Сократи комментарий до 25-ти символов.\n\nЖду более короткого комментария 🫡', reply_markup=reply.admin_nav)
        return await state.set_state(CheckingProj.comment)

    await state.update_data(comment=message.text)
    await message.answer('Введи срок выполнения работы')
    await state.set_state(CheckingProj.deadline)

#________________________________________________________________________________________________________________________________
@admin_router.message(CheckingProj.deadline, F.text)
async def add_deadline(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer('Прикрепи файл работы')
    await state.set_state(CheckingProj.file)

#________________________________________________________________________________________________________________________________
@admin_router.message(CheckingProj.file, F.document)
async def add_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document.file_id)

    await message.answer("Добавь исполнителя", reply_markup=await get_callback_btns(
        btns={
            "Александра Люфт": "Александра Люфт @EtoNeFlirt",
            "Ирина Штукарева": "Ирина Штукарева @peachbbyi",
            # "Фатеев Никита": "Фатеев Никита @Kic9ndr",
            }
        )
    )
    await state.set_state(CheckingProj.worker)

#________________________________________________________________________________________________________________________________
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
@admin_router.message(CheckingProj.file, F.text)
async def add_file(message: types.Message, state: FSMContext):
    await message.answer('<b>Необходимо отправить файл</b>\n\nПопробуй на этот раз загрузить файл')
    return await state.set_state(CheckingProj.file)
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#________________________________________________________________________________________________________________________________
@admin_router.callback_query(CheckingProj.worker, F.data)
async def add_link(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    await callback.answer()
    await callback.message.delete()
    await state.update_data(worker=callback.data)
    data = await state.get_data()
    await state.clear()

    await orm_add_work(
        session,
        title=data['title'],
        work_comment=data['comment'],
        deadline=data['deadline'],
        complexity=None,
        file_name=None,
        file=data['file'],
        worker_name=data['worker'],
        image=None,
        ready_status=True,
    )

    title = data['title']
    comment = data['comment']
    deadline = data['deadline']
    file = data['file']

    worker = await orm_get_one_user_by_name(session, callback.data.split(' @')[0])

    await orm_add_user_work(
        session,
        user_id=worker.user_id,
        current_work=title,
        task='Проверка работы',
        salary=0,
        check_work=False
    )

    work = await orm_get_one_user_work(session, worker.user_id, title)
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    mes = await bot.send_document(chat_id=int(admin_chat), document=file, caption=
        f'Работа <i>{title}</i> на проверку для @{worker.username}\nКомментарий к работе: {comment}\n\n',
        message_thread_id=int(admin_message_thread))

    send_work = await bot.send_document(chat_id=int(work_check), document=file, caption=
            f'Работа <i>{title}</i> на проверку для @{worker.username}\nКомментарий к работе: {comment}\n\n',
            reply_markup=await get_callback_btns(btns={
                'Принять работу': f"accept_{title}_{worker.user_id}",
                'Отправить правки/комментарий': f"edits_{title}_{worker.user_id}"
            }, sizes={1,1}
        )
    )
    
    await orm_add_id_send_message(
        session,
        id=send_work.message_id,
        title=title,
        user_id=worker.user_id,
        work_link='Выше прикрепленный файл ⬆️',
        work_id=random.randint(1, 10000),
        mes_id=0,
    )

    await orm_update_user_status(session, worker.user_id, True)       # Изменение статуса проверки на "Проверка" в базе данных

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    await bot.send_document(
        chat_id=worker.user_id,
        document=file,
        caption=f'<b>Вам назначена задача для проверки</b>\n\n<u>{title}</u>\nКомментарий к работе: <i>{comment}</i>\nВыполнить до - {deadline}'
    )
    await callback.message.answer('Задача успешно создана', reply_markup=admin_kb)

#####################################################################################################################
class NewProject(StatesGroup):
    send_project = State()

    support = None
    team = None

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('help'))
async def new_project(callback: types.CallbackQuery, bot: Bot):
    await callback.answer('Отправил данные')
    data = NewProject.support
    client = data['client']
    named = data['named']
    deadline = data['deadline']
    link = data['link']
    NewProject.support = None

    await bot.send_message(chat_id=(5617295673), text='⬇️⬇️⬇️Данные для подготовки проекта⬇️⬇️⬇️')
    await bot.send_message(chat_id=(5617295673), text=(
        f'<b>Заказчик:</b>\n<i>{client}</i>\n<b>Название проекта:</b>\n<i>{named}</i>\n<b>Срок выполнения:</b> {deadline}\n<b>Ссылка на файлы:</b>\n{link}'
        ), disable_web_page_preview=True, reply_markup=await get_callback_btns(
            btns={
                'Отправить работу Эрику': 'project_880624724',
                'Отправить работу Даниле': 'project_834162337',
                }
        )
    )
#________________________________________________________________________________________________________________________________
@admin_router.callback_query(StateFilter(None), F.data.startswith('project_'))
async def new_project(callback: types.CallbackQuery, state: FSMContext):
    team = callback.data.split('_')[-1]
    await callback.answer()
    NewProject.team = int(team)

    await callback.message.answer('Вставь ссылку на файлы проекта', reply_markup=reply.admin_nav)
    await state.set_state(NewProject.send_project)

#________________________________________________________________________________________________________________________________
@admin_router.message(NewProject.send_project, F.text)
async def send_new_project(message: types.Message, state: FSMContext, bot: Bot):
    send_project=message.text
    adm_proj = NewProject.team

    await bot.send_message(chat_id=int(adm_proj), text=f'Тебе отправили файлы для нового <b>Проекта</b>!\n\n{send_project}', disable_web_page_preview=True)
    await bot.send_message(chat_id=int(admin_chat), text=send_project, message_thread_id=int(3), disable_web_page_preview=True)

    await state.clear()
    await message.answer('Отправил файлы', reply_markup=reply.admin_kb)


#####################################################################################################################
class NewTeam(StatesGroup):
    team_name = State()
    captain = State()
    teammates = State()
    confirm = State()

    workers = []
#________________________________________________________________________________________________________________________________
@admin_router.message(or_f(Command('create_team'), F.text == 'Создание команды 🥇'))
async def cmd_create_team(message: types.Message, state: FSMContext):
    await message.answer('Напиши название команды')
    await state.set_state(NewTeam.team_name)

#________________________________________________________________________________________________________________________________
@admin_router.message(NewTeam.team_name, F.text)
async def add_team_name(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.update_data(team_name = message.text)
    await message.answer('Выбери сотрудника на роль капитана', reply_markup=await choice_worker_btns(session))
    await state.set_state(NewTeam.captain)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(NewTeam.captain, F.data)
async def add_captain(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    captain_name = callback.data.split(' @')[0]
    await state.update_data(captain=captain_name)
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(f'<b>Отлично, капитан команды: {captain_name}</b>\nТеперь выбери <u>несколько сотрудников</u> в эту команду и нажми "Продолжить"')
    await asyncio.sleep(1)
    await callback.message.answer('<b>Список всех сотрудников</b>', reply_markup=await choice_workers_btns(session))
    await state.set_state(NewTeam.teammates)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(NewTeam.teammates, F.data.startswith('worker_'))
async def add_teammates(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    name = callback.data.split('_')[-1]
    NewTeam.workers.append(name)
    await callback.message.delete()
    await callback.answer(f'Добавил {name}')
    workers = '\n'.join(NewTeam.workers)
    await callback.message.answer(f'<b>Добавил:</b>\n{workers}', reply_markup=await choice_workers_btns(session))

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('continue'))
async def add_teammates(callback: types.CallbackQuery, state: FSMContext):
    workers = '\n'.join(NewTeam.workers)
    data = await state.get_data()
    captain = data['captain']
    await callback.answer()
    await callback.message.answer(f'<u>Оставляем команду в таком составе?</u>\n\n<b>Капитан: {captain}</b>\n{workers}', reply_markup=await get_callback_btns(
                            btns={
                                'Да': f'confirm_team',
                                'Нет': f'return_choice'
                            }
                        )
                    )
    await state.set_state(NewTeam.confirm)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(NewTeam.confirm, F.data)
async def confirmation(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    if callback.data == 'return_choice':
        NewTeam.workers = []
        await callback.message.answer('<b>Выбери всех сотрудников снова</b>')
        await callback.message.answer('<b>Список всех сотрудников</b>', reply_markup=await choice_workers_btns(session))
        return await state.set_state(NewTeam.teammates)
    
    user = await orm_get_user_name(session, data['captain'])
    await orm_add_teams(
        session,
        user.user_id,
        data['captain'],
        True,
        data['team_name']
    )

    for worker in NewTeam.workers:
        user = await orm_get_user_name(session, worker)
        await orm_add_teams(
            session,
            user.user_id,
            worker,
            False,
            data['team_name']
        )

    await callback.message.answer('Отлично, добавил команду')


###################################################################################################
@admin_router.callback_query(F.data.contains('back_user'))
@admin_router.callback_query(F.data.contains('@'))
async def choice_workers_data(callback: types.CallbackQuery, session: AsyncSession):
    user_name = callback.data.split(' @')[0]
    user_id = callback.data.split(':')[-1]
    await callback.message.delete()
    await callback.answer()
    user = await orm_get_user_name(session, user_name)
    if user is None:
        user = await orm_get_one_user(session, user_id)

    payment = user.payment_details
    programs = user.work_programs
    city = user.residence_city

    user_works = []
    users = await orm_get_users_works(session)          # Получаю всех юзеров с параметром работ

    for user_info in users:                                  # Вход в экземпляр юзера
        for i in user_info.work:                             # Вход в экземпляр UserID.work и получение данных
            if i.user_id == user.user_id:
                user_works.append(i.current_work)

    user_skill = await orm_get_one_user_skills(session, user.user_id)
    if user_skill is None:
        role = 'Странник'
    else:
        role = user_skill.role

    if user_works == []:
        user_works.append("У человека нет работ")
    if payment is None:
        payment = 'Не указан'
    if programs is None:
        programs = 'Не указаны'
    if city is None:
        city = 'не из этого мира 👽'

    await callback.message.answer(
        f'<b>Имя</b>: {user.name}\n<b>Юзернейм</b>: @{user.username}\n<b>{role}</b>\n\n<b>Счет</b>: {payment}\n<b>Программы</b>: {programs}\n<i><b>Город</b></i> - {city}\n\n<b>Ссылка на Яндекс Диск:</b>\n{user.drive}\n<b>Работы сотрудника</b>:\n' + '\n'.join(user_works),
        reply_markup=await get_callback_btns(
            btns={
                'Редактировать': f'edit_profile_{user.user_id}',
                "Удалить": f'delete_user_db_{user.user_id}',
                "↩️": f"all_",
                "➡️": f"next_{user.user_id}"
            }, sizes=(2, 2)
        ), disable_web_page_preview=True
    )

#################################################################################################################################
class DeleteUserFromDB(StatesGroup):
    delete = State()

    user_id = None

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(F.data.startswith('delete_user_db_'))
async def accept_delete_user_from_db(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = callback.data.split("_")[-1]
    await callback.message.delete()
    DeleteUserFromDB.user_id = user_id

    user = await orm_get_one_user(session, user_id)
    await callback.answer()
    await callback.message.answer(
        f'Вы уверены, что хотите удалить сотрудника <b>{user.name} @{user.username}</b>?', 
        reply_markup=await get_callback_btns(
            btns={
                "Да": "delete_user_from_db",
                "Нет": "do_not_delete",
            }
        )
    )

    await state.set_state(DeleteUserFromDB.delete)

#________________________________________________________________________________________________________________________________
@admin_router.callback_query(DeleteUserFromDB.delete, F.data)
async def delete_user_from_db(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.clear()

    if callback.data == "do_not_delete":
        await callback.message.answer('Ладно, ладно. Не удалю я его')

        await asyncio.sleep(2)
        return await callback.message.answer(
            'Выбери сотрудника', reply_markup=await choice_worker_btns(session)
        )
    
    else:
        await orm_delete_user(session, DeleteUserFromDB.user_id)
        await callback.message.answer('Пользователь успешно удален')

        await asyncio.sleep(2)
        return await callback.message.answer(
            'Выбери сотрудника', reply_markup=await choice_worker_btns(session)
        )
