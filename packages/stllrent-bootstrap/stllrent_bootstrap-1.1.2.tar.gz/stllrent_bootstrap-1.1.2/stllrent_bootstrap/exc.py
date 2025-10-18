from celery.exceptions import ImproperlyConfigured

class ConfigurationError(Exception):
    pass

class RequestError(Exception):
    
    def __init__(self, message: str, exc: Exception = None):
        self.message = message
        self.exc = exc
        
        output = self.message
        output_exc = ""
        if exc:
            output_exc = " " + self.__extract_details(exc)
        output = output + output_exc
        super().__init__(output)

    def __extract_details(self, exc: Exception) -> str:
        output = str(exc)
        if hasattr(exc, "response"):
            output = f"{output} \n Response: {exc.response.content.decode('utf-8')}"
        return output
    
    def __str__(self) -> str:
        return super().__str__()



class ProjectStandardException(ImproperlyConfigured):
    """Erro relacionado a problemas no padrão de projeto da aplicação que utiliza este módulo."""
    def __init__(self, requirements, message="Failure identified in the definition of the project standard."):
        self.requirements = requirements
        super().__init__(f"{message} REQUIREMENTS: {self.requirements}")

class BusinessException(RequestError):
    """Erro relacionado a problemas de disponibilidade do serviço a ser consumido."""
    def __init__(self, message="Business Exception", exc: Exception = None):
        super().__init__(message=f"{message}", exc=exc)
