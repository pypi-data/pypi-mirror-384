from aioz_api_client.models.response_success_response import ResponseSuccessResponse
from aioz_api_client.models.response_get_list_model_versioning_lite_response import ResponseGetListModelVersioningLiteResponse
from aioz_api_client.models.response_model_versioning_group_lite_response import ResponseModelVersioningGroupLiteResponse

class ApiKeyModelVersioningService:
    def __init__(self, api):
        self.api = api
        
    def delete_model_versioning_by_model_id_and_commit_hash(self, model_id: str, commit_hash: str)->ResponseSuccessResponse:
        path = f"api-key/model/{model_id}/versioning"
        params = {
            "commitHash": commit_hash
        }
        resp = self.api.request("DELETE", path, query_params=params,response_model=ResponseSuccessResponse)
        return resp


    def change_current_model_versioning_by_model_id_and_commit_hash(self, model_id: str, commit_hash: str)->ResponseSuccessResponse:
        path = f"api-key/model/{model_id}/versioning"
        params = {
            "commitHash": commit_hash
        }
        resp = self.api.request("PUT", path, query_params=params,response_model=ResponseSuccessResponse)
        return resp


    def get_list_verified_model_versioning(self, model_id: str, offset: int, limit: int, verify_status: str)->ResponseGetListModelVersioningLiteResponse:
        path = (
        f"api-key/model/{model_id}/versioning/list"
        f"?offset={offset}&limit={limit}&verifyStatus={verify_status}"
    )
        resp = self.api.request("GET", path,response_model=ResponseGetListModelVersioningLiteResponse)
        return resp

    def get_current_model_versioning_by_model_id(self, model_id: str)->ResponseModelVersioningGroupLiteResponse:
        path = f"api-key/model/{model_id}/versioning"
        resp = self.api.request("GET", path,response_model=ResponseModelVersioningGroupLiteResponse)
        return resp
