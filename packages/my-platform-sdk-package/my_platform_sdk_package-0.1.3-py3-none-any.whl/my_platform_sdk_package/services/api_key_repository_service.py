from typing import Optional
from aioz_api_client.models.response_get_commit_history_response import ResponseGetCommitHistoryResponse

class ApiKeyRepositoryService:
    def __init__(self, api):
        self.api = api

    def get_commit_history(
        self,
        owner_username: str,
        repository_name: str,
        path: Optional[str] = None,
        sha: Optional[str] = None,
        page: Optional[int] = 1,
        page_size: Optional[int] = 10,
        repo_type: Optional[str] = None
    )->ResponseGetCommitHistoryResponse:
        url_path = f"api-key/repository/{owner_username}/{repository_name}/commit/history"
        params = {}
        if path:
            params["path"] = path
        if sha:
            params["sha"] = sha
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if repo_type:
            params["repoType"] = repo_type
        resp = self.api.request("GET", url_path, query_params=params,response_model=ResponseGetCommitHistoryResponse)
        return resp
