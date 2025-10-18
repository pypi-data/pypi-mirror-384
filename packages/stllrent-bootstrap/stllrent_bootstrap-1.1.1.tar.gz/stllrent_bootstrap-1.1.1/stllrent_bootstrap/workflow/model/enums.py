from enum import Enum

class TaskStatus(str, Enum):
    """Define os possíveis status de uma Task."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    REJECTED = "REJECTED"


class WorkflowStatus(str, Enum):
    """Define os possíveis status de um Workflow."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"