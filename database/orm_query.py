import math
from unittest.util import strclass
from sqlalchemy import Column, String, select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import AdminID, UserID, Work



    
############################################## Добавление id администраторов ##############################################

async def orm_add_admin(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
):
    query = select(AdminID).where(AdminID.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            AdminID(
                user_id=user_id, 
                first_name=first_name, 
                last_name=last_name, 
                username=username, 
                )
        )
        await session.commit()



async def orm_get_admin_info(session: AsyncSession):
    query = select(AdminID)
    result = await session.execute(query)
    return result.scalars().all()

############################################## Добавление id пользователей ##############################################

async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    current_work: str | None = None,
):
    query = select(UserID).where(UserID.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            UserID(
                user_id=user_id, 
                first_name=first_name, 
                last_name=last_name, 
                username=username, 
                current_work=current_work
                )
        )
        await session.commit()

        
############################################## Получение инфы пользователей ##############################################

async def orm_get_user_info(session: AsyncSession):
    # query = select(UserID).filter(UserID.first_name, UserID.last_name, UserID.username)
    # result = await session.execute(query)
    # return result.scalars()

    query = select(UserID)
    result = await session.execute(query)
    user = result.scalars().all()
    return user
    # if user is None:
    #     raise ValueError(f"User with id {user.user_id} not found")
    # return {
    #     "user_id": user.user_id,
    #     "first_name": user.first_name,
    #     "last_name": user.last_name,
    #     "username": user.username,
    #     "current_work": user.current_work,
    # }



############################################## Создание работы ##############################################

async def orm_add_task(session: AsyncSession, data: dict):
    obj = Work(
        title = data['title'],
        deadline = data['deadline'],
        file_name = data['file_name'],
        file = data['file'],
        worker_name = '',
        image = data['image'],
    )

    session.add(obj)
    await session.commit()

############################################## Изменение работы ##############################################

async def orm_appoint_worker(session: AsyncSession, title_id: str, new_worker: str):
    query = (
        update(Work)
        .where(Work.title == title_id)
        ).values(worker_name=new_worker)
 
    await session.execute(query)
    await session.commit()

####################################### Получение информации о всех работах ##########################################

async def orm_get_work(session: AsyncSession):
    query = select(Work)
    result = await session.execute(query)
    return result.scalars().all()


