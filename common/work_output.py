# await callback.message.answer_photo(
#     work.image,
#     caption=f'{work.title}\n<b>Комментарий</b>: {work.work_comment}\n<b>Срок выполнения:</b> {work.deadline}\n<b>Ссылка на файл:</b> <a href="{work.file}"> Work Files </a>\n<b>Назначены:</b>\n{work.worker_name}',
#     reply_markup=get_callback_btns(btns={
#         'Назначить': f'appoint_{work.title}',
#         'Изменить': f'select_{work.title}',
#         'Отправить в архив': f'sendarchive_{work.title}',
#         'Полностью удалить работу': f'delete_{work.title}',
#         }, sizes=(2,1,1)), parse_mode='HTML'
# )