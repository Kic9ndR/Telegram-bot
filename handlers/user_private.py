import os
from aiogram import types, Router, F, Bot
from aiogram.filters import Command, or_f
from aiogram.types import Message
from filters.chat_types import ChatFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from database.orm_query import *
from kbrd import reply
from kbrd.inline import get_callback_btns


user_router = Router()
user_router.message.filter(ChatFilter(["private"]))

user_chat = os.getenv('USER_CHAT')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')            # Тестовые значение


class AddName(StatesGroup):
    name = State()



@user_router.message(
    or_f(
        Command("start"), (F.text.lower() == "в начало ↩️"), (F.text.lower() == "старт")
    )
)
async def start_cmd(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user = await orm_get_user(session, message.from_user.id)

    if user is None:
        await state.set_state(AddName.name)
        await message.answer('Пожалуйста, введите имя и фамилию', reply_markup=reply.start_kb)
    else:
        await message.answer("Что интересует?", reply_markup=reply.start_kb)


@user_router.message(AddName.name, F.text)
async def add_name(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    user = message.from_user
    user_name = data['name']
    await orm_add_user(
        session, 
        user_id = user.id,
        first_name = user_name,
        username = user.username,
        current_work = None,
        )
    
    await message.answer(f'Добавил Вас {user_name}, спасибо 😃', reply_markup=reply.start_kb)
    await state.clear()


#------------------------------------------------------------------------------------------------------
@user_router.message(
    or_f(Command("current_work"), (F.text.lower() == "текущая работа ⏱"))
)
async def current_work_cmd(message: types.Message, session: AsyncSession, bot: Bot):
    user = await orm_get_user(session, message.from_user.id)
    try:
        if user.current_work == None:
            await message.answer("У тебя нет текущей работы")
        else:
            work = await orm_get_ready_work(session, user.current_work) 
            task = work.worker_name.split("-")[0]
            await message.answer_photo(photo=work.image, caption=
                        f'Работа - {work.title}\nСрок выполнения: {work.deadline}\nСсылка на файл: {work.file}\nТвоя задача: {task}')
    except Exception as e:
        await message.answer(f'Ошибка:\n{e}', reply_markup=reply.start_kb)

# #----------------------------------------------------------------------------------------------------
class SendWork(StatesGroup):
    comment = State()
    work = State()

@user_router.message(
    or_f(Command("send work"), (F.text.lower() == "отправить работу 📧"))
)
async def send_work_cmd(message: types.Message, state: FSMContext):
    await message.answer("Оставь комментарий к работе", reply_markup=reply.send_work_kb)
    await state.set_state(SendWork.comment)


@user_router.message(SendWork.comment, F.text)
async def send_work_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Вставь ссылку на работу")
    await state.set_state(SendWork.work)


@user_router.message(SendWork.work, F.text)
async def send_work(message: types.Message, bot:Bot, state: FSMContext, session: AsyncSession):
    await state.update_data(work=message.text)
    data = await state.get_data()
    await bot.send_message(chat_id=int(admin_chat), text=
                f'Работа на проверку от @{message.from_user.username}\nКоментарий к работе: {data["comment"]}\n\nСсылка на работу:\n{message.text}',
                message_thread_id=int(admin_message_thread), reply_markup=get_callback_btns(btns={
                    'Принять работу': f"accept_{message.from_user.id}",
                    'Отправить правки': f"edits_{message.from_user.id}"
                }, sizes={1,1}
            )
        )
    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    await state.clear()
    user = await orm_get_user(session, message.from_user.id)
    work = await orm_get_ready_work(session, user.current_work)
    check_work = await orm_get_check_work(session, user.user_id)

    if user.user_id == check_work.user_id:
        await orm_update_check_work(session, user.current_work, user.current_work)
    else:
        await orm_add_chech_work(            # Добавляем работу в базу данных "work check"
            session, 
            user_id = user.user_id,
            first_name = user.first_name,
            username = user.username,
            title = work.title,
            )


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("archive"), (F.text.lower() == "архив работ 🗄️")))
async def archive_cmd(message: types.Message):
    await message.answer("Прошлые работы:", reply_markup=reply.archive_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("about"), (F.text.lower() == "о боте 🤖")))
async def about_cmd(message: types.Message):
    with open('user_about.md', 'r', encoding='utf-8') as user_list:
        user_text = user_list.read()

    await message.answer(text=(user_text), reply_markup=reply.start_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("timetable"), (F.text.lower() == "график работы 🗓")))
async def nav_cal_handler(message: Message):
    await message.answer(text="Таблица с графиком:\nhttps://docs.google.com/spreadsheets/d/1VTlLg0JOvnw-owN4xpzwl7Vl_5vtooEukcCH3phl6Nw/edit?gid=1574826567#gid=1574826567", reply_markup=reply.start_kb)










"""
========================================== Вызов календаря ==========================================
"""


#     await message.answer(
#         "Выберите дату: ",
#         reply_markup=await SimpleCalendar(locale="Russian_Russia").start_calendar(),
#     )


# @user_router.callback_query(SimpleCalendarCallback.filter())
# async def process_simple_calendar(
#     callback_query: CallbackQuery, callback_data: CallbackData
# ):
#     calendar = SimpleCalendar(locale="Russian_Russia", show_alerts=True)
#     calendar.set_dates_range(datetime(2024, 1, 1), datetime(2050, 12, 31))
#     selected, date = await calendar.process_selection(callback_query, callback_data)
#     if selected:
#         await callback_query.message.answer(
#             f'Выбрана дата: {date.strftime("%d/%m/%Y")}',
#             reply_markup=reply.timetable_kb,
#         )