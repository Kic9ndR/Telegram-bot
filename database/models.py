from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    create: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    update: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class AdminList(Base):
    __tablename__ = 'admin list'

    id: Mapped[str] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)


class CurrentWork(Base):
    __tablename__ = 'current work'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    work: Mapped[str] = mapped_column(String(150), nullable=False)
    photo: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(150), nullable=False)