import pytest
import os
from unittest.mock import patch, MagicMock

# Importar as classes de Settings (não as instâncias globais)
from stllrent_bootstrap.config.app_settings import Settings as AppSettingsClass
from stllrent_bootstrap.config.celery_settings import CelerySettings as CelerySettingsClass

# Importar a função fábrica do Flask e a instância do Celery app
from stllrent_bootstrap.app_factory import create_flask_app
from stllrent_bootstrap.celery_app_instance import celery_app as global_celery_app_instance # A instância global

# Fixture para configurar variáveis de ambiente para testes
@pytest.fixture(scope='session', autouse=True)
def set_test_env_vars():
    """
    Define variáveis de ambiente para garantir que as configurações Pydantic
    carreguem valores controlados durante os testes.
    """
    # Guardar os valores originais para restaurar depois
    original_env = os.environ.copy()

    # Variáveis de ambiente para AppSettings
    os.environ['FLASK_SECRET_KEY'] = 'test_flask_secret'
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://user:pass@testhost:5432/testdb'
    os.environ['APP_NAME'] = 'test-app'
    os.environ['APP_LOG_LEVEL'] = 'DEBUG'
    os.environ['APP_ENVIRONMENT'] = 'testing'
    os.environ['SQL_ALCHEMY_ECHO'] = 'True' # Bool em string

    # Variáveis de ambiente para CelerySettings
    os.environ['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'
    os.environ['RESULT_BACKEND_URL'] = 'testdbhost'
    os.environ['RESULT_BACKEND_PORT'] = '5432'
    os.environ['RESULT_BACKEND_USER'] = 'celeryuser'
    os.environ['RESULT_BACKEND_PASS'] = 'celerypass'
    os.environ['RESULT_BACKEND_DATABASE'] = 'celery_results_test'
    # Testar com e sem RESULT_BACKEND_URI para o model_validator
    # os.environ['RESULT_BACKEND_URI'] = 'db+postgresql://custom_uri'

    yield # Executa os testes

    # Restaura as variáveis de ambiente originais após os testes
    os.environ.clear()
    os.environ.update(original_env)

# Fixture para instanciar AppSettings no contexto de teste
@pytest.fixture(scope='function')
def app_settings_test():
    """Retorna uma instância de AppSettings com as variáveis de ambiente de teste."""
    # Recarrega a instância para cada teste para isolamento
    return AppSettingsClass()

# Fixture para instanciar CelerySettings no contexto de teste
@pytest.fixture(scope='function')
def celery_settings_test():
    """Retorna uma instância de CelerySettings com as variáveis de ambiente de teste."""
    # Recarrega a instância para cada teste para isolamento
    return CelerySettingsClass()

# Fixture para uma aplicação Flask de teste
@pytest.fixture(scope='function')
def flask_app_test():
    """
    Cria uma instância de aplicação Flask configurada para testes.
    Usa um patch para o logger para evitar saída de log durante os testes.
    """
    with patch('stllrent_bootstrap.utils.app_logger.setup_logging', MagicMock()):
        # Para garantir que a instância do Flask não afete testes de Celery,
        # podemos resetar certas coisas ou inicializar um app limpo.
        app = create_flask_app()
        app.config['TESTING'] = True # Modo de teste para Flask
        # Se você tiver um banco de dados de teste, configure-o aqui
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
        # with app.app_context():
        #     db.create_all() # Crie tabelas para testes
        yield app
        # Teardown de recursos de DB ou outros específicos do Flask
        # with app.app_context():
        #     db.drop_all()

# Fixture para a instância global do Celery app (para testes de Celery)
@pytest.fixture(scope='function')
def celery_app_test():
    """
    Retorna a instância global do Celery app, configurada para testes.
    Reinicia o Celery de forma limpa para cada teste.
    """
    # Embora `global_celery_app_instance` seja uma singleton,
    # `.control.ping()` ou `.start(argv=['celery', 'worker', ...])`
    # podem ser usados em testes de integração com workers reais (complexo).
    # Para testes unitários de configuração, basta a instância configurada.
    
    # Para garantir isolamento entre testes, podemos resetar a configuração
    # ou testar um Celery app recém-configurado.
    
    # Configurar o Celery para usar um broker/backend de teste, se necessário.
    # Por agora, ele usará as variáveis de ambiente definidas em `set_test_env_vars`.
    
    # IMPORTANTE: Se você estiver testando o comportamento do Celery (e.g., tasks being called),
    # considere usar `celery.app.task.Task.delay` com mocks, ou o `pytest-celery` que
    # fornece fixtures para workers em-memória.

    # Para testes de configuração pura, a instância carregada é suficiente.
    # Limpa as configurações de tasks para não ter side effects entre testes
    global_celery_app_instance.conf.task_routes = {}
    yield global_celery_app_instance
    global_celery_app_instance.conf.task_routes = {} # Limpa novamente