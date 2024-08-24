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
from googlesheets.table import GoogleTable
from kbrd import reply
from kbrd.inline import choice_work_btns, get_callback_btns


user_router = Router()
user_router.message.filter(ChatFilter(["private"]))

user_chat = os.getenv('USER_CHAT')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')            # Тестовые значение
message_treads_for_check = os.getenv('MESSAGE_THREAD_FOR_CHECK')

user_comment = []

class AddName(StatesGroup):
    name = State()
    payment_details = State()
    work_programs = State()
    residence_city = State()

    programs = []
    mes_id = None


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
        await message.answer('Пожалуйста, введите имя и фамилию', reply_markup=reply.del_kb)
    elif (user.payment_details) is None:
        await state.set_state(AddName.payment_details)
        await message.answer('Введите номер телефона и банк для перевода:', reply_markup=reply.del_kb)
    else:
        await message.answer("Что интересует?", reply_markup=reply.start_kb)



@user_router.message(AddName.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите номер телефона и банк для перевода:', reply_markup=reply.del_kb)
    await state.set_state(AddName.payment_details)


@user_router.message(AddName.payment_details, F.text)
async def add_payment(message: types.Message, state: FSMContext):
    await state.update_data(payment_details=message.text)
    await message.answer('Выбери программы в которых работаешь:', reply_markup=get_callback_btns(
        btns={
            'Maya': f'Maya',
            '3DMax': f'3DMax',
            'Blender': f'Blender',
            '❌ Отменить': f'Cancel',
            'Продолжить ➡️': f'Continue',
        }, sizes=(2,1,2))
    )


########################################################################################################################
"""
Выбор программы для работы
"""
@user_router.callback_query(F.data.startswith('Maya'))
async def maya_prog(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer('Добавил в список "Maya"')
    title = callback.data
    print(title)
    AddName.programs.append(title)


@user_router.callback_query(F.data.startswith('3DMax'))
async def three_d_max_prog(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer('Добавил в список "3DMax"')
    title = callback.data
    print(title)
    AddName.programs.append(title)


@user_router.callback_query(F.data.startswith('Blender'))
async def blender_prog(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer('Добавил в список "Blender"')
    title = callback.data
    print(title)
    AddName.programs.append(title)

@user_router.callback_query(F.data.startswith('Cancel'))
async def cancel_prog(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer('Отменил выбор')
    current_state = await state.get_state()

    AddName.programs = []
    previous = None
    for step in AddName.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await callback.message.answer(f"Хорошо, введите снова\nВведите программы повторно")
            return
        previous = step


########################################################################################################################

@user_router.callback_query(F.data.startswith('Continue'))
async def add_programs(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(work_programs=AddName.programs)
    await callback.answer('Добавил программ(у/ы)')
    await callback.message.answer('Напиши город проживания')
    await state.set_state(AddName.residence_city)


@user_router.message(AddName.residence_city, F.text)
async def add_city(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await state.update_data(residence_city=message.text)
    data = await state.get_data()
    user = message.from_user
    programs = ''
    google_table = GoogleTable()                        # Создается лист в google sheets

    for i in (AddName.programs):
        print(i)
        programs += f"{i}, "

    await bot.send_chat_action(chat_id = user.id, action="typing")
    try:
        orm_user = await orm_get_one_user(session, user.id)
        if orm_user is None:
            user_name = data['name']
            await orm_add_user(
                session, 
                user_id = user.id,
                name = user_name,
                username = user.username,
                payment_details = data['payment_details'],
                work_programs = programs,
                residence_city = data['residence_city'],
                )
            
            google_table.create_sheet(user_name)
            google_table.add_name(user_name, user.username)
            google_table.add_user_info(user_name, data['payment_details'], programs, data['residence_city'])
        else:
            user_name = orm_user.name
            await orm_add_user_data(
                session, 
                user_id = user.id,
                payment_details = data['payment_details'],
                work_programs = programs,
                residence_city = data['residence_city'],
                )
            google_table.add_user_info(user_name, data['payment_details'], programs, data['residence_city'])
    except Exception as e:
        await message.answer(f'Ошибка: {e}\nОбратитесь к @Kic9ndr')
    
    await state.clear()

    AddName.programs = []
    await message.answer(f'Добавил твои данные, {user_name}, спасибо 😃', reply_markup=reply.start_kb)


#####################################################################################################################################################
@user_router.message(
    or_f(Command("current_work"), (F.text.lower() == "текущая работа ⏱"))
)
async def current_work_cmd(message: types.Message, session: AsyncSession):
    """
    Отправка текущей работы сотруднику
    """
    user_id = message.from_user.id
    user_work = await orm_get_user_work(session, user_id)

    try:
        if user_work is None:
            await message.answer("У тебя нет текущей работы")
            return
        else:
            for all_works in await orm_get_user_works(session):
                if all_works.user_id == user_id:
                    work = await orm_get_one_work(session, all_works.current_work)
                    await message.answer_photo(
                        photo=work.image, 
                        caption=
                        f'<b>Работа</b> - {work.title}\n<b>Срок выполнения:</b> {work.deadline}\n<b>Ссылка на файл:</b> <a href="{work.file}"> Work Files </a>\n<b>Оклад за работу:</b> {all_works.salary}\n<b>Твоя задача:</b> {all_works.task}',
                        parse_mode='HTML'
                    )
    except Exception as e:
        await message.answer(f'Ошибка вывода работы сотрудников:\n{e}\n\nНапишите @Kic9ndr', reply_markup=reply.start_kb)


#####################################################################################################################################################
class SendWork(StatesGroup):
    """
    FSM для отправки работы на проверку
    """
    choice_work = State()
    comment = State()
    work = State()

    work_id = ''


@user_router.message(
    or_f(Command("send work"), (F.text.lower() == "отправить работу 📧"))
)
async def work_btns(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Вывод клавиатуры для выбора работы
    """
    await message.answer("Выбери какую работу из списка отправить на проверку:", reply_markup = await choice_work_btns(session, user_id=message.from_user.id))
    await state.set_state(SendWork.choice_work)


@user_router.callback_query(SendWork.choice_work, F.data)
async def send_work_cmd(callback: types.CallbackQuery, state: FSMContext):
    """
    Выбор работы и запись данных с нее
    """
    await callback.answer()
    title = callback.data.split("_")[0]
    work_id = callback.data.split("_")[-1]
    SendWork.work_id = work_id

    await state.update_data(choice_work=title)
    await callback.message.answer("Оставь комментарий к работе", reply_markup=reply.send_work_kb)
    await state.set_state(SendWork.comment)


@user_router.message(SendWork.comment, F.text)
async def send_work_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Вставь ссылку на работу")
    await state.set_state(SendWork.work)


@user_router.message(SendWork.work, F.text)
async def send_work(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    await state.update_data(work=message.text)
    data = await state.get_data()
    send_work = await bot.send_message(chat_id=int(admin_chat), text=
                f'Работа на проверку от @{message.from_user.username}\nКомментарий к работе: {data["comment"]}\n\nСсылка на работу:\n{message.text}',
                message_thread_id=int(admin_message_thread), reply_markup=get_callback_btns(btns={
                    'Принять работу': f"accept_{message.from_user.id}",
                    'Отправить правки': f"edits_{message.from_user.id}"
                }, sizes={1,1}
            ), disable_web_page_preview=True
        )
    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    user = await orm_get_one_user(session, message.from_user.id)    # Получаю юзера
    work_id = SendWork.work_id
    await orm_add_id_send_message(
            session,
            id=send_work.message_id,
            title=data['choice_work'],
            user_id=message.from_user.id,
            work_link=message.text,
            work_id=work_id
        )
    
    await state.clear()
    await orm_update_user_status(session, user.user_id, True)     # Изменение статуса проверки на "Проверка"


#-------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("archive"), (F.text.lower() == "архивные работы 🗄️")))
async def archive_cmd(message: types.Message, session: AsyncSession, bot: Bot):
    user = await orm_get_one_user(session, message.from_user.id)
    google_table = GoogleTable()
    link = google_table.get_link_worker(user.name)

    await bot.send_chat_action(chat_id = user.user_id, action="typing")
    await message.answer('Архивные работы:')
    for archive_work in await orm_get_archive_works(session):
        if user.name in archive_work.worker_name:
            await message.answer_photo(
                photo=archive_work.image, 
                caption=        # Отправка архивной работы и ссылка на гугл таблицу
                f'<b>Название работы:</b> {archive_work.title}\n<b>Срок выполнения:</b> {archive_work.deadline}\n<b>Ссылка на файл:</b> <a href="{archive_work.file}"> Work Files </a>\n\n<i>Для получения информации о оплате и стоимости задачи:</i>\n<a href="{link}">Ссылка на GoogleTable</a>'
            )
    else:
        await message.answer('Архивных работы кончились :( ')


#-------------------------------------------------------------------------------------------------------
@user_router.message(F.text.lower() == "хочу работу 🤑")
async def want_to_work(message: types.Message, bot: Bot, session: AsyncSession):
    user = await orm_get_one_user(session, message.from_user.id)
    admin_list = [5825144544, 5624308044]
    for i in admin_list:
        await bot.send_sticker(chat_id=i, sticker='CAACAgIAAxkBAAEMsoVmydWYfGwFoazZb8ffbF3D29zF-AACIwADX93LNgABGL7i461AdjUE')
        await bot.send_message(chat_id=i, text=f'{user.name} @{user.username} хочет поработать, нужно больше золота нужно построить зиккурат ')
    await message.answer(text='Вас понял 🫡\nОтправил пожелание капитану', reply_markup=reply.start_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("timetable"), (F.text.lower() == "график работы 🗓")))
async def nav_cal_handler(message: Message):
    await message.answer(text=
        "Таблица с графиком:\nhttps://docs.google.com/spreadsheets/d/1VTlLg0JOvnw-owN4xpzwl7Vl_5vtooEukcCH3phl6Nw/edit?gid=1574826567#gid=1574826567", 
        reply_markup=reply.start_kb
    )


########################################################################################################

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


# Информация о боте и как им пользоваться

# @user_router.message(or_f(Command("about"), (F.text.lower() == "О боте 🤖")))
# async def about_cmd(message: types.Message):
#     with open('user_about.md', 'r', encoding='utf-8') as user_list:
#         user_text = user_list.read()
#     await message.answer(text=(user_text), reply_markup=reply.start_kb)


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