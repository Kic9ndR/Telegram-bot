from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command, or_f
from filters.chat_types import ChatFilter

from kbrd import reply

user_router = Router()
user_router.message.filter(ChatFilter(['private']))



@user_router.message(or_f(Command("start"), (F.text.lower() == "в начало ↩️"), (F.text.lower() == "старт")))
async def start_cmd(message: types.Message):
    await message.answer('Что Вас интересует?', reply_markup=reply.start_kb)

#------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command('current_work'), (F.text.lower() == "текущая работа ⏱")))
async def current_work_cmd(message: types.Message):
    await message.answer('Твоя текущая работа:', reply_markup=reply.current_work_kb)

#------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command('send work'), (F.text.lower() == "отправить работу 📧")))
async def send_work_cmd(message: types.Message):
    await message.answer('Выбери работы:', reply_markup=reply.send_work_kb)

#------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command('archive'), (F.text.lower() == "архив работ 🗄️")))
async def archive_cmd(message: types.Message):
    await message.answer('Прошлые работы:', reply_markup=reply.archive_kb)

#------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command('about'), (F.text.lower() == "о боте 🤖")))
async def about_cmd(message: types.Message):
    await message.answer('Я умею и могу...', reply_markup=reply.start_kb)

#------------------------------------------------------------------------------------------------------
@user_router.message(or_f(Command('timetable'), (F.text.lower() == "график работы 🗓")))
async def timetable_cmd(message: types.Message):
    await message.answer('График работы:', reply_markup=reply.timetable_kb)



