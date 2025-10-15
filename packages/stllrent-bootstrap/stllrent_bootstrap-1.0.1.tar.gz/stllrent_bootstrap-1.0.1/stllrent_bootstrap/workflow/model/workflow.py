from ...database.model.core import Base
from typing import Any
from typing import List
from sqlalchemy import text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.types import Uuid
import uuid
from datetime import datetime

class WorkflowModel(Base):
    __tablename__ = 'workflow'
    
    oid: Mapped[uuid.UUID] = mapped_column(Uuid, init=False, primary_key=True , nullable=False, unique=True, index=True, server_default=text("gen_random_uuid()"))
    resource: Mapped[str] = mapped_column(unique=False, nullable=False, index=True)
    input: Mapped[dict[str, Any]] = mapped_column(unique=False, nullable=False, index=False)
    flow_type: Mapped[str] = mapped_column(unique=False, nullable=False, index=True)
    flow_metadata: Mapped[dict[str, Any]] = mapped_column(unique=False, nullable=True, index=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, init=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=True, onupdate=func.now(), init=False)
    
    # task_list: Mapped[List["TaskModel"]] = relationship(back_populates='tasks', init=False)
    task_list = relationship("TaskModel", back_populates="workflow", cascade="all, delete-orphan")

    status: Mapped[str] = mapped_column(unique=False, nullable=False, index=False, default="PENDING")# Em .../stllrent_bootstrap/workflow/model/workflow.py       
    