import os
from aiogram import Bot, types
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext

from database.orm_query import *
from kbrd import reply
from kbrd.inline import get_callback_btns

# Тестовые значение
user_chat = os.getenv('USER_CHAT')
work_check = os.getenv('WORK_CHECK')
admin_chat = os.getenv('ADMIN_CHAT')
admin_message_thread = os.getenv('ADMIN_MESSAGE_THREAD')            
message_treads_for_check = os.getenv('MESSAGE_THREAD_FOR_CHECK')

########################################################################################################################################
async def work_output(callback: types.CallbackQuery, session: AsyncSession, work: str):             # С типом callback
    title = await orm_get_one_work(session, work)
    if title.worker_name is None:                                 # Проверка, что строка исполнителей пустая
        worker_name = 'Исполнители еще не назначены'                # Если пустая, то информирую об этом об этом
    else:
        worker_name = title.worker_name

    if title.image is None:
        await callback.message.answer(
            f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nИсполнитель: \n{worker_name}',
            reply_markup=await get_callback_btns(btns={
                'Полностью удалить работу': f'delete_work_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Назначить': f'appoint_{title.title}',
                '↩️': f'realized'
            }, sizes=(1,1,1)), parse_mode='HTML',
        )
    elif title.ready_status == False:                                 # Если работа еще не опубликована
        await callback.message.answer_photo(
            title.image,
            caption=f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nУровень сложности: {title.complexity}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nСписок исполнителей:\n{worker_name}',
            reply_markup=await get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в работу': f'send_{title.title}',
                'Полностью удалить работу': f'delete_work_{title.title}',
                '↩️': f'process'
            }, sizes=(2,1,1)), parse_mode='HTML',
        )
    else:                                                           # Если уже отправлена в работу
        await callback.message.answer_photo(
            title.image,
            caption=f'{title.title}\n<b>Комментарий</b>: {title.work_comment}\n<b>Срок выполнения:</b> {title.deadline}\nУровень сложности: {title.complexity}\n<b>Ссылка на файл:</b> <a href="{title.file}"> Work Files </a>\n<b>Назначены:</b>\n{worker_name}',
            reply_markup=await get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Полностью удалить работу': f'delete_work_{title.title}',
                '↩️': f'realized'
                }, sizes=(2,1,1)), parse_mode='HTML'
        )

################################################################################################################################################

async def work_output2(message: types.Message, session: AsyncSession, work: str):           # С типом message
    title = await orm_get_one_work(session, work)
    if title.worker_name is None:                                 # Проверка, что строка исполнителей пустая
        worker_name = 'Исполнители еще не назначены'                # Если пустая, то информирую об этом об этом
    else:
        worker_name = title.worker_name

    if title.image is None:
        await message.answer(
            f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nИсполнитель: \n{worker_name}',
            reply_markup=await get_callback_btns(btns={
                'Полностью удалить работу': f'delete_work_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Назначить': f'appoint_{title.title}',
                '↩️': f'realized'
            }, sizes=(1,1,1)), parse_mode='HTML',
        )
    elif title.ready_status == False:                                 # Если работа еще не опубликована
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\nКомментарий: {title.work_comment}\nСрок выполнения: {title.deadline}\nУровень сложности: {title.complexity}\nСсылка на файл: <a href="{title.file}"> Work Files </a>\nСписок исполнителей:\n{worker_name}',
            reply_markup=await get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в работу': f'send_{title.title}',
                'Полностью удалить работу': f'delete_work_{title.title}',
                '↩️': f'process'
            }, sizes=(2,1,1)), parse_mode='HTML',
        )
    else:                                                           # Если уже отправлена в работу
        await message.answer_photo(
            title.image,
            caption=f'{title.title}\n<b>Комментарий</b>: {title.work_comment}\n<b>Срок выполнения:</b> {title.deadline}\nУровень сложности: {title.complexity}\n<b>Ссылка на файл:</b> <a href="{title.file}"> Work Files </a>\n<b>Назначены:</b>\n{worker_name}',
            reply_markup=await get_callback_btns(btns={
                'Назначить': f'appoint_{title.title}',
                'Изменить': f'select_{title.title}',
                'Отправить в архив': f'sendarchive_{title.title}',
                'Полностью удалить работу': f'delete_work_{title.title}',
                '↩️': f'realized'
                }, sizes=(2,1,1)), parse_mode='HTML'
        )

################################################################################################################################################
# Отправка файла буклета
async def send_booklet_output(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession, work_id):
    await state.update_data(booklet=message.document)
    data = await state.get_data()
    work_link = data['work']
    work_title = data['choice_work']                        # Название отправляемой работы
    comment = data["comment"]                               # Комментарий к работе
    file = data["booklet"]

    send_work = await bot.send_document(chat_id=int(work_check), document=file.file_id, caption=
            f'Работа <i>{work_title}</i> на проверку от @{message.from_user.username}\nКомментарий к работе: {comment}\n\nСсылка на работу:\n{work_link}',
            reply_markup=await get_callback_btns(btns={
                'Принять работу': f"accept_{work_title}_{message.from_user.id}",
                'Отправить правки': f"edits_{work_title}_{message.from_user.id}"
            }, sizes={1,1}
        )
    )
    
    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    user = await orm_get_one_user(session, message.from_user.id)    # Получаю юзера

    await orm_add_id_send_message(
            session,
            id=send_work.message_id,
            title=work_title,
            user_id=message.from_user.id,
            work_link=work_link,
            work_id=work_id,
            mes_id=0,
        )
    await state.clear()
    await orm_update_user_status(session, user.user_id, True)       # Изменение статуса проверки на "Проверка" в базе данных
    await orm_delete_user_date(session, work_id)                    # Убрать время отправки правок


################################################################################################################################################
# Отправки ссылки
async def send_booklet_output2(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession, work_id):
    await state.update_data(booklet=message.document)
    data = await state.get_data()
    booklet = message.text
    work_link = data['work']
    work_title = data['choice_work']                        # Название отправляемой работы
    comment = data["comment"]                               # Комментарий к работе


    send_work = await bot.send_message(chat_id=int(work_check), text=
            f'Работа <i>{work_title}</i> на проверку от @{message.from_user.username}\nКомментарий к работе: {comment}\n\nСсылка на работу:\n{work_link}\n\nСсылка на буклет:\n{booklet}',
            reply_markup=await get_callback_btns(btns={
                'Принять работу': f"accept_{work_title}_{message.from_user.id}",
                'Отправить правки': f"edits_{work_title}_{message.from_user.id}"
            }, sizes={1,1}
        ), disable_web_page_preview=True
    )

    await message.answer('Работа отправлена. Вы Молодец!', reply_markup=reply.start_kb)
    user = await orm_get_one_user(session, message.from_user.id)    # Получаю юзера

    await orm_add_id_send_message(
        session,
        id=send_work.message_id,
        title=work_title,
        user_id=message.from_user.id,
        work_link=work_link,
        work_id=work_id,
        mes_id=0,
    )
    await state.clear()
    await orm_update_user_status(session, user.user_id, True)       # Изменение статуса проверки на "Проверка" в базе данных
    await orm_delete_user_date(session, work_id)                    # Убрать время отправки правок
