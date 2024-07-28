import math
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import AdminList


async def orm_add_admin(
    session: AsyncSession,
    id: int,
    first_name: str | None = None,
    last_name: str | None = None,
):
    query = select(AdminList).where(AdminList.user_id == id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            AdminList(id=id, first_name=first_name, last_name=last_name)
        )
        await session.commit()