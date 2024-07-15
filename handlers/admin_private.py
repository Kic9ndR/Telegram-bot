from cgitb import text
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from filters.chat_types import ChatFilter, IsAdmin
from kbrd import reply
from kbrd.reply import admin_kb, del_kb

#----------------------------------------------------------------------------------
admin_router = Router()
admin_router.message.filter(ChatFilter(["private"]), IsAdmin())

#----------------------------------------------------------------------------------
@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=admin_kb)

#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Список сотрудников")
async def worker_list(message: types.Message):
    await message.answer("ОК, вот список сотрудников")

#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Распределение задач")
async def task_distrib(message: types.Message):
    await message.answer("Кому хотите передать задачу?")

#----------------------------------------------------------------------------------
@admin_router.message(F.text == "Проектный календарь")
async def project_klnd(message: types.Message):
    await message.answer("ОК, вот календарь:")

#----------------------------- Код ниже для машины состояний (FSM) -----------------------------

class CreateTask(StatesGroup):
    street = State()
    deadline = State()
    file_name = State()
    file = State()
    name = State()
    image = State()

    texts = {
        'CreateTask:street': 'Введите улицу повторно: ',
        'CreateTask:deadline': 'Введите срок выполнения повторно: ',
        'CreateTask:file_name': 'Введите названия файла повторно: ',
        'CreateTask:file': 'Загрузите файл повторно: ', #------------- протестировать данный вариант на ошибку
        'CreateTask:name': 'Введите имена через запятую: ',
        'CreateTask:image': 'Загрузите изображение повторно: ', #------ протестировать данный вариант на ошибку
    }

#----------------------------------------------------------------------------------
@admin_router.message(StateFilter(None), F.text == "Создание задачи")
async def create_task(message: types.Message, state: FSMContext):
    await message.answer("Введите название улицы: ", reply_markup=reply.del_kb)
    await state.set_state(CreateTask.street)

@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=admin_kb)


#----------------------------------------------------------------------------------
@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == CreateTask.street:
        await message.answer('Предыдущего шага нет, напишите "отмена"')
        return

    previous = None
    for step in CreateTask.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу \n {CreateTask.texts[previous.state]}")
            return
        previous = step

#----------------------------------------------------------------------------------
@admin_router.message(CreateTask.street, F.text)
async def set_street(message: types.Message, state: FSMContext):
    await state.update_data(street=message.text)
    await message.answer("Введите срок выполнения: ")
    await state.set_state(CreateTask.deadline)

@admin_router.message(CreateTask.street)
async def set_street2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать текст ")

#----------------------------------------------------------------------------------
@admin_router.message(CreateTask.deadline, F.text)
async def set_deadline(message: types.Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer("Введите название файла: ")
    await state.set_state(CreateTask.file_name)

@admin_router.message(CreateTask.deadline)
async def set_deadline2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо написать число ")

#----------------------------------------------------------------------------------
@admin_router.message(CreateTask.file_name, F.text)
async def set_file_name(message: types.Message, state: FSMContext):
    await state.update_data(file_name=message.text)
    await message.answer("Загрузите файл: ")
    await state.set_state(CreateTask.file)

@admin_router.message(CreateTask.file_name)
async def set_file_name2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо ввести название файла")

# #----------------------------------------------------------------------------------
@admin_router.message(CreateTask.file, F.document)
async def set_file(message: types.Message, state: FSMContext):
    await state.update_data(file=message.document)
    await message.answer("Введите имена через запятую: ")
    await state.set_state(CreateTask.name)

@admin_router.message(CreateTask.file)
async def set_file2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо загрузить файл ")

#----------------------------------------------------------------------------------
@admin_router.message(CreateTask.name, F.text)
async def add_names(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Загрузите изображение: ")
    await state.set_state(CreateTask.image)

@admin_router.message(CreateTask.name)
async def add_names2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Добавьте имена через запятую ")

#----------------------------------------------------------------------------------
@admin_router.message(CreateTask.image, F.photo)
async def add_image(message: types.Message, state: FSMContext):
    await state.update_data(image=message.photo[-1].file_id)
    await message.answer("Задача добавлена!", reply_markup=admin_kb)
    data = await state.get_data()
    await message.answer(str(data))
    await state.clear()

@admin_router.message(CreateTask.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Ввели данные неверно. Необходимо загрузить фото")