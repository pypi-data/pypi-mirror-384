from celery import bootsteps
import logging

# Use o logger padrão do Celery para que as mensagens apareçam nos logs do worker
log = logging.getLogger(__name__)

class SetupQueuesBootstep(bootsteps.StartStopStep):
    """
    Bootstep do worker que garante que TODAS as filas definidas na configuração
    sejam declaradas no RabbitMQ na inicialização.
    """
    requires = {'celery.worker.components:Pool'}

    def start(self, worker):
        self.app = worker.app
        queues = self.app.conf.get('task_queues', [])

        log.info(f"Encontradas {len(queues)} filas para declarar na configuração.")
        if not queues:
            log.warning("Nenhuma 'task_queues' encontrada na configuração do Celery.")
            return

        try:
            with worker.app.pool.acquire() as conn:
                log.info("Conexão com o broker adquirida.")
                for queue in queues:
                    log.info(f"Declarando fila: {queue.name}")
                    # A declaração é idempotente: cria se não existir, ou valida se já existir.
                    queue.bind(conn).declare()
                log.info("Todas as filas foram declaradas com sucesso.")
        except Exception as e:
            log.error(f"Ocorreu um erro durante a declaração das filas: {e}", exc_info=True)
