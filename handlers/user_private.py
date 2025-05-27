import os
import random
import aiohttp
import validators
from aiogram import types, Router, F, Bot
from aiogram.filters import Command, or_f, StateFilter
from aiogram.types import Message, FSInputFile
from common.work_output import send_booklet_output, send_booklet_output2
from filters.chat_types import ChatFilter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


from database.orm_query import *
from googlesheets.table import GoogleTable
from kbrd import reply
from kbrd.inline import *


user_router = Router()
user_router.message.filter(ChatFilter(["private"]))

user_chat = os.getenv('USER_CHAT')
work_check = os.getenv('WORK_CHECK')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')            # Тестовые значение
message_treads_for_check = os.getenv('MESSAGE_THREAD_FOR_CHECK')

user_comment = []

async def send_file(message: types.Message):
    user_agreement = FSInputFile(path=os.path.join('user_agreement.docx'))
    await message.answer_document(document=(user_agreement), caption='<b>Пожалуйста, прочтите и примите <i>пользовательское соглашение</i></b>', reply_markup=await get_callback_btns(
            btns={
                'Принять пользовательское соглашение': 'file_accept',
                }
            )
        )


class AddName(StatesGroup):
    name = State()
    payment_details = State()
    work_programs = State()
    residence_city = State()
    drive = State()

    for_change = ''
    role = None
    change_prof = False
    programs = []
    mes_id = None

#_________________________________________________________________________________________
@user_router.message(StateFilter('*'), Command("отмена"))
@user_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=reply.start_kb)

#_________________________________________________________________________________________
@user_router.message(StateFilter(AddName), Command("назад"))
@user_router.message(StateFilter(AddName), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == AddName.name:
        await message.answer('Предыдущего шага нет, напишите "отмена"', reply_markup=reply.admin_nav)
        return

    previous = None
    for step in AddName.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу", reply_markup=reply.admin_nav)
            return
        previous = step

#_________________________________________________________________________________________
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

    elif user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)
    else:
        await message.answer("Что интересует?", reply_markup=reply.start_kb)

#_________________________________________________________________________________________
@user_router.message(AddName.name, or_f(F.text, F.text == '.'))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == '.' and AddName.change_prof is True:
        await state.update_data(name=AddName.for_change.name)
    else:
        await state.update_data(name=message.text)
    await message.answer('Введите номер телефона и банк для перевода:', reply_markup=reply.del_kb)
    await state.set_state(AddName.payment_details)

#_________________________________________________________________________________________
@user_router.message(AddName.payment_details, or_f(F.text, F.text == '.'))
async def add_payment(message: types.Message, state: FSMContext):
    if message.text == '.' and AddName.change_prof is True:
        await state.update_data(payment_details=AddName.for_change.payment_details)
    else:
        await state.update_data(payment_details=message.text)
    await message.answer('Выбери программы в которых работаешь:', reply_markup=await get_callback_btns(
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
async def maya_prog(callback: types.CallbackQuery):
    await callback.answer('Добавил в список "Maya"')
    title = callback.data
    AddName.programs.append(title)

#_________________________________________________________________________________________
@user_router.callback_query(F.data.startswith('3DMax'))
async def three_d_max_prog(callback: types.CallbackQuery):
    await callback.answer('Добавил в список "3DMax"')
    title = callback.data
    AddName.programs.append(title)

#_________________________________________________________________________________________
@user_router.callback_query(F.data.startswith('Blender'))
async def blender_prog(callback: types.CallbackQuery):
    await callback.answer('Добавил в список "Blender"')
    title = callback.data
    AddName.programs.append(title)

#_________________________________________________________________________________________
@user_router.callback_query(F.data.startswith('Cancel'))
async def cancel_prog(callback: types.CallbackQuery, state: FSMContext):
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
    if callback.message.text == '.' and AddName.change_prof is True:
        await state.update_data(work_programs=AddName.for_change.work_programs)
    else:
        await state.update_data(work_programs=AddName.programs)
    await callback.answer('Добавил программ(у/ы)')
    await callback.message.answer('Напиши город проживания')
    await state.set_state(AddName.residence_city)

#_________________________________________________________________________________________________
@user_router.message(AddName.residence_city, or_f(F.text, F.text == '.'))
async def add_city(message: types.Message, state: FSMContext):
    if message.text == '.' and AddName.change_prof is True:
        await state.update_data(residence_city=AddName.for_change.residence_city)
    else:
        await state.update_data(residence_city=message.text)
    await message.answer('Вставь ссылку на Яндекс Диск с работами', reply_markup=reply.del_kb)
    await state.set_state(AddName.drive)

#_________________________________________________________________________________________________
@user_router.message(AddName.drive, or_f(F.text, F.text == '.'))
async def add_drive(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == '.' and AddName.change_prof is True:
        await state.update_data(drive=AddName.for_change.drive)
    else:
        await state.update_data(drive=message.text)

    data = await state.get_data()
    user = message.from_user
    programs = ''
    payment_details = data['payment_details'].split('+')[-1]
    google_table = GoogleTable()
    orm_user = await orm_get_one_user(session, user.id)
    for i in (AddName.programs):
        programs += f"{i}, "

    await bot.send_chat_action(chat_id = user.id, action="typing")
    if AddName.role is not None:
        await orm_update_user_role(session, user.id, AddName.role)

    try:
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
                drive = data['drive'],
            )
            google_table.create_sheet(user_name)
            google_table.add_name(user_name, user.username)
            google_table.add_user_info(user_name, payment_details, programs, data['residence_city'], data['drive'])
            
        elif AddName.change_prof == True:             # Если профиль был обновлен, то:
            google_table.update_user_info(
                title = orm_user.name,
                username=user.username, 
                payment_details=data['payment_details'], 
                work_programs=programs, 
                residence_city=data['residence_city'], 
                drive=data['drive']
            )
            await orm_update_user_prof(
                session, 
                user_id = user.id,
                username = user.username,
                payment_details = data['payment_details'],
                work_programs = programs,
                residence_city = data['residence_city'],
                drive = data['drive'],
            )

        elif orm_user.payment_details is None:
            user_name = orm_user.name
            await orm_add_user_data(
                session, 
                user_id = user.id,
                payment_details = data['payment_details'],
                work_programs = programs,
                residence_city = data['residence_city'],
                drive = data['drive']
            )
            google_table.add_user_info(user_name, data['payment_details'], programs, data['residence_city'], data['drive'])

        else:
            user_name = orm_user.name
            await orm_add_user_drive(
                session, 
                user_id=user.id, 
                drive = data['drive']
            )
            google_table.add_user_drive(user_name, data['drive'])

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
    user = await orm_get_one_user(session, user_id)
    if user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)

    cur_work = False
    for user_work in await orm_get_one_user_works(session, user_id):
        work = await orm_get_one_work(session, user_work.current_work)

        if work.image is None:
            await message.answer(
                f'<b>Работа</b> - {work.title}\n<b>Комментарий:</b> {work.work_comment}\n<b>Срок выполнения:</b> {work.deadline}\n<b>Оклад за работу:</b> {user_work.salary}\n<b>Твоя задача:</b> {user_work.task}'
            )
            cur_work = True         # Есть ли работа у сотрудника или нет
        else:  
                await message.answer_photo(
                    photo=work.image,
                    caption=
                    f'<b>Работа</b> - {work.title}\n<b>Комментарий:</b> {work.work_comment}\n<b>Срок выполнения:</b> {work.deadline}\n<b>Ссылка на файл:</b> <a href="{work.file}"> Work Files </a>\n<b>Оклад за работу:</b> {user_work.salary}\n<b>Твоя задача:</b> {user_work.task}',
                )
                cur_work = True         # Есть ли работа у сотрудника или нет
    else:
        if cur_work == False:
            return await message.answer("У тебя нет текущей работы")


#################################################################################################################
"""
Назначение сотрудника============================================================================================
"""
#################################################################################################################

class DistributeWorker(StatesGroup):
    work_id = State()
    task = State()
    name = State()

    mes_id = None

    texts = {
    "DistributeWorker:task": 'Введите задачу',
    "DistributeWorker:name": 'Выберите имя',
    }

#################################################################################################################
@user_router.callback_query(AllWorkers.filter())
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

################################################ Команда назад ################################################
@user_router.message(StateFilter(DistributeWorker), Command("назад"))
@user_router.message(StateFilter(DistributeWorker), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == DistributeWorker.task:
        await message.answer('Предыдущего шага нет, напишите "отмена"')
        return

    previous = None
    for step in DistributeWorker.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Вернул к прошлому шагу\n{DistributeWorker.texts[previous.state]}")
            return
        previous = step

################################################ Получение id работы ################################################

@user_router.callback_query(StateFilter(None), F.data.startswith('distribute_'))
async def add_work_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    title_id = callback.data.split('_')[-1]
    await state.set_state(DistributeWorker.work_id)
    await state.update_data(work_id=title_id)
    await state.set_state(DistributeWorker.task)
    await callback.answer('Введите задачу:')
    await callback.message.answer('Введите задачу:', reply_markup=reply.admin_nav)


################################################ Выбор задачи ################################################

@user_router.message(DistributeWorker.task, F.text)
async def add_task(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await message.answer('Выберите сотрудника:', reply_markup = await choice_worker_btns(session))
    await state.update_data(task=message.text)
    await state.set_state(DistributeWorker.name)


################################################ Распределение работы ################################################

@user_router.callback_query(DistributeWorker.name, F.data)
async def add_name(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    await callback.message.delete()
    await state.update_data(name=callback.data)
    data = await state.get_data()
    title_id = data['work_id']
    name = data['name'].split(' @')[0]
    salary = 'Не указана'
    task = data['task']
    
    task_and_name = str(f"🫡  {data['task']} - {data['name']}")

    before_added = await orm_get_one_work(session, title_id)
    for users in await orm_get_users(session):
        if users.name in name:
            user = users.user_id
            user_info = users

    user = await orm_get_one_user_by_name(session, name)
    try:
        await orm_add_user_work(
            session,
            user_id=user.user_id,
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
        await state.clear()

    except Exception as e:
        await callback.answer(f'Ошибка: {e}')
        await callback.message.answer(f'Ошибка: {e}', reply_markup=reply.admin_kb)
        await state.clear()

    i = await orm_get_one_work(session, title_id)
        
    # Отправка информации пользователю
    await bot.send_message(chat_id=user.user_id, text='Вам назначена новая работа\nБолее подробно можно узнать написав /current_work')
    await bot.send_photo(chat_id=user.user_id, photo=i.image, caption=
            f'💰 - {i.title}\n💬 - {i.work_comment}\n🗓 - {i.deadline}\n📂 - {i.file_name}\n👉 - <a href="{i.file}"> Work Files </a>\n<b>Твоя задача</b>: {task}',
            parse_mode='HTML')

    user_info = [title_id, task, 'В работе', salary]
    google_table = GoogleTable()
    google_table.add_user_work(name=name, data=user_info)


@user_router.message(DistributeWorker.name)
async def add_name2(message: types.Message):
    await message.answer("Необходимо выбрать имя на клавиатуре")


#####################################################################################################################################################
class SendWork(StatesGroup):
    """
    FSM для отправки работы на проверку
    """
    choice_work = State()
    new_title = State()
    comment = State()
    work = State()
    booklet = State()

    work_id = ''


@user_router.message(
    or_f(Command("send_work"), (F.text.lower() == "отправить работу 📧"))
)
async def work_btns(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Вывод клавиатуры для выбора работы
    """
    user_id = message.from_user.id
    user = await orm_get_one_user(session, user_id)
    if user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)
    
    await message.answer("Выбери какую работу из списка отправить на проверку:", reply_markup = await choice_work_btns(session, user_id=message.from_user.id))
    await state.set_state(SendWork.choice_work)

#_________________________________________________________________________________________________
@user_router.callback_query(SendWork.choice_work, F.data)
async def send_work_cmd(callback: types.CallbackQuery, state: FSMContext):
    """
    Выбор работы и запись данных с нее
    """
    await callback.answer()
    await callback.message.delete()
    title = callback.data.split("_")[0]
    work_id = callback.data.split("_")[-1]
    SendWork.work_id = work_id

    if title == 'nothing':
        await callback.message.answer('Введи полное название работы')
        SendWork.work_id = random.randint(1, 10000)
        return await state.set_state(SendWork.new_title)
    
    await state.update_data(choice_work=title)
    await callback.message.answer("Оставь комментарий к работе", reply_markup=reply.send_work_kb)
    await state.set_state(SendWork.comment)

#_________________________________________________________________________________________________
@user_router.message(SendWork.new_title, F.text)
async def set_new_title(message: types.Message, state: FSMContext):
    if len(message.text) > 26: 
        await message.answer('<b>Передумай</b>. <u>Название не должно превышать 26-ти символов</u>')
        return await send_work_cmd(types.CallbackQuery, state)
    
    await state.update_data(choice_work=message.text)
    await message.answer("Оставь комментарий к работе", reply_markup=reply.send_work_kb)
    await state.set_state(SendWork.comment)

#_________________________________________________________________________________________________
@user_router.message(SendWork.comment, F.text)
async def send_work_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Вставь ссылку на работу")
    await state.set_state(SendWork.work)

#_________________________________________________________________________________________________
@user_router.message(SendWork.work, F.text)
async def send_work(message: types.Message, state: FSMContext):
    await state.update_data(work=message.text)
    await message.answer('Прикрепи файл или ссылку буклета')
    await state.set_state(SendWork.booklet)

#_________________________________________________________________________________________________
# Для отправки с документом
@user_router.message(SendWork.booklet, F.document)
async def send_booklet(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    await send_booklet_output(message, bot, state, session, SendWork.work_id)


#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Отправки ссылки
@user_router.message(SendWork.booklet, F.text)
async def send_booklet2(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    if validators.url(message.text) is True:
        await send_booklet_output2(message, bot, state, session, SendWork.work_id)
    else:
        await message.answer('Необходимо загрузить буклет.\n<b>Прикрепи файл или ссылку буклета</b>')
        return send_booklet(message, bot, state, session)

###################################################################################################
@user_router.message(or_f(Command("archival_works"), (F.text.lower() == "архивные работы 🗄️")))
async def archive_cmd(message: types.Message, session: AsyncSession, bot: Bot, state: FSMContext):
    await state.clear()
    user = await orm_get_one_user(session, message.from_user.id)
    if user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)
    
    google_table = GoogleTable()

    await message.answer('Пожалуйста, подождите минуту')
    await bot.send_chat_action(chat_id = user.user_id, action="typing")
    works = google_table.get_user_archive(user.name)
    if works == []:
        await message.answer('У Вас нет архивных работ\nВы можете просмотреть свои <b>текущие работы</b> написать <i>/current_work</i> или открыв свой профиль')

    for work in works:
        if work[-1] in 'FALSE':
            payment_status = 'Не оплачена'
        else:
            payment_status = 'Оплачена'

        archive_work = await orm_get_one_archive_work(session, work[0])
        current_work = await orm_get_one_work(session, work[0])
        if archive_work is not None:
            image = archive_work.image
        elif current_work is not None:
            image = current_work.image
        else:
            await message.answer(f"Работа - {work[0]}\nЗадача - {work[1]}\nОклад - {work[2]}\nСтатус оплаты - {payment_status}")
            image = None
        
        if image is not None:
            await message.answer_photo(photo=image,
                caption=f"Работа - {work[0]}\nЗадача - {work[1]}\nОклад - {work[2]}\nСтатус оплаты - {payment_status}",
            )

#__________________________________________________________________________________________________
@user_router.message(F.text.lower() == "хочу работу 🤑")
async def want_to_work(message: types.Message, bot: Bot, session: AsyncSession):
    user = await orm_get_one_user(session, message.from_user.id)
    if user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)

    sticker = random.choice(['CAACAgIAAxkBAAEM9upnDO_MXyKyN3lMiuJZDVGOZWgKjgACIWQAAjbYYUjm8Vzo9wuZ5DYE', 'CAACAgIAAxkBAAEM9uhnDO_IegTXj2FzE3sos4CrSNzhvgAC4loAAnUwaUhWCw_IhlPokzYE'])
    admin_list = [5825144544, 5624308044, 880624724, 834162337]
    for i in admin_list:
        await bot.send_sticker(chat_id=i, sticker=sticker)
        await bot.send_message(chat_id=i, text=f'{user.name} @{user.username}')
    await message.answer(text='Вас понял 🫡\nОтправил пожелание капитану', reply_markup=reply.start_kb)


# ------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command("timetable"), (F.text.lower() == "график работы 🗓")))
async def nav_cal_handler(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await orm_get_one_user(session, user_id)
    if user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)
    
    await message.answer(text=
        "Таблица с графиком:\nhttps://docs.google.com/spreadsheets/d/1VTlLg0JOvnw-owN4xpzwl7Vl_5vtooEukcCH3phl6Nw", 
        reply_markup=reply.start_kb
    )

##################################################################################################################

@user_router.callback_query(F.data.startswith('profile_'))
async def my_profile2(callback: types.CallbackQuery, session: AsyncSession):
    user_id = callback.data.split('_')[-1]
    await callback.message.delete()
    await callback.answer()
    user_skill = await orm_get_one_user_skills(session, callback.message.from_user.id)
    user = await orm_get_one_user(session, user_id)
    payment = user.payment_details
    programs = user.work_programs
    city = user.residence_city

    user_works = []
    users = await orm_get_users_works(session)               # Получаю всех юзеров с параметром работ
    for user_info in users:                                  # Вход в экземпляр юзера
        for i in user_info.work:                             # Вход в экземпляр UserID.work и получение данных
            if i.user_id == user.user_id:
                user_works.append(f'{i.current_work} -- оклад {i.salary} руб.')

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
                'Редактировать': f'edit_my_profile_{user.user_id}',
                "Навыки ➡️": f"go_on:{user.user_id}"
            }, sizes=(1, 2)
        ), disable_web_page_preview=True
    )

#_________________________________________________________________________________________________
@user_router.message(or_f(Command('my_profile'), (F.text == 'Мой профиль 🪪')))
async def my_profile(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user = await orm_get_one_user(session, message.from_user.id)
    user_skill = await orm_get_one_user_skills(session, message.from_user.id)
    if user.accept_processing is False:                   # Проверка пользовательского соглашения
        return await send_file(message)

    payment = user.payment_details
    programs = user.work_programs
    city = user.residence_city

    user_works = []
    users = await orm_get_users_works(session)               # Получаю всех юзеров с параметром работ
    for user_info in users:                                  # Вход в экземпляр юзера
        for i in user_info.work:                             # Вход в экземпляр UserID.work и получение данных
            if i.user_id == user.user_id:
                user_works.append(f'{i.current_work} -- оклад {i.salary} руб.')
    
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

    await message.answer(
        f'<b>Имя</b>: {user.name}\n<b>Юзернейм</b>: @{user.username}\n<b>{role}</b>\n\n<b>Счет</b>: {payment}\n<b>Программы</b>: {programs}\n<i><b>Город</b></i> - {city}\n\n<b>Ссылка на Яндекс Диск:</b>\n{user.drive}\n<b>Работы сотрудника</b>:\n' + '\n'.join(user_works),
        reply_markup=await get_callback_btns(
            btns={
                'Редактировать': f'edit_my_profile_{user.user_id}',
                "Навыки ➡️": f"go_on:{user.user_id}"
            }, sizes=(1, 2)
        ), disable_web_page_preview=True
    )
#_________________________________________________________________________________________________
@user_router.callback_query(F.data.startswith('go_on:'))
async def user_skills(callback: types.CallbackQuery, session: AsyncSession):
    user_id = callback.data.split(':')[-1]
    await callback.answer()
    await callback.message.delete()
    user_info = await orm_get_one_user_skills(session, user_id)

    if user_info is None:
        await callback.message.answer('Навыки еще не добавлены\nАдминистратор в <i>ближайшее время</i> добавит твои навыки', reply_markup=await get_callback_btns(
            btns={
                '⬅️ Профиль': f'profile_{user_id}'
                }
            )
        )
    user_spec_skill = user_info.special_skills.replace(', ', '\n• ')
    user_skill = user_info.modeling.replace(';', '\n• ')
    skill_grade = user_skill.replace(':', ' - ')
    await callback.message.answer(
        f'<b>Моделирование</b>:\n• {skill_grade}\n\n<b>Особые навыки</b>\n• {user_spec_skill}', reply_markup=await get_callback_btns(
            btns={
                "⬅️ Профиль": f'profile_{user_id}',
            }
        ),
    )
#_________________________________________________________________________________________________
@user_router.callback_query(F.data.startswith('edit_profile_'))
async def edit_my_profile(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = callback.data.split('_')[-1]
    await callback.answer()
    await callback.message.answer(
        '<b>Выбери своего бойца!</b>', reply_markup=await get_callback_btns(
            btns={
                'Наемник': f'role_mercenary_{user_id}',
                'Приключенец': f'role_adventure_{user_id}',
            }
        )
    )
#_________________________________________________________________________________________________
@user_router.callback_query(F.data.startswith('role_'))
@user_router.callback_query(F.data.startswith('edit_my_profile_'))
async def edit_my_profile(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = callback.data.split('_')[-1]
    if callback.data.startswith('role_'):
        if callback.data.split('_')[1] in 'mercenary':
            AddName.role = 'Наемник'
        elif callback.data.split('_')[1] in 'adventure':
            AddName.role = 'Приключенец'

    await callback.answer()
    await state.set_state(AddName.payment_details)
    await callback.message.answer('Введите номер телефона и банк для перевода\nЕсли не хотите вносить изменения, то напишите "."', reply_markup=reply.admin_nav)

    for_change = await orm_get_one_user(session, user_id)
    AddName.for_change = for_change
    AddName.change_prof = True

#_________________________________________________________________________________________________
@user_router.callback_query(F.data == 'file_accept')
async def accept_file(callback: types.CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await orm_get_one_user(session, user_id)
    await orm_update_accept_processing(session=session, user_id=user_id, new_value=True)
    await callback.answer()
    await callback.message.answer('Спасибо за уделенное время')

    google_table = GoogleTable()
    google_table.update_accept_processing(user.name)


##################################################################################################################
@user_router.message(or_f(Command('my_team'), F.text == 'Моя команда 👨‍👧‍👧'))
async def my_team(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    emp_list = []
    
    emp = await orm_get_team_emp(session, message.from_user.id)
    if emp is None:
        return await message.answer('У Вас еще нет команды 😢')

    for teammate in await orm_get_teammates(session, emp.team_name):
        if teammate.captain is True:
            emp_list.insert(0, f'{teammate.name} 🥇')
        else:
            emp_list.append(teammate.name)
    workers = '\n'.join(emp_list)

    works = []
    for work in await orm_get_one_user_works(session, message.from_user.id):
        works.append(work.current_work)
    works_list = '\n🏠 '.join(works)

    for captain in await orm_get_captains(session):
        if message.from_user.id == captain.id:
            return await message.answer(f'Состав команды 👨‍👧‍👧:\n{workers}\n\nТекущие работы 🚀:\n🏠 {works_list}', reply_markup=await get_callback_btns(
                btns={
                    'Распределение задач': f'assign_tasks',
                }, sizes=(1,1)
            )
        )
    else:
        await message.answer(f'Состав команды 👨‍👧‍👧:\n{workers}\n\nТекущие работы 🚀:\n🏠 {works_list}')


#______________________________________________________________________________________________________________________
@user_router.callback_query(F.data == 'assign_tasks')
async def assign_tasks(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.answer('Выбери работы из списка', reply_markup=await captain_works(session, callback.from_user.id))


@user_router.message(Command('work_check'))
async def test_work_check(message: types.Message):
    data = {
        'title': 'Test',
        'work_link': 'https://yandex.ru',
        'booklet': '-',
    }

    key = os.getenv('SITE_KEY')
    # Отправляем POST-запрос на ваш сайт
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                "http://127.0.0.1:8000/api/telegram/message",
                json=data,
                headers={"X-API-Key": key}
            )
            if response.status == 200:
                await message.answer("✅ Сообщение сохранено на сайте!")
            else:
                await message.answer("❌ Ошибка при сохранении.")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {str(e)}")