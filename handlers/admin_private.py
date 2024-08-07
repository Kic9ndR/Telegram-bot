import os
from aiogram import F, Bot, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession


from database import orm_query
from filters.chat_types import ChatFilter, IsAdmin
from kbrd import reply
from kbrd.inline import choise_worker_btns, get_callback_btns
from kbrd.reply import admin_kb
# from googlesheets.table import GoogleTable   ------ for google sheets


#----------------------------------------------------------------------------------
admin_router = Router()
admin_router.message.filter(ChatFilter(["private"]), IsAdmin())

user_chat = os.getenv('USER_CHAT')
user_message_thread = os.getenv('USER_MESSAGE_THREAD')

admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')


class CreateTask(StatesGroup):
    title = State()
    deadline = State()
    file_name = State()
    file = State()
    # worker_name = State()
    image = State()

    title_for_change = ''
    status_create = bool

    texts = {
        'CreateTask:title': 'Введите работы повторно: ',
        'CreateTask:deadline': 'Введите срок выполнения повторно: ',
        'CreateTask:file_name': 'Введите названия файла повторно: ',
        'CreateTask:file': 'Отправте ссылку повторно: ', 
        'CreateTask:image': 'Загрузите фото повторно: ',
    }

#---------------------------------------------------------------------------------- 
@admin_router.message(Command("admin"))
async def admin(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Что хотите сделать?", reply_markup=admin_kb)


#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список сотрудников 📋")
async def project_klnd(message: types.Message, session: AsyncSession):
    await message.answer('Список сотрудников Века:')
    for users in await orm_query.orm_get_user_info(session):
        await message.answer(f'{users.first_name} @{users.username}', reply_markup=admin_kb)


"""
Получение таблицу сотрудников с google sheets
"""
    # google_table = GoogleTable()
    # second_column = google_table.get_second_column()
    # await message.answer('\n'.join(second_column))

#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Таблица работ 𝄜")
async def task_distrib(message: types.Message):
    await message.answer(
        "Ссылка на таблицу: \nhttps://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g", 
        reply_markup=admin_kb
                         )
#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список работ 📜")
async def project_klnd(message: types.Message, session: AsyncSession):
    await message.answer('Вот список:')
    for title in await orm_query.orm_get_all_works(session):
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nНазначены:\n{title.worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'change_{title.title}',
                'Полностью удалить работу': f'deleteready_{title.title}',
                }), parse_mode='HTML'
            )


@admin_router.message(F.text == "В процессе создания 🔄")
async def process_of_creation(message: types.Message, session: AsyncSession):
    await message.answer('Работы в процессе создания:')
    for title in await orm_query.orm_get_all_unready(session):
        hyperlink = f'<a href="{title.file}"> Work Files </a>'
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nСписок исполнителей\n{title.worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'change_{title.title}',
                'Полностью удалить работу': f'delete_{title.title}',
                'Отправить в работу': f'send_{title.title}',
            }, sizes=(2,1,1)), parse_mode='HTML',
        )



"""
Удаление выложенной в группу работы ===============================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('deleteready_'))
async def change_work(callback: types.CallbackQuery, session: AsyncSession):
    title_id = callback.data.split('_')[-1]
    await orm_query.orm_delete_ready_work(session, title_id)
    await callback.answer('Работа удалена')
    await callback.message.answer('Работа удалена')


"""
Удаление незаконченной работы =====================================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('delete_'))
async def change_work(callback: types.CallbackQuery, session: AsyncSession):
    title_id = callback.data.split('_')[-1]
    await orm_query.orm_delete_un_work(session, title_id)
    await callback.answer('Работа удалена')
    await callback.message.answer('Работа удалена')


"""
Отправка работы в группу и назначенным сотрудникам ================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('send_'))
async def send_work(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    title_id = callback.data.split('_')[-1]
    work = await orm_query.orm_get_work(session, title_id)
    await orm_query.orm_delete_un_work(session, title_id)

    await orm_query.orm_add_work(
        session, 
        title = work.title,
        deadline = work.deadline,
        file_name = work.file_name,
        file = work.file,
        worker_name = work.worker_name,
        image = work.image,
        )
    
    try:
        for user_id in await orm_query.orm_get_user_info(session):
            if user_id.username in work.worker_name:
                await orm_query.orm_add_current_work(session, user_id.user_id, title_id) 
                task = work.worker_name.split("-")[0]
                await bot.send_message(chat_id=user_id.user_id, text='Вам назначена новая работа')
                await bot.send_photo(chat_id=user_id.user_id, photo=work.image, caption=
                        f'💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 - <a href="{work.file}"> Work Files </a>\n{task}',
                        parse_mode='HTML')
    except Exception as e:
        await callback.message.answer(f'Ошибка: {e}\n')

    hyperlink = f'<a href="{work.file}"> Work Files </a>'
    await bot.send_photo(chat_id=int(user_chat), photo=work.image, caption=
                    f"💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 {hyperlink}\n{work.worker_name}",
                    message_thread_id=int(user_message_thread), parse_mode='HTML')


    await callback.answer()
    await callback.message.answer('Работа отправлена!')



"""
Вход в состояние изменения работы =================================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    title_id = callback.data.split('_')[-1]
    title_for_change = await orm_query.orm_get_work(session, title_id)
    if title_for_change is None:
        title_for_change = await orm_query.orm_get_ready_work(session, title_id)

    CreateTask.status_create = False
    CreateTask.title_for_change = title_for_change
    await callback.answer()
    await callback.message.answer(
        'Введите название работы\nОтправьте "." если не хотите вносить изменения', reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CreateTask.title)



################################# Код ниже для машины состояний (FSM) ##########################################
"""
=========================================== Создание работы ====================================================
"""
################################################################################################################

@admin_router.message(StateFilter(None), F.text == "Создание задачи ✍🏼")
async def create_task(message: types.Message, state: FSMContext):
    CreateTask.status_create = True
    await message.answer("Введите название работы: ", 
                         reply_markup=reply.admin_nav)
    await state.set_state(CreateTask.title)


################################################ Команда Отмены ################################################
@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=admin_kb)

################################################ Команда назад ################################################
@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
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
    if message.text == '.' and CreateTask.status_create is False:
        await state.update_data(title=CreateTask.title_for_change.title)
    else:
        await state.update_data(title=message.text)

    await message.answer("Введите срок выполнения: ")
    await state.set_state(CreateTask.deadline)

@admin_router.message(CreateTask.title)
async def set_title2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать текст ")


################################################ Ввод дедлайна ################################################

@admin_router.message(CreateTask.deadline, or_f(F.text, F.text == '.'))
async def set_deadline(message: types.Message, state: FSMContext):
    if message.text == '.' and CreateTask.status_create is False:
        await state.update_data(deadline = CreateTask.title_for_change.deadline)
    else:
        await state.update_data(deadline=message.text)
    await message.answer("Введите название файла: ")
    await state.set_state(CreateTask.file_name)

@admin_router.message(CreateTask.deadline)
async def set_deadline2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать число ")


################################################ Ввод названия файла ################################################

@admin_router.message(CreateTask.file_name, or_f(F.text, F.text == '.'))
async def set_file_name(message: types.Message, state: FSMContext):
    if message.text == '.' and CreateTask.status_create is False:
        await state.update_data(file_name = CreateTask.title_for_change.file_name)
    else:
        await state.update_data(file_name=message.text)
    await message.answer("Добавьте сссылку на рабочие файлы ")
    await state.set_state(CreateTask.file)

@admin_router.message(CreateTask.file_name)
async def set_file_name2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно.\nНеобходимо добавить сссылку на рабочие файлы")


################################################ Ввод файла ################################################

@admin_router.message(CreateTask.file, or_f(F.text, F.text == '.'))
async def set_file(message: types.Message, state: FSMContext):
    if message.text == '.' and CreateTask.status_create is False:
        await state.update_data(file=CreateTask.title_for_change.file)
    else:
        await state.update_data(file=message.text)
    await message.answer("Загрузите фото обложки задачи")
    await state.set_state(CreateTask.image)
    # await message.answer('Если хотите изменить исполнителей напишите: "Да"\n(При изменении удалятся все сотрудники).')
    # await state.set_state(CreateTask.worker_name)


@admin_router.message(CreateTask.file)
async def set_file2(message: types.Message):
    await message.answer("Ввели данные неверно.\nНеобходимо загрузить фото обложки задачи ")


################################################ Изменение Исполнителя ################################################

# @admin_router.message(CreateTask.worker_name, or_f(F.text, F.text == '.'))
# async def change_worker(message: types.Message, state: FSMContext):
#     if message.text == '.':
#         await state.update_data(worker_name=CreateTask.title_for_change.worker_name)
#     else:
#         await state.update_data(worker_name=message.text.lower())

    # await message.answer("Загрузите фото: ")
    # await state.set_state(CreateTask.image)


################################################ Загрузка фото ################################################

@admin_router.message(CreateTask.image, or_f(F.photo, F.text == '.'))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == '.' and CreateTask.status_create is False:
        await state.update_data(image=CreateTask.title_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    title_id = data['title']
    i = await orm_query.orm_get_work(session, title_id)

    try:
        if CreateTask.status_create is False:
            if i is not None:          # Выполняется проверка есть ли в UnreadyWorks данное название или нет
                await orm_query.orm_change_unready(session, CreateTask.title_for_change.title, data)
            else:
                await orm_query.orm_change_ready_work(session, CreateTask.title_for_change.title, data)
            await message.answer("Задача обновлена!", reply_markup=admin_kb)
        else:
            await orm_query.orm_add_task(session, data)
            await message.answer("Задача добавлена!", reply_markup=admin_kb)
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру",
            reply_markup=admin_kb,
        )

    await state.clear()

    # if data['worker_name'] == 'да':
    #     await orm_query.orm_delete_worker(session, title_id)


    """
    Если добавляли работу выводим список незаконченных работ
    """

    if i is not None:            # Выполняется проверка есть ли в UnreadyWorks данное название или нет
        await message.answer_photo(photo=data['image'], caption=
            f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{i.title}',
                'Изменить': f'change_{i.title}',
                'Полностью удалить работу': f'delete_{i.title}',
                'Отправить в работу': f'send_{i.title}',
            }, sizes=(2,1,1)), parse_mode='HTML'
        )
    else:
        """
        Если изменяли работу выводим список законченных работ
        """
        i = await orm_query.orm_get_ready_work(session, title_id)
        await message.answer_photo(photo=i.image, caption=
            f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}',
            reply_markup=get_callback_btns(btns={
                    'Назначить': f'appoint_{i.title}',
                    'Изменить': f'change_{i.title}',
                    'Полностью удалить работу': f'delete_{i.title}',
                }), parse_mode='HTML'
            )
  
    CreateTask.title_for_change = ''


@admin_router.message(CreateTask.image)
async def add_image2(message: types.Message):
    await message.answer("Ввели данные неверно. Необходимо загрузить фото")


#################################################################################################################
"""
Назначение сотрудника============================================================================================
"""
#################################################################################################################

class ChoiseWorker(StatesGroup):
    work_id = State()
    task = State()
    name = State()


################################################ Получение id работы ################################################

@admin_router.callback_query(StateFilter(None), F.data.startswith('appoint_'))
async def add_work_id(callback: types.CallbackQuery, state: FSMContext):
    title_id = callback.data.split('_')[-1]
    await state.set_state(ChoiseWorker.work_id)
    await state.update_data(work_id=title_id)
    await state.set_state(ChoiseWorker.task)
    await callback.answer('Введите задачу:')
    await callback.message.answer('Введите задачу:', reply_markup=reply.admin_nav)
    await callback.message.delete()


################################################ Выбор задачи ################################################

@admin_router.message(ChoiseWorker.task, F.text)
async def add_task(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(task=message.text)
    await state.set_state(ChoiseWorker.name)
    await message.answer('Выберите сотрудника:', reply_markup=await choise_worker_btns(session))


################################################ Распределение работы ################################################

@admin_router.callback_query(ChoiseWorker.name, F.data)
async def add_name(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    await state.update_data(name=callback.data)
    data = await state.get_data()
    title_id = data['work_id']
    task_and_name = str(f"🫡  {data['task']} - {data['name']}")
    try:
        await orm_query.orm_appoint_worker(session, title_id, task_and_name)

        await callback.answer('Выполнено')
        await callback.message.answer('Работа назначена', reply_markup=reply.admin_kb)


        await state.clear()
    except Exception as e:
        await callback.answer(f'Ошибка: {e}')
        await callback.message.answer(f'Ошибка: {e}', reply_markup=reply.admin_kb)
        await state.clear()
    
    await callback.message.delete()

    i = await orm_query.orm_get_ready_work(session, title_id)
    if i.title != title_id:
        await callback.message.answer_photo(photo=i.image, caption=
            f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}',
            reply_markup=get_callback_btns(btns={
                    'Назначить': f'appoint_{i.title}',
                    'Изменить': f'change_{i.title}',
                    'Полностью удалить работу': f'delete_{i.title}',
                    'Отправить в работу': f'send_{i.title}',
                }, sizes=(2,1,1)), parse_mode='HTML'
            )
    else:
        work = await orm_query.orm_get_ready_work(session, title_id)
        await orm_query.orm_update_worker_work(session, title_id, task_and_name)
        task = data['task']
        for user_id in await orm_query.orm_get_user_info(session):
            if user_id.first_name in work.worker_name:
                await orm_query.orm_add_current_work(session, user_id.user_id, title_id) 
                await bot.send_message(chat_id=user_id.user_id, text='Вам назначена новая работа')
                await bot.send_photo(chat_id=user_id.user_id, photo=work.image, caption=
                        f'{work.title}\n🗓 Срок выполнения до - {work.deadline}\n📂 Название файла- {work.file_name}\n👉 - <a href="{work.file}"> Work Files </a>\nВаша задача -{task}',
                        parse_mode="HTML")
        
        await callback.message.answer_photo(photo=i.image, caption=
                f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}',
                reply_markup=get_callback_btns(btns={
                        'Назначить': f'appoint_{i.title}',
                        'Изменить': f'change_{i.title}',
                        'Полностью удалить работу': f'delete_{i.title}',
                    }), parse_mode='HTML'
                )


@admin_router.message(ChoiseWorker.name)
async def add_name2(message: types.Message):
    await message.answer("Необходимо выбрать имя на клавиатуре")