from typing import List, Tuple
from kombu import Queue, Exchange
from .brokers import RabbitMQModel

def create_queues_from_models(broker_models: List[RabbitMQModel]) -> Tuple[Queue, ...]:
    """
    Fábrica que recebe uma lista de RabbitMQModel e gera a tupla de
    objetos kombu.Queue para a fila principal e sua respectiva DLQ.
    """
    all_queues = []
    for broker in broker_models:
        # --- Cria a Fila Principal ---
        main_queue = Queue(
            broker.queue,
            Exchange(broker.exchange, type=broker.exchange_type),
            routing_key=broker.routing_key,
            queue_arguments={
                'x-dead-letter-exchange': broker.dl_exchange,
                'x-dead-letter-routing-key': broker.dl_routing_key
            }
        )
        all_queues.append(main_queue)

        # --- Cria a Fila de Dead Letter (DLQ) ---
        dl_queue = Queue(
            broker.dl_queue,
            Exchange(broker.dl_exchange, type=broker.exchange_type),
            routing_key=broker.dl_routing_key
        )
        all_queues.append(dl_queue)

    return tuple(all_queues)