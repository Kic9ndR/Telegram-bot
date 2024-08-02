from datetime import datetime
from tkinter import PhotoImage
from turtle import title
from aiogram import F, Bot, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession

# from common.schemas import SimpleCalendarCallback
# from kbrd.calendar import SimpleCalendar
from database import orm_query # import orm_add_task, orm_appoint_worker, orm_get_last_work, orm_get_user_info, orm_get_work
from filters.chat_types import ChatFilter, IsAdmin
from kbrd import reply
from kbrd.inline import choise_worker_btns, get_callback_btns
from kbrd.reply import admin_kb, del_kb
from googlesheets.table import GoogleTable


#----------------------------------------------------------------------------------
admin_router = Router()
admin_router.message.filter(ChatFilter(["private"]), IsAdmin())


class CreateTask(StatesGroup):
    title = State()
    deadline = State()
    file_name = State()
    file = State()
    image = State()

    title_for_change = ''

    texts = {
        'CreateTask:title': 'Введите улицу повторно: ',
        'CreateTask:deadline': 'Введите срок выполнения повторно: ',
        'CreateTask:file_name': 'Введите названия файла повторно: ',
        'CreateTask:file': 'Загрузите файл повторно: ', 
        'CreateTask:image': 'Загрузите изображение повторно: ',
    }

#---------------------------------------------------------------------------------- 
@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=admin_kb)


#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список сотрудников")
async def project_klnd(message: types.Message, session: AsyncSession):
    google_table = GoogleTable()
    second_column = google_table.get_second_column()
    await message.answer('\n'.join(second_column))

#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Таблица работ")
async def task_distrib(message: types.Message):
    await message.answer(
        "Ссылка на таблицу: \nhttps://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g", 
        reply_markup=admin_kb
                         )
#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список работ")
async def project_klnd(message: types.Message, session: AsyncSession):
    await message.answer('Вот список:')
    for title in await orm_query.orm_get_all_works(session):
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: {title.file}',
            reply_markup=get_callback_btns(btns={
                        'Удалить': f'delete_{title.title}',
                        'Изменить': f'change_{title.title}'
                        }),
                )


@admin_router.message(F.text == "В процессе создания")
async def process_of_creation(message: types.Message, session: AsyncSession):
    await message.answer('Работы в процессе создания:')
    for title in await orm_query.orm_get_all_unready(session):
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: {title.file}\nСписок исполнителей\n{title.worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'change_{title.title}',
                'Отправить в работу': f'send_{title.title}',
            })
        )


@admin_router.callback_query(StateFilter(None), F.data.startswith('send_'))
async def send_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
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
    

    for user_id in await orm_query.orm_get_user_info(session):
        if user_id.username in work.worker_name:
            await orm_query.orm_add_current_work(session, user_id.user_id, title_id) 
            await bot.send_message(chat_id=user_id.user_id, text='Вам назначена новая работа')
            await bot.send_photo(chat_id=user_id.user_id, photo=work.image, caption=
                                f'💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 {work.file}')


    await bot.send_photo(chat_id='-1002192469164', photo=work.image, caption=
                    f"💰 - {work.title}\n🗓 - {work.deadline}\n📂 - {work.file_name}\n👉 {work.file}\n{work.worker_name}")


    await callback.answer()
    await callback.message.answer('Работа отправлена!')


@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_work(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    title_id = callback.data.split('_')[-1]
    title_for_change = await orm_query.orm_get_work(session, title_id)

    CreateTask.title_for_change = title_for_change
    await callback.answer()
    await callback.message.answer(
        'Введите название работы\nОтправьте "." если не хотите вносить изменения', reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CreateTask.title)


################################# Код ниже для машины состояний (FSM) #################################

@admin_router.message(StateFilter(None), F.text == "Создание задачи")
async def create_task(message: types.Message, state: FSMContext):
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
    if message.text == '.':
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
    if message.text == '.':
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
    if message.text == '.':
        await state.update_data(file_name = CreateTask.title_for_change.file_name)
    else:
        await state.update_data(file_name=message.text)
    await message.answer("Загрузите файл: ")
    await state.set_state(CreateTask.file)

@admin_router.message(CreateTask.file_name)
async def set_file_name2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо ввести название файла")


################################################ Ввод файла ################################################
@admin_router.message(CreateTask.file, or_f(F.text, F.text == '.'))
async def set_file(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(file = CreateTask.title_for_change.file)
    else:
        await state.update_data(file=message.text)
    await message.answer("Загрузите фото: ")
    await state.set_state(CreateTask.image)


@admin_router.message(CreateTask.file)
async def set_file2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо загрузить файл ")


################################################ Загрузка фото ################################################
@admin_router.message(CreateTask.image, or_f(F.photo, F.text == '.'))
async def add_image(callback: CallbackQuery, message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == '.':
        await state.update_data(image=CreateTask.title_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    title_id = data['title']
    try:
        if CreateTask.title_for_change:
            await orm_query.orm_change(session, CreateTask.title_for_change.title, data)
        else:
            await orm_query.orm_add_task(session, data)
        await message.answer("Задача добавлена!", reply_markup=admin_kb)
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру, он опять денег хочет",
            reply_markup=admin_kb,
        )

    i = await orm_query.orm_get_work(session, title_id)
    await callback.message.answer_photo(photo=i.image, caption=
        f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: {i.file}\nСписок исполнителей\n{i.worker_name}',
        reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'change_{title.title}',
                'Отправить в работу': f'send_{title.title}',
            })
        )

    await state.clear()
    CreateTask.title_for_change = None


@admin_router.message(CreateTask.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо загрузить фото")



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

    i = await orm_query.orm_get_work(session, title_id)
    await callback.message.answer_photo(photo=i.image, caption=
        f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: {i.file}\nСписок исполнителей\n{i.worker_name}',
        reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'change_{title.title}',
                'Отправить в работу': f'send_{title.title}',
            })
        )


@admin_router.message(ChoiseWorker.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Необходимо выбрать имя на клавиатуре")