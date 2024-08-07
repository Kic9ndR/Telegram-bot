from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import AdminID, UnreadyWorks, UserID, Work, WorkCheck

    
############################################## Добавление id администраторов ##############################################

async def orm_add_admin(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    username: str | None = None,
):
    query = select(AdminID).where(AdminID.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            AdminID(
                user_id=user_id, 
                first_name=first_name, 
                username=username, 
                )
        )
        await session.commit()



async def orm_get_admin_info(session: AsyncSession):
    query = select(AdminID)
    result = await session.execute(query)
    return result.scalars().all()

def get_admin_info(session):
    query = select(AdminID)
    result = session.execute(query)
    return result.scalars().all()



############################################## Добавление id пользователей ##############################################

async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str,
    username: str,
    current_work: str,
):
    query = select(UserID).where(UserID.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            UserID(
                user_id=user_id, 
                first_name=first_name,
                username=username, 
                current_work=current_work
                )
        )
        await session.commit()

        
############################################## Получение инфы пользователей ##############################################

async def orm_get_user_info(session: AsyncSession):
    query = select(UserID)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_user(session: AsyncSession, user_id):
    query = select(UserID).where(UserID.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_add_current_work(session: AsyncSession, user_id: int, title: str):
    query = (
        update(UserID).where(UserID.user_id == user_id)
        .values(current_work=title)
        )
    
    await session.execute(query)
    await session.commit()


async def orm_delete_user_work(session: AsyncSession, title: str):
    query = update(UserID).where(UserID.current_work == title).values(current_work=None)
    await session.execute(query)
    await session.commit()

############################################## Создание работы ##############################################

async def orm_add_work(
        session: AsyncSession, 
        title: str,
        deadline: int,
        file_name: str,
        file: str,
        worker_name: str,
        image: str,
    ):

    query = select(Work).where(Work.title == title)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            Work(
                    title = title,
                    deadline = deadline,
                    file_name = file_name,
                    file = file,
                    worker_name = worker_name,
                    image = image,
                )
        )
        await session.commit()


############################################## Создание базы для проверкии работ ##############################################

async def orm_add_chech_work(
        session,
        user_id: int,
        first_name: str,
        username: str,
        title: str,
    ):

    query = select(WorkCheck).where(WorkCheck.title == title)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            WorkCheck(
                    user_id = user_id,
                    first_name = first_name,
                    username = username,
                    title = title,
                )
        )
        await session.commit()
    

############################################## Удаление работ ##############################################

async def orm_delete_un_work(session: AsyncSession, title: str):
    query = delete(UnreadyWorks).where(UnreadyWorks.title == title)
    await session.execute(query)
    await session.commit()


async def orm_delete_ready_work(session: AsyncSession, title: str):
    query = delete(Work).where(Work.title == title)
    await session.execute(query)
    await session.commit()


############################################## Отправка работы ##############################################

async def orm_add_task(session: AsyncSession, data: dict):
    obj = UnreadyWorks(
        title = data['title'],
        deadline = data['deadline'],
        file_name = data['file_name'],
        file = data['file'],
        worker_name = '',
        image = data['image'],
    )

    session.add(obj)
    await session.commit()


############################################## Выбор исполнителя ##############################################

async def orm_appoint_worker(session: AsyncSession, title_id: str, new_worker: str):
    query = (
        update(UnreadyWorks)
        .where(UnreadyWorks.title == title_id)
        ).values(worker_name=UnreadyWorks.worker_name + '\n' + new_worker)
    
    await session.execute(query)
    await session.commit()

async def orm_delete_worker(session: AsyncSession, title_id: str):
    query = (
        update(UnreadyWorks)
        .where(UnreadyWorks.title == title_id)
        ).values(worker_name='')
    
    await session.execute(query)
    await session.commit()


async def orm_change(session: AsyncSession, title:str, data: dict):
    query = (
        update(UnreadyWorks)
        .where(UnreadyWorks.title == title)
        ).values(
            title = data['title'],
            deadline = data['deadline'],
            file_name = data['file_name'],
            file = data['file'],
            image = data['image'],
        )
    
    await session.execute(query)
    await session.commit()



####################################### Получение информации о всех работах ##########################################

async def orm_get_all_works(session: AsyncSession):
    query = select(Work)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_ready_work(session: AsyncSession, title):
    query = select(Work).where(Work.title == title)
    result = await session.execute(query)
    return result.scalar()


#################################################### Не завершенные ##################################################

async def orm_get_work(session: AsyncSession, title):
    query = select(UnreadyWorks).where(UnreadyWorks.title == title)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_all_unready(session: AsyncSession):
    query = select(UnreadyWorks)
    result = await session.execute(query)
    return result.scalars().all()


