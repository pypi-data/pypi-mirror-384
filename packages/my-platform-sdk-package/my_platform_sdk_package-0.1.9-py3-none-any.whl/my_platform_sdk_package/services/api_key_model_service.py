from aioz_api_client.models.request_get_api_key_statistics_by_model_id_request import RequestGetApiKeyStatisticsByModelIdRequest
from aioz_api_client.models.response_get_task_statistics_response import ResponseGetTaskStatisticsResponse
from aioz_api_client.models.response_estimate_cost_response import ResponseEstimateCostResponse
from aioz_api_client.models.response_check_model_is_serving_response import ResponseCheckModelIsServingResponse
from aioz_api_client.models.response_api_key_info_response import ResponseApiKeyInfoResponse
from aioz_api_client.models.response_get_list_platform_support_response import ResponseGetListPlatformSupportResponse

class ApiKeyModelService:
    def __init__(self, api):
        self.api = api

    def api_key_model_id_statistics_post(self, model_id: str, request: RequestGetApiKeyStatisticsByModelIdRequest)->ResponseGetTaskStatisticsResponse:
        path = f"api-key/model/{model_id}/statistics"
        resp = self.api.request("POST", path, body=request.to_dict(),response_model=ResponseGetTaskStatisticsResponse)
        return resp

    
    def api_key_model_id_task_cost_get(self, model_id: str)->ResponseEstimateCostResponse:
        path = f"api-key/model/{model_id}/task/cost"
        resp = self.api.request("GET", path,response_model=ResponseEstimateCostResponse)
        return resp

    def api_key_model_id_serving_get(self, model_id: str)->ResponseCheckModelIsServingResponse:
        path = f"api-key/model/{model_id}/serving"
        resp = self.api.request("GET", path,response_model=ResponseCheckModelIsServingResponse)
        return resp
    

    def api_key_model_id_info_get(self, model_id: str)->ResponseApiKeyInfoResponse:
        path = f"api-key/model/{model_id}/info"
        resp = self.api.request("GET", path,response_model=ResponseApiKeyInfoResponse)
        return resp

    def api_key_model_verify_support_platforms_get(self)->ResponseGetListPlatformSupportResponse:
        path = "api-key/model/verify/support/platforms"
        resp = self.api.request("GET", path,response_model=ResponseGetListPlatformSupportResponse)
        return resp