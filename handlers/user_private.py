import asyncio
from datetime import datetime
from aiogram import types, Router, F, Bot
from aiogram.filters import Command, StateFilter, or_f
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.markdown import hbold
from filters.chat_types import ChatFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from database.orm_query import orm_add_user, orm_get_user_info
from common.schemas import SimpleCalendarCallback
from handlers import admin_private
from handlers.user_group import get_admins
from kbrd import reply
from kbrd.calendar import SimpleCalendar


user_router = Router()
user_router.message.filter(ChatFilter(["private"]))


@user_router.message(
    or_f(
        Command("start"), (F.text.lower() == "в начало ↩️"), (F.text.lower() == "старт")
    )
)
async def start_cmd(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await message.answer("Что интересует?", reply_markup=reply.start_kb)
    user = message.from_user

    if user.id not in await orm_get_user_info(session):
        await orm_add_user(
            session, 
            user_id = user.id,
            first_name = user.first_name,
            last_name = user.last_name,
            username = user.username,
            current_work = None,
            )


# ------------------------------------------------------------------------------------------------------
@user_router.message(
    or_f(Command("current_work"), (F.text.lower() == "текущая работа ⏱"))
)
async def current_work_cmd(message: types.Message):
    await message.answer("Твоя текущая работа", reply_markup=reply.current_work_kb)


# #----------------------------------------------------------------------------------------------------
class SendWork(StatesGroup):
    work = State()

@user_router.message(
    or_f(Command("send work"), (F.text.lower() == "отправить работу 📧"))
)
async def send_work_cmd(message: types.Message, state: FSMContext):
    await message.answer("Вставь ссылку на работу", reply_markup=reply.send_work_kb)
    await state.set_state(SendWork.work)

@user_router.message(SendWork.work, F.text)
async def send_work(message: types.Message, bot:Bot, state: FSMContext):
    await state.update_data(work=message.text)
    await bot.send_message(chat_id='-1002192469164', text=message.text)
    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    await state.clear()

# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("archive"), (F.text.lower() == "архив работ 🗄️")))
async def archive_cmd(message: types.Message):
    await message.answer("Прошлые работы:", reply_markup=reply.archive_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("about"), (F.text.lower() == "о боте 🤖")))
async def about_cmd(message: types.Message):
    await message.answer(
        "Этот проект представляет собой Telegram-бота, который позволяет пользователям настраивать свой рабочий график и отслеживать текущую рабочую задачу. Пользователи могут отправлять выполненную работу через бота.", 
        reply_markup=reply.start_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("timetable"), (F.text.lower() == "график работы 🗓")))
async def nav_cal_handler(message: Message):
    await message.answer(text="Календарь:", reply_markup=reply.timetable_kb)
    await message.answer(
        "Выберите дату: ",
        reply_markup=await SimpleCalendar(locale="Russian_Russia").start_calendar(),
    )


# ------------------------------------------------------------------------------------------------------
@user_router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(
    callback_query: CallbackQuery, callback_data: CallbackData
):
    calendar = SimpleCalendar(locale="Russian_Russia", show_alerts=True)
    calendar.set_dates_range(datetime(2024, 1, 1), datetime(2050, 12, 31))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Выбрана дата: {date.strftime("%d/%m/%Y")}',
            reply_markup=reply.timetable_kb,
        )
