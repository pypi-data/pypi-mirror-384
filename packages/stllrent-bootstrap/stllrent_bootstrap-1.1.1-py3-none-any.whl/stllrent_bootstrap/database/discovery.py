import importlib
import pkgutil
import logging

def load_project_models(discovery_paths: list[str]):
    """
    Dynamically discovers and imports all modules within specified package paths.

    This ensures that all SQLAlchemy models defined within these paths are
    registered with the declarative Base before any database operations
    (like `create_all`) are attempted.

    Args:
        discovery_paths: A list of dot-notation package paths to search
                         (e.g., ['my_project.models', 'shared_lib.models']).
    """
    log = logging.getLogger(__name__)
    log.info("Starting dynamic model discovery...")
    if not discovery_paths:
        log.warning("No 'MODEL_DISCOVERY_PATHS' defined in settings. Skipping dynamic model loading.")
        return

    for path in discovery_paths:
        try:
            module = importlib.import_module(path)
            log.debug(f"Searching for models in package: '{path}'")
            
            # Walk through all modules and sub-packages
            for _, name, _ in pkgutil.walk_packages(module.__path__, prefix=module.__name__ + '.'):
                importlib.import_module(name)
                log.debug(f"Successfully loaded model module: {name}")
        except ImportError:
            log.error(f"Could not find discovery path '{path}'. Please check your configuration.", exc_info=True)
    log.info("Dynamic model discovery finished.")