import contextlib
from stllrent_bootstrap.database.manager import db_manager

@contextlib.contextmanager
def get_db_session():
    """
    Fornece uma sessão de banco de dados a partir do DatabaseManager central.
    Este método é agnóstico de contexto e funciona tanto em aplicações
    Flask quanto em workers Celery.
    """
    with db_manager.get_session() as session:
        yield session