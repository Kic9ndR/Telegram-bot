from datetime import datetime
from aiogram import types, Router, F, Bot
from aiogram.filters import Command, StateFilter, or_f
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.markdown import hbold
from filters.chat_types import ChatFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from database.orm_query import orm_add_chech_work, orm_add_user, orm_get_admin_info, orm_get_ready_work, orm_get_user, orm_get_user_info
from common.schemas import SimpleCalendarCallback
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
async def current_work_cmd(message: types.Message, session: AsyncSession):
    user = await orm_get_user(session, message.from_user.id)
    work = await orm_get_ready_work(session, user.current_work)
    task = work.worker_name.split("-")[0]

    await message.answer_photo(photo=work.image, caption=
                f'Работа - {work.title}\nСрок выполнения: {work.deadline}\nСсылка на файл: {work.file}\nТвоя задача: {task}')


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
    await bot.send_message(chat_id='-1002165307959', text=
                           f'Работа на проверку от @{message.from_user.username}\nКоментарий к работе: {data["comment"]}\n\nСсылка на работу:\n{message.text}',
                           message_thread_id='2')
    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    await state.clear()
    user = await orm_get_user(session, message.from_user.id)
    work = await orm_get_ready_work(session, user.current_work)

    await orm_add_chech_work(
        session, 
        user_id = user.user_id,
        first_name = user.first_name,
        last_name = user.last_name,
        username = user.username,
        title = work.title,
        )


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("archive"), (F.text.lower() == "архив работ 🗄️")))
async def archive_cmd(message: types.Message):
    await message.answer("Прошлые работы:", reply_markup=reply.archive_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("about"), (F.text.lower() == "о боте 🤖")))
async def about_cmd(message: types.Message, session: AsyncSession, bot: Bot):
    with open('user_about.md', 'r', encoding='utf-8') as user_list, open('admin_about.md', 'r', encoding='utf-8') as admin_list:
        user_text = user_list.read()
        admin_text = admin_list.read()
    admin = await orm_get_admin_info(session)
    for i in admin:
        if message.from_user.id == i.user_id:
            await message.answer(text=(admin_text), reply_markup=reply.start_kb)
        else:
            await message.answer(text=(user_text), reply_markup=reply.start_kb)


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
