from pydantic import BaseModel, Field, model_validator
from typing import Optional

class RabbitMQModel(BaseModel):
    """
    Define os nomes da estrutura de um Broker RabbitMQ no contexto de execução do Celery
    """
    queue: str = Field(...)
    exchange: Optional[str] = Field(default=None)
    exchange_type: Optional[str] = Field(default='direct')
    routing_key: Optional[str] = Field(default=None)
    dl_prefix: str = Field(default="dl_") 
    dl_queue: Optional[str] = Field(default=None)
    dl_exchange: Optional[str] = Field(default=None)
    dl_routing_key: Optional[str] = Field(default=None)

    @model_validator(mode='after')
    def set_defaults(self) -> 'RabbitMQModel':
        """
        Popula os campos se eles não forem fornecidos.
        """
        if self.exchange is None:
            self.exchange = self.queue
        if self.routing_key is None:
            self.routing_key = self.queue
        if self.dl_queue is None:
            self.dl_queue = self.__dl_object_name(self.queue)
        if self.dl_exchange is None:
            self.dl_exchange = self.__dl_object_name(self.exchange)
        if self.dl_routing_key is None:
            self.dl_routing_key = self.__dl_object_name(self.queue)
        return self

    def __dl_object_name(self, name: str) -> str:
        """
        Gera o nome de um objeto Dead Letter.
        """
        return self.dl_prefix + name