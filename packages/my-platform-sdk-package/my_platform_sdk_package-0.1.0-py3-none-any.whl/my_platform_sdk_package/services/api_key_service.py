from aioz_api_client.models.request_get_api_key_statistics_by_model_id_request import RequestGetApiKeyStatisticsByModelIdRequest
from aioz_api_client.models.request_distribute_task_request import RequestDistributeTaskRequest
from aioz_api_client.models.response_wallet_with_address_response import ResponseWalletWithAddressResponse
from aioz_api_client.models.response_distribute_task_response import ResponseDistributeTaskResponse
from aioz_api_client.models.response_get_task_statistics_response import ResponseGetTaskStatisticsResponse
from aioz_api_client.models.response_get_task_result_response import ResponseGetTaskResultResponse
from aioz_api_client.models.response_api_key_history_list_response import ResponseApiKeyHistoryListResponse
from aioz_api_client.models.response_get_api_key_permission_response import ResponseGetApiKeyPermissionResponse

class ApiKeyService:
    def __init__(self, api):
        self.api = api


    def get_balance(self) -> ResponseWalletWithAddressResponse:
        api_response = self.api.request(
            method="GET",
            path="api-key/balance",
            response_model=ResponseWalletWithAddressResponse
        )
        return api_response


    def create_task(self, request: RequestDistributeTaskRequest)->ResponseDistributeTaskResponse:
        path = "api-key/task"
        resp = self.api.request("POST", path, body=request.to_dict(),response_model=ResponseDistributeTaskResponse)
        return resp

    def get_api_key_statistics(self, request: RequestGetApiKeyStatisticsByModelIdRequest)->ResponseGetTaskStatisticsResponse:
        path = "api-key/statistics"
        resp = self.api.request("POST", path, body=request.to_dict(),response_model=ResponseGetTaskStatisticsResponse)
        return resp


    def get_task_result(self, task_id: str)->ResponseGetTaskResultResponse:
        path = f"api-key/task/{task_id}/result"
        resp = self.api.request("GET", path,response_model=ResponseGetTaskResultResponse)
        return resp
    

    def get_task_histories(self, limit: int, offset: int)->ResponseApiKeyHistoryListResponse:
        query_params = {
            "limit": limit,
            "offset": offset
        }
        resp = self.api.request("GET", "api-key/task/histories", query_params=query_params,response_model=ResponseApiKeyHistoryListResponse)
        return resp

    
    
    def get_api_key_permission(self)->ResponseGetApiKeyPermissionResponse:
        resp = self.api.request("GET", "api-key/permission",response_model=ResponseGetApiKeyPermissionResponse)
        return resp