from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import String,Integer,BigInteger,MetaData,Boolean,Enum,ForeignKey
from app.database.roles import OrderRoleUser
from typing import List
metadata = MetaData()

class Base(DeclarativeBase):
    pass

class Projects(Base):
    __tablename__ = "projects"
    id:Mapped = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name:Mapped[str] = mapped_column(String(50), nullable=False)
    description:Mapped[str] = mapped_column(String(225),)
    owner_id:Mapped[int] = mapped_column(ForeignKey("users.id"))

    user:Mapped[List["Users"]] = relationship(back_populates="project")

class Users(Base):
    __tablename__ = "users"
    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(40), unique=True)
    full_name:Mapped[str] = mapped_column(String(60), nullable=False)
    hashed_password:Mapped[str] = mapped_column(String(225), nullable=False)
    role:Mapped[Enum] = mapped_column(Enum(OrderRoleUser,name = 'order_status_enum', create_type = False),nullable=False)
    is_active:Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_verified:Mapped[bool] = mapped_column(Boolean, nullable=False)

    project:Mapped[List["Projects"]] = relationship(back_populates="user")

class ProjectMembers(Base):
    __tablename__ = "project_members"
    id:Mapped[int] = mapped_column()
