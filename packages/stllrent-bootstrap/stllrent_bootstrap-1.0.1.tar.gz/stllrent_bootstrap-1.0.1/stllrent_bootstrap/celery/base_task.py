from celery import Task
from celery.exceptions import Reject, Retry
from celery.utils.log import get_task_logger
from ..workflow.config.flow_config import settings as flow_settings
import requests
from ..workflow.model.schema.task import TaskUpdate
import json


log = get_task_logger(__name__)

class BootstrapTask(Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        """
        Sobrescreve o método de execução da tarefa para interceptar a exceção 'Reject'
        e logar a ação de envio para a DLQ.
        """
        try:
            # Executa a lógica principal da sua tarefa (o código dentro de @celery_app.task)
            return super().__call__(*args, **kwargs)
        
        except Reject as rej_exc:
            queue_name = self.request.delivery_info.get('routing_key', 'UNKNOWN_QUEUE')
            log.error(
                f"[SEND_MESSAGE_TO_DLQ] [{queue_name}] [{self.request.id}]"
            )
            failure_output = {
                "exception_type": type(rej_exc).__name__,
                "exception_message": str(rej_exc)
            }
            self._update_monitoring_service(self.request.id, status="REJECTED", output=failure_output)
            
            # É CRUCIAL relançar a exceção para que o Celery continue
            # o processo de rejeitar a mensagem no broker.
            raise
        except Retry as re_exc:
            log.critical(f"[TASK_RETRY] {self.request.id}. Caused by {re_exc!r}")
            failure_output = {
                "exception_type": type(re_exc).__name__,
                "exception_message": str(re_exc)
            }
            self._update_monitoring_service(self.request.id, status="RETRY", output=failure_output)
            raise
            
        except Exception as exc:
            # Para qualquer outra exceção não tratada, apenas a relance para que
            # o Celery a processe como uma falha normal (e acione o on_failure).
            log.critical(f"Task ID [{self.request.id}]: Exceção não tratada escapou! {exc!r}", exc_info=False)
            failure_output = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)
            }
            self._update_monitoring_service(self.request.id, status="FAILURE", output=failure_output)
            raise

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handler chamado quando a tarefa falha.
        'exc' é a exceção que causou a falha.
        'einfo' é um objeto ExceptionInfo com o traceback completo.
        """
        log.error(f"TASK ID [{task_id}] entrou no estado FAILURE. Exceção: {exc!r}")
        
        # Prepara os metadados da falha para o serviço de monitoramento.
        failure_output = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": einfo.traceback,
        }
        self._update_monitoring_service(task_id, status="FAILURE", output=failure_output)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Handler chamado após a execução bem-sucedida de uma tarefa.
        'retval' contém o valor de retorno da tarefa.
        """
        # O 'retval' é o resultado da task.
        output_data = retval

        # Se o resultado for uma exceção,
        # converta-o para sua representação em string para evitar erros de serialização.
        if isinstance(retval, Exception):
            output_data = str(retval)
        if isinstance(retval, str):
            try:
                output_data = json.loads(retval)
            except json.JSONDecodeError as jse:
                log.debug(f"retval is not JSON serializeble: {jse!r}")
                log.debug(f"retval typing: {type(retval)}")
                pass
        
        # O status aqui será 'SUCCESS'.
        self._update_monitoring_service(task_id, status=status, output={"output": output_data})

    def _update_monitoring_service(self, task_id, status, output):
        """
        Centraliza a lógica de atualização de status para o serviço de Workflow Monitoring.
        """
        try:
            log.info(f"Task [{task_id}] finalizada com status [{status}]. Atualizando serviço de monitoramento.")
            
            task_update_schema = TaskUpdate(
                task_name=self.name,
                status=status,
                task_output=output
            )
            
            update_url = f"{flow_settings.FLOWMON_URL.unicode_string().rstrip('/')}/{flow_settings.FLOWMON_API_PRIMARY_PATH}/task/{task_id}"
            response = requests.patch(update_url, json=task_update_schema.model_dump(mode='json'))
            response.raise_for_status() # Lança uma exceção para respostas de erro (4xx ou 5xx)
            log.debug(f"Serviço de monitoramento atualizado com sucesso para a task [{task_id}].")
        except requests.RequestException as e:
            log.error(f"Falha ao atualizar o serviço de monitoramento para a task [{task_id}]: {e!r}", exc_info=True)
        except Exception as e:
            log.error(f"Erro inesperado durante a atualização do monitoramento para a task [{task_id}]: {e!r}", exc_info=True)
