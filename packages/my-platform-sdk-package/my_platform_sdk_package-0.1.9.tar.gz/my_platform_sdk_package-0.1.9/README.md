<h1 align="center">My sdk Python client</h1>

## Project description
Using my-sdk python package to querry data from my Flatform by using APIKey. For example , Getting user balance, creating a task, getting task result, getting statistics and history of models, checking API permission ...

To start, simply require the my-SDK and set up an instance with your W3AI API Keys.Please checking out your my Page. In the example below show you how to using the SDK.

## Installation
``` 
pip install my-platform-sdk-package
```

## Code sample

```python

from my_platform_sdk_package.http_client import HttpClient, ApiError


API_KEY = "YOUR_API_KEY"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_service.get_balance()
        print(resp)
        print(resp.status)
        print(resp.data.free_balance)

    except ApiError as e:
        print(e)

```

## Documentation for API Endpoints

All URIs are relative to *http://localhost/api/v1*

#### ApiKey


##### Retrieve an instance of the ApiKey API:

```python

from my_platform_sdk_package.http_client import HttpClient, ApiError


API_KEY = "YOUR_API_KEY"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_service
        print(resp)
        

    except ApiError as e:
        print(e)

```

##### Endpoints

Method | HTTP request | Description
------------- | ------------- | -------------
[**api_key_balance_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_balance_get) | **GET** /api-key/balance | Get Api Key Balance
[**api_key_permission_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_permission_get) | **GET** /api-key/permission | Get Api Key Permission
[**api_key_statistics_post**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_statistics_post) | **POST** /api-key/statistics | Get Api Key Statistics
[**api_key_task_histories_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_task_histories_get) | **GET** /api-key/task/histories | Get Tasks Histories
[**api_key_task_id_cancel_delete**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_task_id_cancel_delete) | **DELETE** /api-key/task/{id}/cancel | Cancel Task By Api Key
[**api_key_task_id_result_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_task_id_result_get) | **GET** /api-key/task/{id}/result | Get Task Result
[**api_key_task_post**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_task_post) | **POST** /api-key/task | Distribute Task (Api-Key)


#### ApiKeyModel


##### Retrieve an instance of the ApiKeyModel API:

```python

from my_platform_sdk_package.http_client import HttpClient, ApiError


API_KEY = "YOUR_API_KEY"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_model_service
        print(resp)

    except ApiError as e:
        print(e)

```

Method | HTTP request | Description
------------- | ------------- | -------------
[**api_key_model_id_info_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_info_get) | **GET** /api-key/model/{id}/info | Get Api Key Model Info
[**api_key_model_id_serving_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_serving_get) | **GET** /api-key/model/{id}/serving | Check Model Is Serving
[**api_key_model_id_statistics_post**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_statistics_post) | **POST** /api-key/model/{id}/statistics | Get Model Statistics
[**api_key_model_id_task_cost_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_task_cost_get) | **GET** /api-key/model/{id}/task/cost | Get cost to compute task by model api key
[**api_key_model_verify_support_platforms_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_verify_support_platforms_get) | **GET** /api-key/model/verify/support/platforms | Get List Platforms Support By Api Key

#### ApiKeyModelVerify


##### Retrieve an instance of the ApiKeyModelVerify API:

```python

from my_platform_sdk_package.http_client import HttpClient, ApiError


API_KEY = "YOUR_API_KEY"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_model_verify_service
        print(resp)

    except ApiError as e:
        print(e)

```
Method | HTTP request | Description
------------- | ------------- | -------------
[**api_key_model_id_pre_verify_post**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_pre_verify_post) | **POST** /api-key/model/{id}/pre-verify | Check Valid Source code To Verify Ai Model By Api Key
[**api_key_model_id_verify_cost_post**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_verify_cost_post) | **POST** /api-key/model/{id}/verify/cost | Calculate Cost To Verify Ai Model By Api Key
[**api_key_model_id_verify_post**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_verify_post) | **POST** /api-key/model/{id}/verify | Verify Ai Model By Api Key
[**api_key_model_id_verify_task_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_verify_task_get) | **GET** /api-key/model/{id}/verify/task | Get List Verify Model Task By Commit Hash And Status
[**api_key_model_verify_hub_task_id_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_verify_hub_task_id_get) | **GET** /api-key/model/verify/hub/task/{id} | Get Model Versioning By Hub Task Id By Api Key
[**api_key_model_verify_platform_task_id_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_verify_platform_task_id_get) | **GET** /api-key/model/verify/platform/task/{id} | Get Verify Platform Task By Id By Api Key


#### ApiKeyModelVersioning


##### Retrieve an instance of the ApiKeyModelVersioning API:

```python

from my_platform_sdk_package.http_client import HttpClient, ApiError


API_KEY = "YOUR_API_KEY"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_model_versioning_service
        print(resp)

    except ApiError as e:
        print(e)

```
Method | HTTP request | Description
------------- | ------------- | -------------
[**api_key_model_id_versioning_delete**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_delete) | **DELETE** /api-key/model/{id}/versioning | Delete Model Versioning By Commit Hash By Api Key
[**api_key_model_id_versioning_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_get) | **GET** /api-key/model/{id}/versioning | Get Current Model Versioning By Model Id By ApiKey
[**api_key_model_id_versioning_list_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_list_get) | **GET** /api-key/model/{id}/versioning/list | Get Verified List Model Versioning By Api Key
[**api_key_model_id_versioning_put**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_put) | **PUT** /api-key/model/{id}/versioning | Change Model Versioning By Commit Hash By Api Key

#### ApiKeyRepository


##### Retrieve an instance of the ApiKeyRepository API:

```python

from my_platform_sdk_package.http_client import HttpClient, ApiError


API_KEY = "YOUR_API_KEY"

if __name__ == "__main__":
    client = HttpClient(api_key=API_KEY)

    try:        
        resp = client.api_key_repository_service
        print(resp)

    except ApiError as e:
        print(e)

```
Method | HTTP request | Description
------------- | ------------- | -------------
[**api_key_repository_owner_username_repository_name_commit_history_get**](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ApiKeyRepositoryApi.md#api_key_repository_owner_username_repository_name_commit_history_get) | **GET** /api-key/repository/{ownerUsername}/{repositoryName}/commit/history | Get commit history by repository name and branch name by api key


## Documentation For Models

 - [ModelsApiKeyHistories](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsApiKeyHistories.md)
 - [ModelsApiKeyInfo](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsApiKeyInfo.md)
 - [ModelsApiKeyPackage](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsApiKeyPackage.md)
 - [ModelsCommit](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsCommit.md)
 - [ModelsCommitMeta](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsCommitMeta.md)
 - [ModelsCommitStats](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsCommitStats.md)
 - [ModelsCommitUser](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsCommitUser.md)
 - [ModelsFollow](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsFollow.md)
 - [ModelsMember](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsMember.md)
 - [ModelsModelVersioning](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsModelVersioning.md)
 - [ModelsModelVersioningGroupLite](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsModelVersioningGroupLite.md)
 - [ModelsOffer](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsOffer.md)
 - [ModelsPlatformTask](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsPlatformTask.md)
 - [ModelsQueueTask](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsQueueTask.md)
 - [ModelsRepoCommit](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsRepoCommit.md)
 - [ModelsUser](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsUser.md)
 - [ModelsWallet](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsWallet.md)
 - [ModelsWalletWithAddress](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ModelsWalletWithAddress.md)
 - [RequestCalculateCostToVerifyAiModelRequest](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/RequestCalculateCostToVerifyAiModelRequest.md)
 - [RequestCheckValidToVerifyAiModelRequest](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/RequestCheckValidToVerifyAiModelRequest.md)
 - [RequestDistributeTaskRequest](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/RequestDistributeTaskRequest.md)
 - [RequestGetApiKeyStatisticsByModelIdRequest](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/RequestGetApiKeyStatisticsByModelIdRequest.md)
 - [RequestVerifyAiModelRequest](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/RequestVerifyAiModelRequest.md)
 - [ResponseApiKeyHistoryListData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseApiKeyHistoryListData.md)
 - [ResponseApiKeyHistoryListResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseApiKeyHistoryListResponse.md)
 - [ResponseApiKeyInfoResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseApiKeyInfoResponse.md)
 - [ResponseCheckModelIsServingData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseCheckModelIsServingData.md)
 - [ResponseCheckModelIsServingResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseCheckModelIsServingResponse.md)
 - [ResponseCheckValidToVerifyAiModelData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseCheckValidToVerifyAiModelData.md)
 - [ResponseCheckValidToVerifyAiModelResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseCheckValidToVerifyAiModelResponse.md)
 - [ResponseDistributeTaskResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseDistributeTaskResponse.md)
 - [ResponseErrorResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseErrorResponse.md)
 - [ResponseEstimateCostData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseEstimateCostData.md)
 - [ResponseEstimateCostResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseEstimateCostResponse.md)
 - [ResponseFailResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseFailResponse.md)
 - [ResponseGetApiKeyPermissionData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetApiKeyPermissionData.md)
 - [ResponseGetApiKeyPermissionResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetApiKeyPermissionResponse.md)
 - [ResponseGetCommitHistoryData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetCommitHistoryData.md)
 - [ResponseGetCommitHistoryResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetCommitHistoryResponse.md)
 - [ResponseGetListModelVersioningLiteResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetListModelVersioningLiteResponse.md)
 - [ResponseGetListModelVersioningsLiteData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetListModelVersioningsLiteData.md)
 - [ResponseGetListPlatformSupportResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetListPlatformSupportResponse.md)
 - [ResponseGetTaskResultData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetTaskResultData.md)
 - [ResponseGetTaskResultResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetTaskResultResponse.md)
 - [ResponseGetTaskStatisticsData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetTaskStatisticsData.md)
 - [ResponseGetTaskStatisticsResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseGetTaskStatisticsResponse.md)
 - [ResponseModelVersioningGroupLiteListData](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseModelVersioningGroupLiteListData.md)
 - [ResponseModelVersioningGroupLiteListResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseModelVersioningGroupLiteListResponse.md)
 - [ResponseModelVersioningGroupLiteResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseModelVersioningGroupLiteResponse.md)
 - [ResponseModelVersioningResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseModelVersioningResponse.md)
 - [ResponseQueueTaskResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseQueueTaskResponse.md)
 - [ResponseResult](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseResult.md)
 - [ResponseSuccessResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseSuccessResponse.md)
 - [ResponseVerifyAiModelResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseVerifyAiModelResponse.md)
 - [ResponseWalletWithAddressResponse](https://github.com/thinhtruongnguyen/python-my-sdk/blob/main/python-openapi-generator-cli/aioz_api_client/docs/ResponseWalletWithAddressResponse.md)


<a id="documentation-for-authorization"></a>
## Documentation For Authorization


Authentication schemes defined for the API:
<a id="BearerAuth"></a>
### BearerAuth

- **Type**: API key
- **API key parameter name**: Authorization
- **Location**: HTTP header


## Author

support@swagger.io


