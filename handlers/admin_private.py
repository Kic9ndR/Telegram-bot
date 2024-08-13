import os
from aiogram import F, Bot, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_query import *
from filters.chat_types import ChatFilter, IsAdmin
from kbrd import reply
from kbrd.inline import choise_worker_btns, get_callback_btns, get_url_btns
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
    change_work = False

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


"""
Кнопки для списка сотрудников =====================================================================
"""
@admin_router.message(F.text == "Списки сотрудников 📋")
async def project_klnd(message: types.Message):
    await message.answer('Какой список тебе нужен?', reply_markup=get_callback_btns(btns={
                'Занятые': f"busy_",
                'Свободные': f'available_',
                'Все сотрудники': f'all_',
                }
            )
        )


#-------------------------------------------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith('busy_'))
async def all_worker(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    list = []
    for users in await orm_get_users(session):
        if users.current_work is not None:
            list.append(f'{users.name} @{users.username}')

    if list != []:
        await callback.message.answer('Список занятых сотрудников:', reply_markup=admin_kb)
        await callback.message.answer('\n'.join(list))
    else:
        await callback.message.answer('Все сотрудники свободны')


#-------------------------------------------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith('available_'))
async def all_worker(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    list = []
    for users in await orm_get_users(session):
        if users.current_work is None:
            list.append(f'{users.name} @{users.username}')
    if list != []:
        await callback.message.answer('Список свободных сотрудников:', reply_markup=admin_kb)
        await callback.message.answer('\n'.join(list))
    else:
        await callback.message.answer('Все сотрудники заняты')


#-------------------------------------------------------------------------------------------------------------
@admin_router.callback_query(F.data.startswith('all_'))
async def all_worker(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    list = []
    await callback.message.answer('Список всех сотрудников:', reply_markup=admin_kb)
    for users in await orm_get_users(session):
        list.append(f'{users.name} @{users.username}')
    await callback.message.answer('\n'.join(list))



"""
Получение таблицу сотрудников с google sheets =====================================================
"""
    # google_table = GoogleTable()
    # second_column = google_table.get_second_column()
    # await message.answer('\n'.join(second_column))

@admin_router.message(F.text == "Таблицы 𝄜")
async def task_distrib(message: types.Message):
    # await message.answer(
    #     "Ссылка на таблицу: \nhttps://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g", 
    #     reply_markup=admin_kb
    #                      )

    await message.answer('Список всех таблиц:', reply_markup=get_url_btns(
        btns={
                'Таблица сотрудников': 'https://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g',
                'График работы': 'https://docs.google.com/spreadsheets/d/1VTlLg0JOvnw-owN4xpzwl7Vl_5vtooEukcCH3phl6Nw/edit?gid=1574826567#gid=1574826567'
            }, sizes={1, 1}
        )
    )


"""
Кнопки для выбора работы ==========================================================================
"""
@admin_router.message(F.text == "Список работ 📜")
async def project_klnd(message: types.Message, bot: Bot):
    await bot.send_chat_action(chat_id=message.from_user.id, action='typing')
    await message.answer(
        '<b>Выберите список:</b>\n\n<b>Опубликованный список</b> -- отправлены исполнителям и в группу\n<b>В процессе создания</b> -- не был отправлен в рабочую группу и назначенным сотрудникам', 
        reply_markup=get_callback_btns(btns=
            {
                'Опубликованный список': f'realised_',
                'В процессе создания': f'process_',
            }, sizes={1, 1}
        ), parse_mode='HTML'
    )



@admin_router.callback_query(F.data.startswith('realised_'))
async def realised_list(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    await callback.message.delete()
    await bot.send_chat_action(chat_id=callback.from_user.id, action='typing')
    await callback.answer()
    await callback.message.answer('Вот список опубликованных работ:')
    for title in await orm_get_works(session):
        if title.ready_status == True:
            if title.worker_name is None:
                worker_name = 'Исполнители еще не назначены'
            else:
                worker_name = title.worker_name
    
            await callback.message.answer_photo(
                title.image,
                caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nНазначены:\n{worker_name}',
                reply_markup=get_callback_btns(btns={
                    'Назначить': f'appoint_{title.title}',
                    'Изменить': f'change_{title.title}',
                    'Отправить в архив': f'sendarchive_{title.title}',
                    'Полностью удалить работу': f'delete_{title.title}',
                    }, sizes=(2,1,1)), parse_mode='HTML'
                )


@admin_router.callback_query(F.data.startswith('process_'))
async def process_of_creation(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    await callback.message.delete()
    await bot.send_chat_action(chat_id=callback.from_user.id, action='typing')
    await callback.answer()
    await callback.message.answer('Работы в процессе создания:')
    for title in await orm_get_works(session):
        if title.ready_status == False:
            if title.worker_name is None:
                worker_name = 'Исполнители еще не назначены'
            else:
                worker_name = title.worker_name
            await callback.message.answer_photo(
                title.image,
                caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nСписок исполнителей\n{worker_name}',
                reply_markup=get_callback_btns(btns={
                    'Назначить': f'appoint_{title.title}',
                    'Изменить': f'change_{title.title}',
                    'Полностью удалить работу': f'delete_{title.title}',
                    'Отправить в работу': f'send_{title.title}',
                }, sizes=(2,1,1)), parse_mode='HTML',
            )



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
            work.deadline,
            work.file_name,
            work.file,
            work.worker_name,
            work.image
        )
        for i in await orm_get_users(session):
            if i.current_work == title_id:
                await orm_delete_user_work(session, i.user_id)
        await orm_delete_work(session, title_id)

    await bot.send_photo(chat_id=-1002038832368, photo=work.image, caption=
                    f"💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 <a href='{work.file}'> Work Files </a>\n{work.worker_name}", 
                    message_thread_id=296, parse_mode='HTML',
                )
    await callback.message.answer('Работа отправлена в архив')

"""
Получение работ из архива =========================================================================
"""
@admin_router.message(or_f(Command("archive"), (F.text.lower() == "архив 🗄️")))
async def archive_cmd(message: types.Message, session: AsyncSession):
    for i in await orm_get_archive_works(session):
        await message.answer_photo(photo=i.image, caption=
                f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}'
        )


"""
Удаление работы ===================================================================================
"""
class DeleteWork(StatesGroup):
    title_id = State()
    approve = State()


@admin_router.callback_query(StateFilter(None), F.data.startswith('delete_'))
async def change_work(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    title_id = callback.data.split('_')[-1]
    await state.set_state(DeleteWork.title_id)
    await state.update_data(title_id=title_id)
    await callback.message.answer('Вы уверены что хотите удалить работу?\n(Да или Нет)')
    await state.set_state(DeleteWork.approve)


@admin_router.message(DeleteWork.approve, F.text)
async def change_work(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.update_data(approve=message.text)
    data = await state.get_data()
    if data['approve'] == 'Да':
        for i in await orm_get_users(session):
            if i.current_work == data['title_id']:
                await orm_delete_user_work(session, i.user_id)
        await orm_delete_work(session, data['title_id'])
        await message.answer('Работа удалена')
    else:
        await message.answer('Хух, ну и хорошо\n')
        await project_klnd(message)

    await state.clear()

"""
Отправка работы в группу и назначенным сотрудникам ================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('send_'))
async def send_work(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    title_id = callback.data.split('_')[-1]
    work = await orm_get_one_work(session, title_id)
    await orm_update_work_status(session, title_id, True)

    try:        # Назначение работы на сотрудника
        for users in await orm_get_users(session):
            if users.username in work.worker_name:
                task = work.worker_name.split("-")[0]
                await bot.send_message(chat_id=users.user_id, text='Вам назначена новая работа')
                await bot.send_photo(chat_id=users.user_id, photo=work.image, caption=
                        f'💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 - <a href="{work.file}"> Work Files </a>\n{task}',
                        parse_mode='HTML')
                        
    except Exception as e:
        await callback.message.answer(f'Ошибка: {e}\n')

    # Отправка работы в группу
    await bot.send_photo(chat_id=int(user_chat), photo=work.image, caption=
                    f"💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 <a href='{work.file}'> Work Files </a>\n{work.worker_name}",
                    message_thread_id=int(user_message_thread), parse_mode='HTML'
                )


    await callback.answer()
    await callback.message.answer('Работа отправлена!')

"""
Вход в состояние изменения работы =================================================================
"""
@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    title_id = callback.data.split('_')[-1]
    title_for_change = await orm_get_one_work(session, title_id)

    CreateTask.change_work = True
    CreateTask.title_for_change = title_for_change
    await callback.answer('Изменение работы')
    await callback.message.answer(
        'Введите название работы\nОтправьте "." если не хотите вносить изменения', reply_markup=reply.admin_nav
    )
    await state.set_state(CreateTask.title)



################################# Код ниже для машины состояний (FSM) ##########################################
"""
=========================================== Создание работы ====================================================
"""
################################################################################################################

@admin_router.message(StateFilter(None), F.text == "Создание задачи ✍🏼")
async def create_task(message: types.Message, state: FSMContext):
    CreateTask.change_work = False
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
    if message.text == '.' and CreateTask.change_work is True:
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
    if message.text == '.' and CreateTask.change_work is True:
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
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(file_name = CreateTask.title_for_change.file_name)
    else:
        await state.update_data(file_name=message.text)
    await message.answer("Добавьте ссылку на рабочие файлы ")
    await state.set_state(CreateTask.file)

@admin_router.message(CreateTask.file_name)
async def set_file_name2(message: types.Message, state: FSMContext):
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
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == '.' and CreateTask.change_work is True:
        await state.update_data(image=CreateTask.title_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    title_id = data['title']

    try:
        if CreateTask.change_work == True:      # Если работа была обновлена, то:
            await orm_update_work(session, CreateTask.title_for_change.title, data)
            await message.answer("Задача обновлена!", reply_markup=admin_kb)
        else:
            await orm_add_work(
                session, 
                title=data['title'],
                deadline=data['deadline'],
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

    # if data['worker_name'] == 'да':
    #     await orm_query.orm_delete_worker(session, title_id)


    """
    Если добавляли работу выводим список незаконченных работ
    """
    if i.ready_status == False:     # Выполняется проверка есть ли данное название и в каком статусе работа
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
        await message.answer_photo(photo=i.image, caption=
            f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}',
            reply_markup=get_callback_btns(btns={
                    'Назначить': f'appoint_{i.title}',
                    'Изменить': f'change_{i.title}',
                    'Отправить в архив': f'sendarchive_{i.title}',
                    'Полностью удалить работу': f'delete_{i.title}',
                }, sizes=(2,1,1)
            ), parse_mode='HTML'
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
    salary = State()
    name = State()


################################################ Получение id работы ################################################

@admin_router.callback_query(StateFilter(None), F.data.startswith('appoint_'))
async def add_work_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    title_id = callback.data.split('_')[-1]
    await state.set_state(ChoiseWorker.work_id)
    await state.update_data(work_id=title_id)
    await state.set_state(ChoiseWorker.task)
    await callback.answer('Введите задачу:')
    await callback.message.answer('Введите задачу:', reply_markup=reply.admin_nav)


################################################ Выбор задачи ################################################

@admin_router.message(ChoiseWorker.task, F.text)
async def add_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await state.set_state(ChoiseWorker.salary)
    await message.answer('Введите оклад\nЕсли работает за Спасибо, то напишите: "-"')

################################################ Ввод оклада ################################################

@admin_router.message(ChoiseWorker.salary, F.text)
async def add_salary(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(salary=message.text)
    await state.set_state(ChoiseWorker.name)
    await message.answer('Выберите сотрудника:', reply_markup=await choise_worker_btns(session))


################################################ Распределение работы ################################################

@admin_router.callback_query(ChoiseWorker.name, F.data)
async def add_name(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    await state.update_data(name=callback.data)
    data = await state.get_data()
    title_id = data['work_id']
    task_and_name = str(f"🫡  {data['task']} - {data['name']}")

    before_added = await orm_get_one_work(session, title_id)
    
    try:
        for i in await orm_get_users(session):      # Назначаем работу на сотрудника
            print("Имя в бд", i.name, "\nИмя в дате", data['name'])
            if i.name in data['name']:
                await orm_update_user_work(
                    session,
                    user_id=i.user_id,
                    current_work=title_id,
                    salary=data['salary'],
                    check_work=False
                )
        if before_added.worker_name == None:
            await orm_add_work_worker_name(session, title_id, task_and_name)
        else:
            await orm_update_work_worker_name(session, title_id, task_and_name)
        await callback.answer('Выполнено')
        await callback.message.answer('Работа назначена', reply_markup=reply.admin_kb)
        await state.clear()

    except Exception as e:
        await callback.answer(f'Ошибка: {e}')
        await callback.message.answer(f'Ошибка: {e}', reply_markup=reply.admin_kb)
        await state.clear()


    i = await orm_get_one_work(session, title_id)
    if i.ready_status == False:            # Если работа не опубликована, то:
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
        await callback.message.answer_photo(photo=i.image, caption=
                f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}',
                reply_markup=get_callback_btns(btns={
                        'Назначить': f'appoint_{i.title}',
                        'Изменить': f'change_{i.title}',
                        'Полностью удалить работу': f'delete_{i.title}',
                    }), parse_mode='HTML'
                )
        task = data['task']
        for users in await orm_get_users(session):
            if users.username in i.worker_name:
                task = i.worker_name.split("-")[0]
                await bot.send_message(chat_id=users.user_id, text='Вам назначена новая работа')
                await bot.send_photo(chat_id=users.user_id, photo=i.image, caption=
                        f'💰 - {i.title}\n🗓 - {i.deadline}\n📂 - {i.file_name}\n👉 - <a href="{i.file}"> Work Files </a>\n{task}',
                        parse_mode='HTML')
                

@admin_router.message(ChoiseWorker.name)
async def add_name2(message: types.Message):
    await message.answer("Необходимо выбрать имя на клавиатуре")