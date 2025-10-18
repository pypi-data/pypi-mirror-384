from enum import Enum
from deprecated import deprecated
 
class TaskStatus(str, Enum):
    """Define os possíveis status de uma Task."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    REJECTED = "REJECTED"
    FAILURE = deprecated("FAILURE", version='1.2.0', reason="Utilize 'REJECTED' para falhas de negócio e aguarde um status futuro para falhas de sistema.")

class WorkflowStatus(str, Enum):
    """Define os possíveis status de um Workflow."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
