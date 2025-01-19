from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_captains

async def teams_list(session: AsyncSession):
    teams = []

    for captain in await orm_get_captains(session):
        if captain.team_name not in teams:
            teams.append(captain.team_name)

    return teams