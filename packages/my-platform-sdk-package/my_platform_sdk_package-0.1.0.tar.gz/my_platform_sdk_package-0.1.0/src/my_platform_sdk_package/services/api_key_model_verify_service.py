from aioz_api_client.models.request_check_valid_to_verify_ai_model_request import RequestCheckValidToVerifyAiModelRequest
from aioz_api_client.models.request_verify_ai_model_request import RequestVerifyAiModelRequest
from aioz_api_client.models.request_calculate_cost_to_verify_ai_model_request import RequestCalculateCostToVerifyAiModelRequest
from aioz_api_client.models.response_estimate_cost_response import ResponseEstimateCostResponse
from aioz_api_client.models.response_verify_ai_model_response import ResponseVerifyAiModelResponse
from aioz_api_client.models.response_check_valid_to_verify_ai_model_response import ResponseCheckValidToVerifyAiModelResponse
from aioz_api_client.models.response_model_versioning_group_lite_list_response import ResponseModelVersioningGroupLiteListResponse
from aioz_api_client.models.response_queue_task_response import ResponseQueueTaskResponse
from aioz_api_client.models.response_model_versioning_response import ResponseModelVersioningResponse

class ApiKeyModelVerifyService:
    def __init__(self, api):
        self.api = api

    def calculate_cost_to_verify_model(self, model_id: str, request: RequestCalculateCostToVerifyAiModelRequest)->ResponseEstimateCostResponse:
        path = f"api-key/model/{model_id}/verify/cost"
        resp = self.api.request("POST", path, body=request.to_dict(),response_model=ResponseEstimateCostResponse)
        return resp

    def verify_model(self, model_id: str, request: RequestVerifyAiModelRequest)->ResponseVerifyAiModelResponse:
        path = f"api-key/model/{model_id}/verify"
        resp = self.api.request("POST", path, body=request.to_dict(),response_model=ResponseVerifyAiModelResponse)
        return resp


    def pre_check_to_verify_model(self, model_id: str, request: RequestCheckValidToVerifyAiModelRequest)->ResponseCheckValidToVerifyAiModelResponse:
        path = f"api-key/model/{model_id}/pre-verify"
        resp = self.api.request("POST", path, body=request.to_dict(),response_model=ResponseCheckValidToVerifyAiModelResponse)
        return resp



    def get_list_verify_model_task_by_commit_hash_and_status(self, model_id: str, commit_hash: str, status: str)->ResponseModelVersioningGroupLiteListResponse:
        path = f"api-key/model/{model_id}/verify/task"
        params = {"commitHash": commit_hash, "verifyStatus": status}
        resp = self.api.request("GET", path, query_params=params,response_model=ResponseModelVersioningGroupLiteListResponse)
        return resp

    def get_verify_platform_task_by_id(self, task_id: str)->ResponseQueueTaskResponse:
        path = f"api-key/model/verify/platform/task/{task_id}"
        resp = self.api.request("GET", path,response_model=ResponseQueueTaskResponse)
        return resp

    def get_model_versioning_by_task_id(self, task_id: str)->ResponseModelVersioningResponse:
        path = f"api-key/model/verify/hub/task/{task_id}"
        resp = self.api.request("GET", path,response_model=ResponseModelVersioningResponse)
        return resp
