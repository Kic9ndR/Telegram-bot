from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_user_works, orm_get_users


def get_callback_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


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



async def choice_worker_btns(
        session: AsyncSession,
        sizes = (2,),
        ):

    user_info = await orm_get_users(session)
    keyboard = InlineKeyboardBuilder()

    for worker in user_info:
        keyboard.add(InlineKeyboardButton(text=
                f'{worker.name}', callback_data=f"{worker.name} @{worker.username}"))

    return keyboard.adjust(*sizes).as_markup()


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
