from stllrent_bootstrap.workflow.model.schema.workflow import WorkflowCreate, WorkflowResponse
from stllrent_bootstrap.workflow.config.flow_config import settings
from urllib.parse import urljoin
import requests
import json
import logging

log = logging.getLogger(__name__)

class WorkflowAPI():

    def __init__(self):
        self.__post_headers = {
            "Accept": "application/json"
        }
    
    def create(self, workflow_schem:WorkflowCreate) -> WorkflowResponse:
        try:
            data_json = workflow_schem.model_dump_json()
            log.debug(data_json)
            data_dict = json.loads(data_json)
            response = requests.post(urljoin(settings.FLOWMON_URL.unicode_string(), f"{settings.FLOWMON_API_PRIMARY_PATH}/workflow"), headers=self.__post_headers, json=data_dict)
            response_dict = json.loads(response.text)
            log.debug(response.json())
            workflow_response = WorkflowResponse.model_validate(response_dict)
            return workflow_response
        except Exception as e:
            log.error(f"WORKFLOW_MONITORING_API_ERROR: {e!r}")
            return None