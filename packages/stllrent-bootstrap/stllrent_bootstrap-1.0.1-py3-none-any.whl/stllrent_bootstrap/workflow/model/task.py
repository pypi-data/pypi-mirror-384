# DUMP - Converte classe para JSON (Ex.: DB -> class model -> dump() -> JSON ))
# LOAD - converte JSON em classe (Ex.: POST API -> json -> load() -> class model -> DB)
from ...database.model.core import Base
from ..model.workflow import WorkflowModel
from typing import Any
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
import uuid
from datetime import datetime

class TaskModel(Base):
    __tablename__ = 'task'
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        nullable=False,
        unique=True, 
        index=True,
        init=True
    )
    
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('workflow.oid', 
        ondelete='CASCADE'), 
        index=True, 
        init=False
    )
    
    task_name: Mapped[str] = mapped_column(
        nullable=True,
        unique=False,
        index=False
    )

    task_metadata: Mapped[dict[str, Any]] = mapped_column(
        unique=False, 
        nullable=True, 
        index=False,
        default=None
    )

    task_output: Mapped[dict[str, Any]] = mapped_column(
        unique=False,
        nullable=True,
        index=False,
        init=False,
        default=None
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, init=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=True, onupdate=func.now(), init=False)

    status: Mapped[str] = mapped_column(unique=False, nullable=False, index=False, default="PENDING")
    
    workflow: Mapped["WorkflowModel"] = relationship(
        back_populates='task_list',
        init=False
    )
