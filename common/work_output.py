from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import *
from kbrd.inline import get_callback_btns


async def work_output(callback: types.CallbackQuery, session: AsyncSession, work: str):             # С типом callback
    title = await orm_get_one_work(session, work)
    if title.worker_name is None:                                 # Проверка, что строка исполнителей пустая
        worker_name = 'Исполнители еще не назначены'                # Если пустая, то информирую об этом об этом
    else:
        worker_name = title.worker_name

    if title.image is None:
        await callback.message.answer(
            f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nИсполнитель: \n{worker_name}',
            reply_markup=get_callback_btns(btns={
                'Полностью удалить работу': f'delete_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Назначить': f'appoint_{title.title}',
                '↩️': f'realized'
            }, sizes=(1,1,1)), parse_mode='HTML',
        )
    elif title.ready_status == False:                                 # Если работа еще не опубликована
        await callback.message.answer_photo(
            title.image,
            caption=f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nСписок исполнителей:\n{worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в работу': f'send_{title.title}',
                'Полностью удалить работу': f'delete_{title.title}',
                '↩️': f'process'
            }, sizes=(2,1,1)), parse_mode='HTML',
        )
    else:                                                           # Если уже отправлена в работу
        await callback.message.answer_photo(
            title.image,
            caption=f'{title.title}\n<b>Комментарий</b>: {title.work_comment}\n<b>Срок выполнения:</b> {title.deadline}\n<b>Ссылка на файл:</b> <a href="{title.file}"> Work Files </a>\n<b>Назначены:</b>\n{worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Полностью удалить работу': f'delete_{title.title}',
                '↩️': f'realized'
                }, sizes=(2,1,1)), parse_mode='HTML'
        )



async def work_output2(message: types.Message, session: AsyncSession, work: str):           # С типом message
    title = await orm_get_one_work(session, work)
    if title.worker_name is None:                                 # Проверка, что строка исполнителей пустая
        worker_name = 'Исполнители еще не назначены'                # Если пустая, то информирую об этом об этом
    else:
        worker_name = title.worker_name

    if title.image is None:
        await message.answer(
            f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nИсполнитель: \n{worker_name}',
            reply_markup=get_callback_btns(btns={
                'Полностью удалить работу': f'delete_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Назначить': f'appoint_{title.title}',
                '↩️': f'realized'
            }, sizes=(1,1,1)), parse_mode='HTML',
        )
    elif title.ready_status == False:                                 # Если работа еще не опубликована
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nСписок исполнителей:\n{worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в работу': f'send_{title.title}',
                'Полностью удалить работу': f'delete_{title.title}',
                '↩️': f'process'
            }, sizes=(2,1,1)), parse_mode='HTML',
        )
    else:                                                           # Если уже отправлена в работу
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\n<b>Комментарий</b>: {title.work_comment}\n<b>Срок выполнения:</b> {title.deadline}\n<b>Ссылка на файл:</b> <a href="{title.file}"> Work Files </a>\n<b>Назначены:</b>\n{worker_name}',
            reply_markup=get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Полностью удалить работу': f'delete_{title.title}',
                '↩️': f'realized'
                }, sizes=(2,1,1)), parse_mode='HTML'
        )
