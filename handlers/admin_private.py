from datetime import datetime
from turtle import title
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession

# from common.schemas import SimpleCalendarCallback
# from kbrd.calendar import SimpleCalendar
from database.orm_query import orm_add_task, orm_appoint_worker, orm_get_user_info, orm_get_work
from filters.chat_types import ChatFilter, IsAdmin
from kbrd import reply
from kbrd.inline import choise_worker_btns, get_callback_btns
from kbrd.reply import admin_kb, del_kb
from googlesheets.table import GoogleTable


#----------------------------------------------------------------------------------
admin_router = Router()
admin_router.message.filter(ChatFilter(["private"]), IsAdmin())

#---------------------------------------------------------------------------------- 
@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=admin_kb)


#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список сотрудников")
async def project_klnd(message: types.Message, session: AsyncSession):
    user_list = await orm_get_user_info(session)
    for i in user_list:
        await message.answer(f'{i.first_name} @{i.username}')
    # google_table = GoogleTable()
    # second_column = google_table.get_second_column()
    # await message.answer('\n'.join(second_column))

#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список работ")
async def project_klnd(message: types.Message, session: AsyncSession):
    await message.answer('Вот список:')
    for title in await orm_get_work(session):
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nСрок выполнения: {title.deadline}\nСсылка на файл: {title.file}',
            reply_markup=get_callback_btns(btns={
                        'Назначить': f'appoint_{title.title}',
                        'Изменить': f'change_{title.title}'
                        }),
                )


#----------------------------------------------------------------------------------
# @admin_router.callback_query(F.data.startswith('appoint_'))
# async def appoint_worker(callback: types.CallbackQuery, session: AsyncSession):
#     title_id = callback.data.split('_')[-1]
#     task = callback.message.answer('Введите задачу:')
#     if task is not None:
#         for worker in await orm_get_user_info(session):
#             w_kb = choise_worker_btns(btns={f'{worker.first_name} {worker.last_name}': f'{worker.username}'})
#         callback.message.answer('Выберите сотрудника:', reply_markup=w_kb)



#################################################################################################################

@admin_router.message(F.text == "Проверка работ")
async def project_klnd(message: types.Message):
    await message.answer("Работа на проверку: ")


#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Таблица работ")
async def task_distrib(message: types.Message):
    await message.answer(
        "Ссылка на таблицу: \nhttps://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g", 
        reply_markup=admin_kb
                         )

#----------------------------------------------------------------------------------
# @admin_router.message(F.text == "Проектный календарь")
# async def worker_list(message: types.Message):
#         await message.answer(
#         "Выберите дату: ",
#         reply_markup=await SimpleCalendar(locale='Russian_Russia').start_calendar()
#     )

# @admin_router.callback_query(SimpleCalendarCallback.filter())
# async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
#     calendar = SimpleCalendar(
#         locale='Russian_Russia', show_alerts=True
#     )
#     calendar.set_dates_range(datetime(2024, 1, 1), datetime(2050, 12, 31))
#     selected, date = await calendar.process_selection(callback_query, callback_data)
#     if selected:
#         await callback_query.message.answer(
#             f'Выбрана дата: {date.strftime("%d/%m/%Y")}',
#             reply_markup=reply.timetable_kb
#         )

################################# Код ниже для машины состояний (FSM) #################################

class CreateTask(StatesGroup):
    title = State()
    deadline = State()
    file_name = State()
    file = State()
    image = State()

    texts = {
        'CreateTask:title': 'Введите улицу повторно: ',
        'CreateTask:deadline': 'Введите срок выполнения повторно: ',
        'CreateTask:file_name': 'Введите названия файла повторно: ',
        'CreateTask:file': 'Загрузите файл повторно: ', 
        'CreateTask:image': 'Загрузите изображение повторно: ',
    }

################################################ Создание задачи ################################################
@admin_router.message(StateFilter(None), F.text == "Создание задачи")
async def create_task(message: types.Message, state: FSMContext):
    await message.answer("Введите название улицы (Нельзя изменить после  создания): ", 
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
@admin_router.message(CreateTask.title, F.text)
async def set_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите срок выполнения: ")
    await state.set_state(CreateTask.deadline)

@admin_router.message(CreateTask.title)
async def set_title2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать текст ")

################################################ Ввод дедлайна ################################################
@admin_router.message(CreateTask.deadline, F.text)
async def set_deadline(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer("Введите название файла: ")
    await state.set_state(CreateTask.file_name)

@admin_router.message(CreateTask.deadline)
async def set_deadline2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать число ")

################################################ Ввод названия файла ################################################
@admin_router.message(CreateTask.file_name, F.text)
async def set_file_name(message: types.Message, state: FSMContext):
    await state.update_data(file_name=message.text)
    await message.answer("Загрузите файл: ")
    await state.set_state(CreateTask.file)

@admin_router.message(CreateTask.file_name)
async def set_file_name2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо ввести название файла")

################################################ Ввод файла ################################################
@admin_router.message(CreateTask.file, F.text)
async def set_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.text)
    await message.answer("Загрузите фото: ")
    await state.set_state(CreateTask.image)


@admin_router.message(CreateTask.file)
async def set_file2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо загрузить файл ")


################################################ Загрузка фото ################################################
@admin_router.message(CreateTask.image, F.photo)
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        await orm_add_task(session, data)
        await message.answer("Задача добавлена!", reply_markup=admin_kb)
        await state.clear()
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру, он опять денег хочет",
            reply_markup=admin_kb,
        )
        await state.clear()

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


################################################ Выбор задачи ################################################

@admin_router.message(ChoiseWorker.task, F.text)
async def add_task(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(task=message.text)
    await state.set_state(ChoiseWorker.name)
    await message.answer('Выберите сотрудника:', reply_markup=await choise_worker_btns(session))


################################################ Распределение работы ################################################

@admin_router.callback_query(ChoiseWorker.name, F.data)
async def add_name(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.update_data(name=callback.data)
    data = await state.get_data()
    title_id = data['work_id']
    task_and_name = str(f"{data['task']} -- {data['name']}")
    try:
        await orm_appoint_worker(session, title_id, task_and_name)
        await callback.answer('Выполнено')
        await callback.message.answer('Работа назначена', reply_markup=reply.admin_kb)
        await state.clear()
    except Exception as e:
        await callback.answer(f'Ошибка: {e}')
        await callback.message.answer(f'Ошибка: {e}', reply_markup=reply.admin_kb)
        await state.clear()


@admin_router.message(ChoiseWorker.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Необходимо выбрать имя на клавиатуре")