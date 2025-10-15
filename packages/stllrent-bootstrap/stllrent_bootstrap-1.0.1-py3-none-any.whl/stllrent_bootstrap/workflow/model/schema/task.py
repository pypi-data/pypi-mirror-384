from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class TaskCreate(BaseModel):
    """
    Schema para criar uma nova Task.
    O cliente envia apenas os dados necessários para a criação.
    """
    task_id: UUID = Field(..., description="ID único da tarefa dentro do workflow (gerado automaticamente pelo Celery).")
    task_name: Optional[str] = Field(None, description="Nome da task. Em alguns tipos de workfloy, o Celery não define o nome da task automaticamente.")
    task_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais opcionais para a tarefa.")

class TaskResponse(BaseModel):
    """
    Schema para retornar uma Task.
    Inclui todos os campos do banco de dados que podem ser expostos.
    """
    task_id: UUID = Field(..., description="ID único da tarefa dentro do workflow (gerado automaticamente pelo Celery).")
    workflow_id: UUID = Field(..., description="OID do workflow ao qual esta tarefa pertence.")
    task_name: Optional[str] = Field(None, description="Nome da tarefa.")
    task_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais da tarefa.")
    task_output: Optional[Dict[str, Any]] = Field(None, description="Dados gerados na saída do Worker.")
    status: str = Field(..., description="Status atual da tarefa (ex: PENDING, RUNNING, COMPLETED, FAILED).")
    created_at: datetime = Field(..., description="Data e hora de criação da tarefa.")
    updated_at: Optional[datetime] = Field(None, description="Última data e hora de atualização da tarefa.")

    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    """
    Schema para atualizar campos específicos de uma Task.
    Todos os campos são opcionais, permitindo atualizações parciais.
    """
    task_name: Optional[str] = Field(None, description="Novo nome para a tarefa.")
    task_output: Optional[Dict[str, Any]] = Field(None, description="Dados gerados na saída do Worker.")
    status: Optional[str] = Field(None, description="Novo status para a tarefa.")


