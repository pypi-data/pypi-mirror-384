import json
import pytest
from my_platform_sdk_package.http_client import ApiError
from aioz_api_client.models.request_distribute_task_request import RequestDistributeTaskRequest
from config import API_KEY, BASE_URL, MODEL_ID,LIMIT, OFFSET, TASK_ID, FROM, TO

@pytest.mark.parametrize(
    "limit, offset, expect_success",
    [
        (5, 0, True),
        (5, -99, False),
    ]
)
def test_get_task_histories(api_key_service, limit, offset, expect_success):
    try:
        resp = api_key_service.api_key_task_histories_get(limit=limit, offset=offset)
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
    except ApiError as e:
        assert "Offset" in str(e), "Expected Offset validation error"

   

def test_get_balance(api_key_service):
    try:
        resp = api_key_service.api_key_balance_get()
        assert resp.status == "success"
        assert resp.data is not None
        assert hasattr(resp.data, "balance")
    except ApiError as e:
        pytest.fail(f"Unexpected APIError: {e}")



@pytest.mark.parametrize(
    "model_id, expect_success",
    [
        (MODEL_ID, False),
    ]
)
def test_create_task(api_key_service, model_id, expect_success):
    request = RequestDistributeTaskRequest(
        model_id=MODEL_ID,
        files=[
            {
                "key":"input",
                "data":"https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/1200px-Cat_August_2010-4.jpg",
                "name":"image.jpg"
            }
        ],
        input_params={}
    )

    if expect_success:
        try:
            resp = api_key_service.api_key_task_post(request)
            assert resp.status == "success"
            assert resp.data is not None
        except ApiError as e:
            pytest.fail(f"Unexpected APIError: {e}")


@pytest.mark.parametrize(
    "task_id, expect_success",
    [
        ("aea6944c-a808-4c11-b8de-557fe02d505f", False),
    ]
)
def test_get_task_result(api_key_service, task_id, expect_success):
    if expect_success:
        try:
            resp = api_key_service.api_key_task_id_result_get(task_id=task_id)
            assert resp.status == "success"
            assert resp.data is not None
        except ApiError as e:
            pytest.fail(f"Unexpected APIError: {e}")






