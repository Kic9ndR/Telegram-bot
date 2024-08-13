import os
from aiogram import types, Router, F, Bot
from aiogram.filters import Command, or_f
from aiogram.types import Message
from filters.chat_types import ChatFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMedia, ContentType as CT


from database.orm_query import *
from kbrd import reply
from kbrd.inline import get_callback_btns


user_router = Router()
user_router.message.filter(ChatFilter(["private"]))

user_chat = os.getenv('USER_CHAT')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')            # Тестовые значение
message_treads_for_check = os.getenv('MESSAGE_THREAD_FOR_CHECK')

user_comment = []

class AddName(StatesGroup):
    name = State()


@user_router.message(
    or_f(
        Command("start"), (F.text.lower() == "в начало ↩️"), (F.text.lower() == "старт")
    )
)
async def start_cmd(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user = await orm_get_one_user(session, message.from_user.id)

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
        name = user_name,
        username = user.username,
        )
    
    await message.answer(f'Добавил Вас {user_name}, спасибо 😃', reply_markup=reply.start_kb)
    await state.clear()


#------------------------------------------------------------------------------------------------------
@user_router.message(
    or_f(Command("current_work"), (F.text.lower() == "текущая работа ⏱"))
)
async def current_work_cmd(message: types.Message, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    user = await orm_get_one_user(session, user_id)

    work = await orm_get_one_work(session, user.current_work)
    if work is None:
        await message.answer("У тебя нет текущей работы")
        return
    else:
        task = work.worker_name.split("-")[0]
    try:
        if user.current_work == None:
            await message.answer("У тебя нет текущей работы")
        else:
            await message.answer_photo(photo=work.image, caption=
                        f'<b>Работа</b> - {work.title}\n<b>Срок выполнения:</b> {work.deadline}\n<b>Ссылка на файл:</b> <a href="{work.file}"> Work Files </a>\n<b>Оклад за работу:</b> {user.salary}\n<b>Твоя задача:</b> {task}',
                        parse_mode='HTML')
    except Exception as e:
        await message.answer(f'Ошибка:\n{e}\n\nНапишите програмёру @Kic9ndr', reply_markup=reply.start_kb)


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
            ), disable_web_page_preview=True
        )
    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    await state.clear()
    user = await orm_get_one_user(session, message.from_user.id)    # Получаю юзера
    await orm_update_user_status(session, user.user_id, True)     # Изменение статуса проверки на "Проверка"


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("archive"), (F.text.lower() == "архивные работы 🗄️")))
async def archive_cmd(message: types.Message, session: AsyncSession):
    i = await orm_get_archive_works(session)
    await message.answer_photo(photo=i.image, caption=
            f'{i.title}\nСрок выполнения: {i.deadline}\nСсылка на файл: <a href="{i.file}"> Work Files </a>\nСписок исполнителей\n{i.worker_name}'
    )


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("about"), (F.text.lower() == "О боте 🤖")))
async def about_cmd(message: types.Message):
    with open('user_about.md', 'r', encoding='utf-8') as user_list:
        user_text = user_list.read()
    await message.answer(text=(user_text), reply_markup=reply.start_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("timetable"), (F.text.lower() == "график работы 🗓")))
async def nav_cal_handler(message: Message):
    await message.answer(text="Таблица с графиком:\nhttps://docs.google.com/spreadsheets/d/1VTlLg0JOvnw-owN4xpzwl7Vl_5vtooEukcCH3phl6Nw/edit?gid=1574826567#gid=1574826567", reply_markup=reply.start_kb)




# ------------------------------------------------------------------------------------------------------
class ReportWork(StatesGroup):
    comment = State()
    photo = State()


@user_router.message(F.text == 'Отчет о работе 💬')
async def report_work(message: types.Message, state: FSMContext):
    await message.answer('Оставь комментарий к работе', reply_markup=reply.send_work_kb)
    await state.set_state(ReportWork.comment)

@user_router.message(ReportWork.comment, F.text)
async def report_work_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Приложи фото/видео к работе")
    await state.set_state(ReportWork.photo)
    # data = await state.get_data()
    # user_comment.append(data['comment'])
    # await state.clear()

#       |
#       |
#       |
#      \ /
#       '

# @user_router.message(F.content_type.in_([CT.PHOTO]))

@user_router.message(ReportWork.photo, F.photo)
async def report_work_photo(message: types.Message, album: list[Message], bot: Bot, session: AsyncSession, state: FSMContext):
    user = await orm_get_one_user(session, message.from_user.id)
    data = await state.get_data()
    user_comment.append(data['comment'])

    comment = (''.join(user_comment))
    await bot.send_message(chat_id=int(admin_chat), text=
                    f'Работа от {user.name} @{user.username}\nКомментарий к работе:\n{comment}', 
                    message_thread_id=int(message_treads_for_check)
    )

    media_group = []
    for msg in album:
        if msg.photo:
            file_id = msg.photo[-1].file_id
            media_group.append(InputMediaPhoto(media=file_id))
        else:
            obj_dict = msg.dict()
            file_id = obj_dict[msg.content_type]['file_id']
            media_group.append(InputMedia(media=file_id))



    await bot.send_media_group(chat_id=int(admin_chat), media=media_group, message_thread_id=int(message_treads_for_check))
    await message.answer('Работа отправлена', reply_markup=reply.start_kb)
    await state.clear()


# @user_router.message(ReportWork.photo, F.photo)
# async def report_work_photo2(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
#     user = await orm_get_one_user(session, message.from_user.id)
#     data = await state.get_data()
#     user_comment.append(data['comment'])

#     comment = (''.join(user_comment))
#     await bot.send_message(chat_id=int(admin_chat), text=
#                     f'Работа от {user.name} @{user.username}\nКомментарий к работе:\n{comment}', 
#                     message_thread_id=int(message_treads_for_check)
#     )

#     await bot.send_photo(chat_id=int(admin_chat), photo=message.photo[-1].file_id, message_thread_id=int(message_treads_for_check))
#     await message.answer('Работа отправлена', reply_markup=reply.start_kb)
#     await state.clear()


@user_router.message(F.video)
async def send_video(message: types.Message, bot: Bot, session: AsyncSession):
    user = await orm_get_one_user(session, message.from_user.id)

    comment = (''.join(user_comment))
    await bot.send_message(chat_id=int(admin_chat), text=
                    f'Работа от {user.name} @{user.username}\nКомментарий к работе:\n{comment}', 
                    message_thread_id=int(message_treads_for_check)
    )
    await bot.send_video(chat_id=int(admin_chat), video=message.video.file_id, message_thread_id=int(message_treads_for_check))
    await message.answer('Работа отправлена', reply_markup=reply.start_kb)









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