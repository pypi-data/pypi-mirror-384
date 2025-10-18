import pytest
from my_platform_sdk_package.http_client import ApiError
from config import API_KEY, BASE_URL, MODEL_ID,LIMIT, OFFSET, TASK_ID, FROM, TO, COMMIT_HASH, VERIFY_STATUS
from aioz_api_client.models.request_get_api_key_statistics_by_model_id_request import RequestGetApiKeyStatisticsByModelIdRequest

@pytest.mark.parametrize("model_id, from_date, to_date, expect_success", [
    (MODEL_ID, FROM, TO, True)
])
def test_get_model_statistics(api_key_model_service, model_id, from_date, to_date, expect_success):
    request = RequestGetApiKeyStatisticsByModelIdRequest(var_from=from_date, to=to_date)
    try:
        resp= api_key_model_service.api_key_model_id_statistics_post(model_id, request)
        assert resp.status == "success"
        assert resp.data is not None
    except ApiError as e:
        pytest.fail(f"Unexpected APIError: {e}")
       

@pytest.mark.parametrize("model_id, expect_success", [
    (MODEL_ID, False),
])
def test_get_model_task_cost(api_key_model_service, model_id, expect_success):
    try:
        resp = api_key_model_service.api_key_model_id_task_cost_get(model_id)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")
        else:
            assert "don't have any version" in str(e).lower(), f"Expected version error, got {e}"

        
@pytest.mark.parametrize("model_id, expect_success", [
    (MODEL_ID, False)
])
def test_check_model_is_serving(api_key_model_service, model_id, expect_success):
    try:
        resp = api_key_model_service.api_key_model_id_serving_get(model_id)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")


@pytest.mark.parametrize("model_id, expect_success", [
    (MODEL_ID, True),
])
def test_get_model_info(api_key_model_service, model_id, expect_success):
    try:
        resp = api_key_model_service.api_key_model_id_info_get(model_id)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")




@pytest.mark.parametrize("expect_success", [True])
def test_get_list_platforms_support(api_key_model_service, expect_success):
    try:
        resp = api_key_model_service.api_key_model_verify_support_platforms_get()
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected APIError: {e}")

