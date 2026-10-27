from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import String,BigInteger,Enum,ForeignKey,DateTime, UniqueConstraint,func
from app.schemas.roles import OrderRoleUser,TaskStatus,TaskPriority,EmailTokensEnum,ProjectRole
from typing import List,Optional
from datetime import datetime,date

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default = func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default = func.now(),onupdate= func.now(), nullable=False)

class Projects(Base, TimestampMixin):
    __tablename__ = "projects"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name:Mapped[str] = mapped_column(String(50), nullable=False)
    description:Mapped[Optional[str]] = mapped_column(String(225), nullable=True)
    owner_id:Mapped[int] = mapped_column(ForeignKey("users.id"))

    user:Mapped["Users"] = relationship(back_populates="project")
    task:Mapped[List["Tasks"]] = relationship(back_populates="project")
    project_member:Mapped[List["ProjectMembers"]] = relationship(back_populates="project")

class Users(Base, TimestampMixin):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    full_name:Mapped[str] = mapped_column(String(60), nullable=False)
    hashed_password:Mapped[str] = mapped_column(String(225), nullable=False)
    role:Mapped[OrderRoleUser] = mapped_column(Enum(OrderRoleUser,name = 'user_role_enum',values_callable=lambda e: [m.value for m in e]),default = OrderRoleUser.USER,nullable=False)
    is_active:Mapped[bool] = mapped_column(nullable=False, default = True)
    is_verified:Mapped[bool] = mapped_column(nullable=False, default= False)

    created_tasks:Mapped[List["Tasks"]] = relationship(back_populates="creator", foreign_keys="[Tasks.creator_id]")
    assigned_tasks:Mapped[List["Tasks"]] = relationship(back_populates="assignee", foreign_keys="[Tasks.assignee_id]")
    project:Mapped[List["Projects"]] = relationship(back_populates="user")
    project_member:Mapped[List["ProjectMembers"]] = relationship(back_populates="user")
    comment:Mapped[List["Comments"]] = relationship(back_populates="author")
    history: Mapped[List["History"]] = relationship(back_populates="user")
    attachments:Mapped[List["Attachments"]] = relationship(back_populates="users")

class ProjectMembers(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id:Mapped[int] = mapped_column(ForeignKey("projects.id",  ondelete="CASCADE"))
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id",  ondelete="CASCADE")) 
    role:Mapped[ProjectRole] = mapped_column(Enum(ProjectRole, name = "project_role"))

    user:Mapped["Users"] = relationship(back_populates="project_member")
    project:Mapped["Projects"] = relationship(back_populates="project_member")


class Tasks(Base, TimestampMixin):
    __tablename__ = "tasks"

    id:Mapped[int] = mapped_column(BigInteger,primary_key=True, autoincrement=True)
    title:Mapped[str] = mapped_column(String(200), nullable=False)
    description:Mapped[Optional[str]] = mapped_column(String(225),nullable=True)
    status:Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name = "task_status_enum",values_callable=lambda e: [m.value for m in e]),index = True, nullable=False)
    priority:Mapped[TaskPriority] = mapped_column(Enum(TaskPriority, name = "task_priority_enum",values_callable=lambda e: [m.value for m in e]), nullable=False)
    due_date:Mapped[date] = mapped_column(nullable=False,index=True)
    project_id:Mapped[int] = mapped_column(ForeignKey("projects.id",ondelete = "CASCADE"),index=True, nullable=False)
    creator_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"))
    assignee_id:Mapped[Optional[int]] = mapped_column(ForeignKey("users.id",ondelete = "SET NULL"),index=True,nullable=True)
    completed_at:Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),nullable=True) 
    deleted_at:Mapped[Optional[datetime | None]] = mapped_column(DateTime(timezone=True), nullable=True) 
    version: Mapped[int] = mapped_column(nullable=False, default= False)

    creator:Mapped["Users"] = relationship(back_populates="created_tasks", foreign_keys=[creator_id])
    assignee:Mapped[Optional["Users"]] = relationship(back_populates="assigned_tasks", foreign_keys=[assignee_id])
    project:Mapped["Projects"] = relationship(back_populates="task")
    tasktags:Mapped[List["TaskTags"]] = relationship(back_populates="task")
    comment:Mapped[List["Comments"]] = relationship(back_populates="task")
    history:Mapped[List["History"]] = relationship(back_populates="task")
    attachments:Mapped[List["Attachments"]] = relationship(back_populates="task")


class Attachments(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True,autoincrement=True)
    task_id:Mapped[Optional[int]]= mapped_column(ForeignKey("tasks.id", ondelete = "CASCADE"), nullable=True)
    filename:Mapped[str] = mapped_column(String(225),default="report.pdf")
    size:Mapped[int] = mapped_column(BigInteger)
    content_type:Mapped[str] = mapped_column(String(100))
    path:Mapped[str] = mapped_column(String(500))
    uploaded_by:Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable = True)

    task:Mapped["Tasks"] = relationship(back_populates="attachments")
    users:Mapped["Users"] = relationship(back_populates="attachments")

class Tags(Base, TimestampMixin):
    __tablename__="tags"

    id:Mapped[int] = mapped_column(BigInteger,primary_key=True, autoincrement=True)
    name:Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    color:Mapped[str] = mapped_column(String(60),nullable=False)

    tasktags:Mapped[List["TaskTags"]] = relationship(back_populates="tag")

class TaskTags(Base, TimestampMixin):
    __tablename__="task_tags"
    __table_args__ = (UniqueConstraint("task_id", "tag_id"),)
    
    id:Mapped[int] = mapped_column(BigInteger,primary_key=True, autoincrement=True)
    task_id:Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete = "CASCADE"), nullable=False)
    tag_id:Mapped[int] = mapped_column(ForeignKey("tags.id",ondelete = "CASCADE"), nullable=False)

    task:Mapped["Tasks"] = relationship(back_populates="tasktags")
    tag:Mapped["Tags"] = relationship(back_populates="tasktags")

class Comments(Base, TimestampMixin):
    __tablename__="comments"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id:Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete = "CASCADE"), nullable = False)
    author_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"), nullable = False)
    body:Mapped[str] = mapped_column(String(225))

    author:Mapped["Users"] = relationship(back_populates="comment")
    task:Mapped["Tasks"] = relationship(back_populates="comment")

class History(Base, TimestampMixin):
    __tablename__ = "task_history"
    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id",ondelete = "CASCADE"))
    task_id:Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete = "CASCADE"))
    field:Mapped[str] = mapped_column(String(60)) 
    old_value:Mapped[Optional[str]] = mapped_column(String(100))
    new_value:Mapped[Optional[str]] = mapped_column(String(100))

    user: Mapped["Users"] = relationship(back_populates="history")
    task: Mapped["Tasks"]= relationship(back_populates="history")

class EmailTokens(Base, TimestampMixin):
    __tablename__ = "email_tokens"

    id:Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id", ondelete = "CASCADE"))
    token:Mapped[str] = mapped_column(String(225), nullable=False)
    purpose:Mapped[EmailTokensEnum] = mapped_column(Enum(EmailTokensEnum, name = "email_tokens_enum", values_callable=lambda e: [m.value for m in e]), nullable=False)
    expires_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)
    used_at:Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),nullable=True)
