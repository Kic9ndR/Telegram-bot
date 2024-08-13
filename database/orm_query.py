from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import AdminID, Archive, UserID, Work

    
############################################## Работа с админами ##############################################

async def orm_add_admin(
    session: AsyncSession,
    user_id: int,
    name: str | None = None,
    username: str | None = None,
):
    query = select(AdminID).where(AdminID.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            AdminID(
                user_id=user_id, 
                name=name, 
                username=username, 
                )
        )
        await session.commit()


async def orm_get_admins(session: AsyncSession):
    query = select(AdminID)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_one_admin(session: AsyncSession, user_id):
    query = select(AdminID).where(AdminID.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


############################################## Работа с сотрудниками ##############################################

async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    username: str,
):
    query = select(UserID).where(UserID.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            UserID(
                user_id=user_id, 
                name=name, 
                username=username,
                )
        )
        await session.commit()

async def orm_get_users(session: AsyncSession):
    query = select(UserID)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_one_user(session: AsyncSession, user_id):
    query = select(UserID).where(UserID.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_update_user_status(session: AsyncSession, user_id: int, new_value: str):
    query = (
        update(UserID)
        .where(UserID.user_id == user_id)
        .values(check_work=new_value)
    )
    await session.execute(query)
    await session.commit()


async def orm_update_user_work(
        session: AsyncSession, 
        user_id: int, 
        current_work: str,
        salary: int,
        check_work: bool,
):
    query  = (
        update(UserID)
        .where(UserID.user_id == user_id)
        .values(current_work=current_work,
                salary=salary,
                check_work=check_work
                )
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_user_work(
        session: AsyncSession, 
        user_id: int,
):
    query  = (
        update(UserID)
        .where(UserID.user_id == user_id)
        .values(current_work=None,
                salary=None,
                check_work=False
                )
    )
    await session.execute(query)
    await session.commit()

############################################## Добавление работы ##############################################

async def orm_add_work(
    session: AsyncSession,
    title: str,
    deadline: int,
    file_name: str,
    file: str,
    worker_name: str,
    image: str,
    ready_status: bool,
):
    query = select(Work).where(Work.title == title)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            Work(
                title=title,
                deadline=deadline,
                file_name=file_name,
                file=file,
                worker_name=worker_name,
                image=image,
                ready_status=ready_status,
            )
        )
    await session.commit()

async def orm_get_works(session: AsyncSession):
    query = select(Work)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_one_work(session: AsyncSession, title):
    query = select(Work).where(Work.title == title)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_work_status(session: AsyncSession, title: str, new_value: str):
    query = (
        update(Work)
        .where(Work.title == title)
        .values(ready_status=new_value)
    )
    await session.execute(query)
    await session.commit()


async def orm_update_work_worker_name(session: AsyncSession, title: str, new_value: str):
    query = (
        update(Work)
        .where(Work.title == title)
        .values(worker_name=Work.worker_name + "\n" + new_value)
    )
    await session.execute(query)
    await session.commit()


async def orm_add_work_worker_name(session: AsyncSession, title: str, new_value: str):
    query = (
        update(Work)
        .where(Work.title == title)
        .values(worker_name=new_value)
    )
    await session.execute(query)
    await session.commit()



async def orm_update_work(session: AsyncSession, title: str, data: dict):
    query = (
        update(Work)
        .where(Work.title == title)
        .values(
            title=data['title'],
            deadline=data['deadline'],
            file_name=data['file_name'],
            file=data['file'],
            image=data['image'],
        )
    )
    await session.execute(query)
    await session.commit()



async def orm_delete_work(session: AsyncSession, title: str):
    query = delete(Work).where(Work.title == title)
    await session.execute(query)
    await session.commit()


############################################## Работа с архивом ##############################################

async def orm_add_archive_work(
    session: AsyncSession,
    title: str,
    deadline: int,
    file_name: str,
    file: str,
    worker_name: str,
    image: str,
):
    query = select(Archive).where(Archive.title == title)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            Archive(
                title=title,
                deadline=deadline,
                file_name=file_name,
                file=file,
                worker_name=worker_name,
                image=image,
                )
        )
        await session.commit()

async def orm_get_archive_works(session: AsyncSession):
    query = select(Archive)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_one_archive_work(session: AsyncSession, title):
    query = select(Archive).where(Archive.title == title)
    result = await session.execute(query)
    return result.scalar()

