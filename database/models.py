from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.declarative import declarative_base


class Base(DeclarativeBase):
    pass

###################################################################################################################
###################################################################################################################
class Work(Base):
    __tablename__ = 'work'

    title: Mapped[str] = mapped_column(String(150), unique=True, primary_key=True)
    deadline: Mapped[int] = mapped_column(unique=False, nullable=False)
    file_name: Mapped[str] = mapped_column(String(150), unique=False)
    file: Mapped[str] = mapped_column(String(150), unique=False, nullable=False)
    worker_name: Mapped[str] = mapped_column(unique=False, nullable=True)
    image: Mapped[str] = mapped_column(String(150), unique=False, nullable=False)
    ready_status: Mapped[bool] = mapped_column(nullable=True)


###################################################################################################################

class UserID(Base):
    __tablename__ = 'user_id'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    current_work: Mapped[str] = mapped_column(String(150), nullable=True)
    salary: Mapped[int] = mapped_column(String(150), nullable=True)
    check_work: Mapped[bool] = mapped_column(nullable=True)


###################################################################################################################
class AdminID(Base):
    __tablename__ = 'admin id'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)

###################################################################################################################
class Archive(Base):
    __tablename__ = 'archive'

    title: Mapped[str] = mapped_column(String(150), unique=True, primary_key=True)
    deadline: Mapped[int] = mapped_column(unique=False, nullable=False)
    file_name: Mapped[str] = mapped_column(String(150), unique=False)
    file: Mapped[str] = mapped_column(String(150), unique=False, nullable=False)
    worker_name: Mapped[str] = mapped_column(unique=False, nullable=True)
    image: Mapped[str] = mapped_column(String(150), unique=False, nullable=False)
    create_time: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
