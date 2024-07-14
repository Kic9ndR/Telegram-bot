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
timetable_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Работаю 🖥️'),
            KeyboardButton(text='Не работаю 😴'),
        ],
        [
            KeyboardButton(text='Назад ⬅️'),
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
            KeyboardButton(text='Назад ⬅️'),
            KeyboardButton(text='Загрузить 📥'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
current_work_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Назад ⬅️'),
            KeyboardButton(text='Архив работ 🗄️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

#----------------------------------------------------------------------------------
archive_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Назад ⬅️'),
            KeyboardButton(text='В начало ↩️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)
