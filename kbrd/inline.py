from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import *


# Настраиваемые кнопки
def get_callback_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


# CallBack и URL кнопки
def get_url_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, url in btns.items():
        
        keyboard.add(InlineKeyboardButton(text=text, url=url))

    return keyboard.adjust(*sizes).as_markup()


#Создать микс из CallBack и URL кнопок
def get_inlineMix_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            keyboard.add(InlineKeyboardButton(text=text, url=value))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=value))

    return keyboard.adjust(*sizes).as_markup()



##################################################################################################################

class ChoiceWorker(CallbackData, prefix="Worker"):
    action: str                                 # Вперед и назад для кнопок навигации
    page: int = 0                               # Страница с работниками

# Выбор сотрудника
async def choice_worker_btns(
        session: AsyncSession,
        sizes = (1,2,),
        page: int = 0,
        ):

    keyboard = InlineKeyboardBuilder()
    start_offset = page * 12
    limit = 12
    end_offset = start_offset + limit
    user_info = await orm_get_users(session)

    keyboard.add(InlineKeyboardButton(text=f"Страница {page + 1}", callback_data='page'))  # Добавление кнопки "страница"
    for worker in user_info[start_offset:end_offset]:
        keyboard.add(InlineKeyboardButton(text=f'{worker.name}', callback_data=f"{worker.name} @{worker.username}"))
        
    keyboard.adjust(*sizes)

    buttons_row = []                                        # Создание списка кнопок
    if page > 0:                                            # Проверка, что страница не первая
        buttons_row.append(InlineKeyboardButton(text="⬅️", callback_data=ChoiceWorker(action="prev", page=page - 1).pack()))  # Добавление кнопки "назад"
    if end_offset < len(user_info):                         # Проверка, что ещё есть пользователи для следующей страницы
        buttons_row.append(InlineKeyboardButton(text="➡️", callback_data=ChoiceWorker(action="next", page=page + 1).pack()))  # Добавление кнопки "вперед"

    keyboard.adjust(*sizes)

    return keyboard.row(*buttons_row).as_markup()


# Выбор работы для отправки
async def choice_work_btns(
        session: AsyncSession,
        user_id: int,
        sizes = (2,),
        ):

    
    keyboard = InlineKeyboardBuilder()
    works = await orm_get_user_works(session)

    for work in works:
        if int(work.user_id) == int(user_id):
            keyboard.add(InlineKeyboardButton(text=
                    f'{work.current_work}', callback_data=f"{work.current_work}_{work.work_id}")
            )
    else:
        keyboard.add(InlineKeyboardButton(text=
                f'Сами разберутся', callback_data=f"nothing_")
        )

    return keyboard.adjust(*sizes).as_markup()


####################################### Создание клавиатуры для выбора работы #######################################
class ChoiceWork(CallbackData, prefix="Works"):
    category: str | None = None                 # Опубликованные работы или нет
    action: str                                 # Вперед и назад для кнопок навигации
    page: int = 0                               # Страница с работами
    work_title: int | None = None               # Название работы


async def choice_works_btns(
    session: AsyncSession,
    *,
    category: str,
    page: int = 0,
    sizes: tuple[int] = (1,2,)
):
    not_published_works = await orm_get_works_not_publish(session)
    published_works = await orm_get_works_publish(session)
    archive_works = await orm_get_archive_works(session)

    keyboard = InlineKeyboardBuilder()
    start_offset = page * 14
    limit = 14
    end_offset = start_offset + limit


    if category == 'realized':
        count_works = len(published_works)
        if count_works > 0:
            keyboard.add(InlineKeyboardButton(text=f"Опубликованные работы\nСтраница {page + 1}", callback_data='page'))  # Добавление кнопки "страница"
            for work in published_works[start_offset:end_offset]:
                keyboard.add(InlineKeyboardButton(text=f'{work.title}', callback_data=f'work_{work.title}'))
        else:
            keyboard.add(InlineKeyboardButton(text=f"Работы отсутствуют", callback_data='page'))  # Добавление кнопки отсутствия работы
    elif category == "process":
        count_works = len(not_published_works)
        if count_works > 0:
            keyboard.add(InlineKeyboardButton(text=f"В процессе создания\nСтраница {page + 1}", callback_data='page'))  # Добавление кнопки "страница"
            for work in not_published_works[start_offset:end_offset]:
                keyboard.add(InlineKeyboardButton(text=f'{work.title}', callback_data=f'work_{work.title}'))
        else:
            keyboard.add(InlineKeyboardButton(text=f"Работы отсутствуют", callback_data='page'))  # Добавление кнопки отсутствия работы
    else:
        count_works = len(archive_works)
        if count_works > 0:
            keyboard.add(InlineKeyboardButton(text=f"Архивные работы\nСтраница {page + 1}", callback_data='page'))  # Добавление кнопки "страница"
            for work in archive_works[start_offset:end_offset]:
                keyboard.add(InlineKeyboardButton(text=f'{work.title}', callback_data=f'archive_{work.title}'))
        else:
            keyboard.add(InlineKeyboardButton(text=f"В архиве только пыль...", callback_data='page'))  # Добавление кнопки отсутствия работы
    
    keyboard.adjust(*sizes)

    buttons_row = []                                        # Создание списка кнопок
    if page > 0:                                            # Проверка, что страница не первая
        buttons_row.append(InlineKeyboardButton(text="⬅️", callback_data=ChoiceWork(action="prev", page=page - 1, category=category).pack()))  # Добавление кнопки "назад"
    buttons_row.append(InlineKeyboardButton(text=f"↩️", callback_data='comeback'))  # Добавление кнопки "вернуться"
    if end_offset < count_works:                    # Проверка, что ещё есть пользователи для следующей страницы
        buttons_row.append(InlineKeyboardButton(text="➡️", callback_data=ChoiceWork(action="next", page=page + 1, category=category).pack()))  # Добавление кнопки "вперед"
    
    keyboard.adjust(*sizes)

    return keyboard.row(*buttons_row).as_markup()
 