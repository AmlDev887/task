from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import String,BigInteger,Enum,ForeignKey,DateTime, UniqueConstraint
from app.schemas.roles import OrderRoleUser,TaskStatus,TaskPriority,EmailTokensEnum
from typing import List,Optional
from datetime import datetime,date
from app.database.db import engine

class Base(DeclarativeBase):
    pass

class Projects(Base):
    __tablename__ = "projects"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name:Mapped[str] = mapped_column(String(50), nullable=False)
    description:Mapped[Optional[str]] = mapped_column(String(225), nullable=True)
    owner_id:Mapped[int] = mapped_column(ForeignKey("users.id"))

    user:Mapped["Users"] = relationship(back_populates="project")
    task:Mapped[List["Tasks"]] = relationship(back_populates="project")
    project_member:Mapped[List["ProjectMembers"]] = relationship(back_populates="project")

class Users(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    full_name:Mapped[str] = mapped_column(String(60), nullable=False)
    hashed_password:Mapped[str] = mapped_column(String(225), nullable=False)
    role:Mapped[Enum] = mapped_column(Enum(OrderRoleUser,name = 'order_status_enum', create_type = False),nullable=False)
    is_active:Mapped[bool] = mapped_column(nullable=False, default = True)
    is_verified:Mapped[bool] = mapped_column(nullable=False, default= False)

    created_tasks:Mapped[List["Tasks"]] = relationship(back_populates="creator", foreign_keys="[Tasks.creator_id]")
    assigned_tasks:Mapped[List["Tasks"]] = relationship(back_populates="assignee", foreign_keys="[Tasks.assignee_id]")
    project:Mapped[List["Projects"]] = relationship(back_populates="user")
    project_member:Mapped[List["ProjectMembers"]] = relationship(back_populates="user")
    comment:Mapped[List["Comments"]] = relationship(back_populates="author")

class ProjectMembers(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id:Mapped[int] = mapped_column(ForeignKey("projects.id"))
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id")) 

    user:Mapped["Users"] = relationship(back_populates="project_member")
    project:Mapped["Projects"] = relationship(back_populates="project_member")


class Tasks(Base):
    __tablename__ = "tasks"

    id:Mapped[int] = mapped_column(BigInteger,primary_key=True, autoincrement=True)
    title:Mapped[str] = mapped_column(String(60), nullable=False)
    description:Mapped[Optional[str]] = mapped_column(String(225),nullable=True)
    status:Mapped[Enum] = mapped_column(Enum(TaskStatus, name = "task_status_enum",create_type = False), nullable=False)
    priority:Mapped[Enum] = mapped_column(Enum(TaskPriority, name = "task_priority_enum",create_type = False), nullable=False)
    due_date:Mapped[date] = mapped_column(nullable=False,index=True)
    project_id:Mapped[int] = mapped_column(ForeignKey("projects.id",ondelete = "CASCADE"),index=True, nullable=False)
    creator_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"))
    assignee_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"),index=True,nullable=True)
    completed_at:Mapped[Optional[datetime]] = mapped_column(DateTime,nullable=True) 
    deleted_at:Mapped[Optional[datetime | None]] = mapped_column(DateTime(timezone=True), nullable=True) 
    
    creator:Mapped["Users"] = relationship(back_populates="created_tasks", foreign_keys=[creator_id])
    assignee:Mapped[Optional["Users"]] = relationship(back_populates="assigned_tasks", foreign_keys=[assignee_id])
    project:Mapped["Projects"] = relationship(back_populates="task")
    tasktags:Mapped[List["TaskTags"]] = relationship(back_populates="task")
    comment:Mapped[List["Comments"]] = relationship(back_populates="task")

class Tags(Base):
    __tablename__="tags"

    id:Mapped[Optional[int]] = mapped_column(BigInteger,primary_key=True, autoincrement=True)
    name:Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    color:Mapped[str] = mapped_column(String(60),nullable=False)

    tasktags:Mapped[List["TaskTags"]] = relationship(back_populates="tag")

class TaskTags(Base):
    __tablename__="task_tags"

    id:Mapped[int] = mapped_column(BigInteger,primary_key=True, autoincrement=True)
    task_id:Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete = "CASCADE"), nullable=False)
    tags_id:Mapped[int] = mapped_column(ForeignKey("tags.id",ondelete = "CASCADE"), nullable=False)

    task:Mapped["Tasks"] = relationship(back_populates="tasktags")
    tag:Mapped["Tags"] = relationship(back_populates="tasktags")

class Comments(Base):
    __tablename__="comments"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id:Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete = "CASCADE"), nullable = False)
    author_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"), nullable = False)
    body:Mapped[str] = mapped_column(String(225))

    author:Mapped["Users"] = relationship(back_populates="comment")
    task:Mapped["Tasks"] = relationship(back_populates="comment")

class History(Base):
    __tablename__ = "task_history"
    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"))
    task_id:Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete = "CASCADE"))
    field:Mapped[str] = mapped_column(String(60)) 
    old_value:Mapped[str] = mapped_column(String(40))
    new_value:Mapped[str] = mapped_column(String(40))

class EmailTokens(Base):
    __tablename__ = "email_tokens"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id", ondelete = "CASCADE"))
    token:Mapped[str] = mapped_column(String(225), nullable=False)
    purpose:Mapped[Enum] = mapped_column(Enum(EmailTokensEnum, name = "email_tokens_enum",create_type = False), nullable=False)
    expires_at:Mapped[datetime] = mapped_column(DateTime,nullable=False)
    used_at:Mapped[Optional[datetime]] = mapped_column(DateTime,nullable=True)

Base.metadata.create_all(engine)