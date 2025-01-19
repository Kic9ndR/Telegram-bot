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
            KeyboardButton(text='Мой профиль 🪪'),
            KeyboardButton(text='Хочу работу 🤑'),
        ],
        [
            KeyboardButton(text='График работы 🗓'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт",
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
            KeyboardButton(text='Создание команды 🥇'),
        ],
        [
            KeyboardButton(text='Создание задачи ✍🏼'),
        ],
        [
            KeyboardButton(text='Быстрая задача 🚀'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите нужный пункт"
)

cancel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Отмена'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder='Нажми кнопку "Отмена", чтобы не отправлять файл'
)

admin_nav = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Назад'),
            KeyboardButton(text='Отмена'),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Назад - вернуться на шаг назад. Отмена - отменить действие"
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
