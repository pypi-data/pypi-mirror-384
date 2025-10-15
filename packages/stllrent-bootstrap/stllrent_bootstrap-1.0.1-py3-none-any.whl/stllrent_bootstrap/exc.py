from celery.exceptions import ImproperlyConfigured

class ConfigurationError(Exception):
    pass

class RequestError(Exception):
    pass

class ProjectStandardException(ImproperlyConfigured):
    """Erro relacionado a problemas no padrão de projeto da aplicação que utiliza este módulo."""
    def __init__(self, requirements, message="Failure identified in the definition of the project standard."):
        self.requirements = requirements
        super().__init__(f"{message} REQUIREMENTS: {self.requirements}")

class GatewayTimeoutException(RequestError):
    """Erro relacionado a problemas de disponibilidade do serviço a ser consumido."""
    def __init__(self, message="Failure request external service - Gateway Timeout."):
        super().__init__(f"{message}")

class NetworkException(RequestError):
    """Erro relacionado a problemas de comunicação com o serviço a ser consumido."""
    def __init__(self, message="Failure request external service - Newtwork Error."):
        super().__init__(f"{message}")

class BusinessException(RequestError):
    """Erro relacionado a problemas de disponibilidade do serviço a ser consumido."""
    def __init__(self, message="Business Exception"):
        super().__init__(f"{message}")