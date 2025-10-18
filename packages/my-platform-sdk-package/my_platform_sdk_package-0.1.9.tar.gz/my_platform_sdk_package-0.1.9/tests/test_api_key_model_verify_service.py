import pytest
from config import TASK_ID
from my_platform_sdk_package.http_client import ApiError
from aioz_api_client.models.request_check_valid_to_verify_ai_model_request import RequestCheckValidToVerifyAiModelRequest
from config import API_KEY, BASE_URL, MODEL_ID,LIMIT, OFFSET, TASK_ID, FROM, TO, COMMIT_HASH, VERIFY_STATUS, PLATFORMS
from aioz_api_client.models.request_verify_ai_model_request import RequestVerifyAiModelRequest
from aioz_api_client.models.request_calculate_cost_to_verify_ai_model_request import RequestCalculateCostToVerifyAiModelRequest


@pytest.mark.parametrize(
    "model_id, commit_hash, platforms, expect_success",
    [
        (MODEL_ID, COMMIT_HASH, PLATFORMS, False),
    ]
)
def test_calculate_cost_to_verify_model(api_key_model_verify_service, model_id, commit_hash, platforms, expect_success):
    request_obj = RequestCalculateCostToVerifyAiModelRequest(
        commit_hash=commit_hash,
        platforms=platforms
    )
    try:
        resp = api_key_model_verify_service.api_key_model_id_verify_cost_post(model_id, request_obj)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")
        else:
            assert "please set up model setting" in str(e).lower(), f"Expected setup error, got {e}"



@pytest.mark.parametrize(
    "model_id, commit_hash, platforms, expect_success",
    [
        (MODEL_ID, COMMIT_HASH, PLATFORMS, True),
    ]
)
def test_verify_model(api_key_model_verify_service, model_id, commit_hash, platforms, expect_success):
    request_obj = RequestVerifyAiModelRequest(
        commit_hash=commit_hash,
        platforms=platforms
    )
    try:
        resp= api_key_model_verify_service.api_key_model_id_verify_post(model_id, request_obj)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
       if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")


@pytest.mark.parametrize(
    "model_id, commit_hash, platforms, expect_success",
    [
        (MODEL_ID, COMMIT_HASH, PLATFORMS, False),
    ]
)
def test_pre_check_to_verify_model(api_key_model_verify_service, model_id, commit_hash, platforms, expect_success):
    request_obj = RequestCheckValidToVerifyAiModelRequest(
        commit_hash=commit_hash,
        platforms=platforms
    )
    try:
        resp = api_key_model_verify_service.api_key_model_id_pre_verify_post(model_id, request_obj)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")



@pytest.mark.parametrize("task_id, expect_success", [(TASK_ID, False)])
def test_get_verify_platform_task_by_id(api_key_model_verify_service, task_id, expect_success):
    try:
        resp = api_key_model_verify_service.api_key_model_verify_platform_task_id_get(task_id)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")


@pytest.mark.parametrize("task_id, expect_success", [(TASK_ID, False)])
def test_get_model_versioning_by_task_id(api_key_model_verify_service, task_id, expect_success):
    try:
        resp = api_key_model_verify_service.api_key_model_verify_hub_task_id_get(task_id)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")
