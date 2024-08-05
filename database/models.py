from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    create: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    update: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

###################################################################################################################
###################################################################################################################
class Work(Base):
    __tablename__ = 'work'

    title: Mapped[str] = mapped_column(String(150), unique=True, primary_key=True)
    deadline: Mapped[int] = mapped_column(nullable=False)
    file_name: Mapped[str] = mapped_column(String(150))
    file: Mapped[str] = mapped_column(String(150), nullable=False)
    worker_name: Mapped[str] = mapped_column(String(150), nullable=True)
    image: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)


###################################################################################################################
class UnreadyWorks(Base):
    __tablename__ = 'unready works'

    title: Mapped[str] = mapped_column(String(150), unique=True, primary_key=True)
    deadline: Mapped[int] = mapped_column(nullable=False)
    file_name: Mapped[str] = mapped_column(String(150))
    file: Mapped[str] = mapped_column(String(150), nullable=False)
    worker_name: Mapped[str] = mapped_column(nullable=True)
    image: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)


###################################################################################################################
class UserID(Base):
    __tablename__ = 'user id'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    current_work: Mapped[str] = mapped_column(String(150), nullable=True)


###################################################################################################################
class AdminID(Base):
    __tablename__ = 'admin id'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)

###################################################################################################################

class WorkCheck(Base):
    __tablename__ = 'work check'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
