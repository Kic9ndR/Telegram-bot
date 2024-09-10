from aiogram.types import (ReplyKeyboardMarkup, ReplyKeyboardRemove,
                            KeyboardButton)



del_kb = ReplyKeyboardRemove()

#----------------------------------------------------------------------------------
start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Текущая работа ⏱'),
            KeyboardButton(text='Отправить работу 📧'),
        ],
        [
            KeyboardButton(text='Отчет о работе 💬'),
            KeyboardButton(text='Хочу работу 🤑'),
        ],
        [
            KeyboardButton(text='График работы 🗓'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:",
)

#----------------------------------------------------------------------------------
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Списки сотрудников 📋'),
            KeyboardButton(text='Таблицы 𝄜'),

        ],
        [
            KeyboardButton(text='Список работ 📜'),
            KeyboardButton(text='Добавление проекта 📊'),
        ],
        [
            KeyboardButton(text='Создание задачи ✍🏼'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)

admin_nav = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Назад'),
            KeyboardButton(text='Отмена'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Назад - вернуться на шаг назад. Отмена - отменить создание"
)

#----------------------------------------------------------------------------------
send_work_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='В начало ↩️'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт:"
)
