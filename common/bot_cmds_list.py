from aiogram.types import BotCommand

private = [
    BotCommand(command="start", description="Начальная панель 🎬"),
    BotCommand(command="archival_works", description="Архив работ 🗄️"),
    BotCommand(command="my_profile", description="Твой профиль с данными 🪪"),
    BotCommand(command="timetable", description="График работы 🗓"),
    BotCommand(command="current_work", description="Текущая работа ⏱"),
    BotCommand(command="send_work", description="Отправка работы 📧"),
]

admin = [
    BotCommand(command='admin', description='Панель управления Админа 😎'),
    BotCommand(command="start", description="Начальная панель 🎬"),
    BotCommand(command="project_preparation", description="Подготовка проекта 🚀"),
    BotCommand(command="archive", description="Архив работ 🗄️"),
    BotCommand(command="current_work", description="Текущая работа ⏱"),
    BotCommand(command="send_work", description="Отправка работы 📧"),
    BotCommand(command='send_users', description='Рассылка всем пользователям 📨'),
]
