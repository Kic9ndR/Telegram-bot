from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


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
    payment_details: Mapped[str] = mapped_column(String(50), nullable=True)
    work_programs: Mapped[str] = mapped_column(String(50), nullable=True)
    residence_city: Mapped[str] = mapped_column(String(50), nullable=True)

    work: Mapped[list["UserWork"]] = relationship(back_populates="user")


###################################################################################################################

class UserWork(Base):
    __tablename__ = 'user work' 

    work_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_id.user_id", ondelete="CASCADE"))
    current_work: Mapped[str] = mapped_column(String(150), unique=False)
    task: Mapped[str] = mapped_column(String(150), unique=False)
    salary: Mapped[int] = mapped_column(String(150), unique=False)
    check_work: Mapped[bool] = mapped_column(unique=False)
    
    user: Mapped["UserID"] = relationship(back_populates="work")


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


###################################################################################################################

class MessageSend(Base):
    __tablename__ = 'send message'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), unique=False, nullable=True)
    user_id: Mapped[int] = mapped_column(unique=False, nullable=False)
    work_link: Mapped[str] = mapped_column(unique=False, nullable=False)
    work_id: Mapped[int] = mapped_column(unique=True, nullable=True)


###################################################################################################################

class PublishedWorks(Base):
    __tablename__ = 'published works'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), unique=False, nullable=True)