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

    except ApiError as e:
        print(e)

```

## Documentation for API Endpoints

All URIs are relative to *http://localhost/api/v1*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*ApiKeyApi* | [**api_key_balance_get**](python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_balance_get) | **GET** /api-key/balance | Get Api Key Balance
*ApiKeyApi* | [**api_key_permission_get**](python-openapi-generator-cli/aioz_api_client/docs/ApiKeyApi.md#api_key_permission_get) | **GET** /api-key/permission | Get Api Key Permission
*ApiKeyApi* | [**api_key_statistics_post**](aioz_api_client/docs/ApiKeyApi.md#api_key_statistics_post) | **POST** /api-key/statistics | Get Api Key Statistics
*ApiKeyApi* | [**api_key_task_histories_get**](aioz_api_client/docs/ApiKeyApi.md#api_key_task_histories_get) | **GET** /api-key/task/histories | Get Tasks Histories
*ApiKeyApi* | [**api_key_task_id_cancel_delete**](aioz_api_client/docs/ApiKeyApi.md#api_key_task_id_cancel_delete) | **DELETE** /api-key/task/{id}/cancel | Cancel Task By Api Key
*ApiKeyApi* | [**api_key_task_id_result_get**](aioz_api_client/docs/ApiKeyApi.md#api_key_task_id_result_get) | **GET** /api-key/task/{id}/result | Get Task Result
*ApiKeyApi* | [**api_key_task_post**](aioz_api_client/docs/ApiKeyApi.md#api_key_task_post) | **POST** /api-key/task | Distribute Task (Api-Key)
*ApiKeyModelApi* | [**api_key_model_id_info_get**](aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_info_get) | **GET** /api-key/model/{id}/info | Get Api Key Model Info
*ApiKeyModelApi* | [**api_key_model_id_serving_get**](aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_serving_get) | **GET** /api-key/model/{id}/serving | Check Model Is Serving
*ApiKeyModelApi* | [**api_key_model_id_statistics_post**](aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_statistics_post) | **POST** /api-key/model/{id}/statistics | Get Model Statistics
*ApiKeyModelApi* | [**api_key_model_id_task_cost_get**](aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_id_task_cost_get) | **GET** /api-key/model/{id}/task/cost | Get cost to compute task by model api key
*ApiKeyModelApi* | [**api_key_model_verify_support_platforms_get**](aioz_api_client/docs/ApiKeyModelApi.md#api_key_model_verify_support_platforms_get) | **GET** /api-key/model/verify/support/platforms | Get List Platforms Support By Api Key
*ApiKeyModelVerifyApi* | [**api_key_model_id_pre_verify_post**](aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_pre_verify_post) | **POST** /api-key/model/{id}/pre-verify | Check Valid Source code To Verify Ai Model By Api Key
*ApiKeyModelVerifyApi* | [**api_key_model_id_verify_cost_post**](aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_verify_cost_post) | **POST** /api-key/model/{id}/verify/cost | Calculate Cost To Verify Ai Model By Api Key
*ApiKeyModelVerifyApi* | [**api_key_model_id_verify_post**](aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_verify_post) | **POST** /api-key/model/{id}/verify | Verify Ai Model By Api Key
*ApiKeyModelVerifyApi* | [**api_key_model_id_verify_task_get**](aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_id_verify_task_get) | **GET** /api-key/model/{id}/verify/task | Get List Verify Model Task By Commit Hash And Status
*ApiKeyModelVerifyApi* | [**api_key_model_verify_hub_task_id_get**](aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_verify_hub_task_id_get) | **GET** /api-key/model/verify/hub/task/{id} | Get Model Versioning By Hub Task Id By Api Key
*ApiKeyModelVerifyApi* | [**api_key_model_verify_platform_task_id_get**](aioz_api_client/docs/ApiKeyModelVerifyApi.md#api_key_model_verify_platform_task_id_get) | **GET** /api-key/model/verify/platform/task/{id} | Get Verify Platform Task By Id By Api Key
*ApiKeyModelVersioningApi* | [**api_key_model_id_versioning_delete**](aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_delete) | **DELETE** /api-key/model/{id}/versioning | Delete Model Versioning By Commit Hash By Api Key
*ApiKeyModelVersioningApi* | [**api_key_model_id_versioning_get**](aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_get) | **GET** /api-key/model/{id}/versioning | Get Current Model Versioning By Model Id By ApiKey
*ApiKeyModelVersioningApi* | [**api_key_model_id_versioning_list_get**](aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_list_get) | **GET** /api-key/model/{id}/versioning/list | Get Verified List Model Versioning By Api Key
*ApiKeyModelVersioningApi* | [**api_key_model_id_versioning_put**](aioz_api_client/docs/ApiKeyModelVersioningApi.md#api_key_model_id_versioning_put) | **PUT** /api-key/model/{id}/versioning | Change Model Versioning By Commit Hash By Api Key
*ApiKeyRepositoryApi* | [**api_key_repository_owner_username_repository_name_commit_history_get**](aioz_api_client/docs/ApiKeyRepositoryApi.md#api_key_repository_owner_username_repository_name_commit_history_get) | **GET** /api-key/repository/{ownerUsername}/{repositoryName}/commit/history | Get commit history by repository name and branch name by api key


## Documentation For Models

 - [ModelsApiKeyHistories](aioz_api_client/docs/ModelsApiKeyHistories.md)
 - [ModelsApiKeyInfo](aioz_api_client/docs/ModelsApiKeyInfo.md)
 - [ModelsApiKeyPackage](aioz_api_client/docs/ModelsApiKeyPackage.md)
 - [ModelsCommit](aioz_api_client/docs/ModelsCommit.md)
 - [ModelsCommitMeta](aioz_api_client/docs/ModelsCommitMeta.md)
 - [ModelsCommitStats](aioz_api_client/docs/ModelsCommitStats.md)
 - [ModelsCommitUser](aioz_api_client/docs/ModelsCommitUser.md)
 - [ModelsFollow](aioz_api_client/docs/ModelsFollow.md)
 - [ModelsMember](aioz_api_client/docs/ModelsMember.md)
 - [ModelsModelVersioning](aioz_api_client/docs/ModelsModelVersioning.md)
 - [ModelsModelVersioningGroupLite](aioz_api_client/docs/ModelsModelVersioningGroupLite.md)
 - [ModelsOffer](aioz_api_client/docs/ModelsOffer.md)
 - [ModelsPlatformTask](aioz_api_client/docs/ModelsPlatformTask.md)
 - [ModelsQueueTask](aioz_api_client/docs/ModelsQueueTask.md)
 - [ModelsRepoCommit](aioz_api_client/docs/ModelsRepoCommit.md)
 - [ModelsUser](aioz_api_client/docs/ModelsUser.md)
 - [ModelsWallet](aioz_api_client/docs/ModelsWallet.md)
 - [ModelsWalletWithAddress](aioz_api_client/docs/ModelsWalletWithAddress.md)
 - [RequestCalculateCostToVerifyAiModelRequest](aioz_api_client/docs/RequestCalculateCostToVerifyAiModelRequest.md)
 - [RequestCheckValidToVerifyAiModelRequest](aioz_api_client/docs/RequestCheckValidToVerifyAiModelRequest.md)
 - [RequestDistributeTaskRequest](aioz_api_client/docs/RequestDistributeTaskRequest.md)
 - [RequestGetApiKeyStatisticsByModelIdRequest](aioz_api_client/docs/RequestGetApiKeyStatisticsByModelIdRequest.md)
 - [RequestVerifyAiModelRequest](aioz_api_client/docs/RequestVerifyAiModelRequest.md)
 - [ResponseApiKeyHistoryListData](aioz_api_client/docs/ResponseApiKeyHistoryListData.md)
 - [ResponseApiKeyHistoryListResponse](aioz_api_client/docs/ResponseApiKeyHistoryListResponse.md)
 - [ResponseApiKeyInfoResponse](aioz_api_client/docs/ResponseApiKeyInfoResponse.md)
 - [ResponseCheckModelIsServingData](aioz_api_client/docs/ResponseCheckModelIsServingData.md)
 - [ResponseCheckModelIsServingResponse](aioz_api_client/docs/ResponseCheckModelIsServingResponse.md)
 - [ResponseCheckValidToVerifyAiModelData](aioz_api_client/docs/ResponseCheckValidToVerifyAiModelData.md)
 - [ResponseCheckValidToVerifyAiModelResponse](aioz_api_client/docs/ResponseCheckValidToVerifyAiModelResponse.md)
 - [ResponseDistributeTaskResponse](aioz_api_client/docs/ResponseDistributeTaskResponse.md)
 - [ResponseErrorResponse](aioz_api_client/docs/ResponseErrorResponse.md)
 - [ResponseEstimateCostData](aioz_api_client/docs/ResponseEstimateCostData.md)
 - [ResponseEstimateCostResponse](aioz_api_client/docs/ResponseEstimateCostResponse.md)
 - [ResponseFailResponse](aioz_api_client/docs/ResponseFailResponse.md)
 - [ResponseGetApiKeyPermissionData](aioz_api_client/docs/ResponseGetApiKeyPermissionData.md)
 - [ResponseGetApiKeyPermissionResponse](aioz_api_client/docs/ResponseGetApiKeyPermissionResponse.md)
 - [ResponseGetCommitHistoryData](aioz_api_client/docs/ResponseGetCommitHistoryData.md)
 - [ResponseGetCommitHistoryResponse](aioz_api_client/docs/ResponseGetCommitHistoryResponse.md)
 - [ResponseGetListModelVersioningLiteResponse](aioz_api_client/docs/ResponseGetListModelVersioningLiteResponse.md)
 - [ResponseGetListModelVersioningsLiteData](aioz_api_client/docs/ResponseGetListModelVersioningsLiteData.md)
 - [ResponseGetListPlatformSupportResponse](aioz_api_client/docs/ResponseGetListPlatformSupportResponse.md)
 - [ResponseGetTaskResultData](aioz_api_client/docs/ResponseGetTaskResultData.md)
 - [ResponseGetTaskResultResponse](aioz_api_client/docs/ResponseGetTaskResultResponse.md)
 - [ResponseGetTaskStatisticsData](aioz_api_client/docs/ResponseGetTaskStatisticsData.md)
 - [ResponseGetTaskStatisticsResponse](aioz_api_client/docs/ResponseGetTaskStatisticsResponse.md)
 - [ResponseModelVersioningGroupLiteListData](aioz_api_client/docs/ResponseModelVersioningGroupLiteListData.md)
 - [ResponseModelVersioningGroupLiteListResponse](aioz_api_client/docs/ResponseModelVersioningGroupLiteListResponse.md)
 - [ResponseModelVersioningGroupLiteResponse](aioz_api_client/docs/ResponseModelVersioningGroupLiteResponse.md)
 - [ResponseModelVersioningResponse](aioz_api_client/docs/ResponseModelVersioningResponse.md)
 - [ResponseQueueTaskResponse](aioz_api_client/docs/ResponseQueueTaskResponse.md)
 - [ResponseResult](aioz_api_client/docs/ResponseResult.md)
 - [ResponseSuccessResponse](aioz_api_client/docs/ResponseSuccessResponse.md)
 - [ResponseVerifyAiModelResponse](aioz_api_client/docs/ResponseVerifyAiModelResponse.md)
 - [ResponseWalletWithAddressResponse](aioz_api_client/docs/ResponseWalletWithAddressResponse.md)


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


