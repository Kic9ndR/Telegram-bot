from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton


del_kb = ReplyKeyboardRemove()

#----------------------------------------------------------------------------------
start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Текущая работа ⏱'),
            KeyboardButton(text='Отправить работу 📧'),
        ],
        [
            KeyboardButton(text='Архив работ 🗄️'),
            KeyboardButton(text='О боте 🤖'),
        ],
        [
            KeyboardButton(text='График работы 🗓'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Создание задачи'),
            KeyboardButton(text='Список сотрудников'),
        ],
        [
            KeyboardButton(text='Распределение задач'),
            KeyboardButton(text='Проектный календарь'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
timetable_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Работаю 🖥️'),
            KeyboardButton(text='Не работаю 😴'),
        ],
        [
            KeyboardButton(text='В начало ↩️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
send_work_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Загрузить 📥'),
            KeyboardButton(text='В начало ↩️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
current_work_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Архив работ 🗄️'),
            KeyboardButton(text='В начало ↩️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
archive_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Текущая работа ⏱'),
            KeyboardButton(text='В начало ↩️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------