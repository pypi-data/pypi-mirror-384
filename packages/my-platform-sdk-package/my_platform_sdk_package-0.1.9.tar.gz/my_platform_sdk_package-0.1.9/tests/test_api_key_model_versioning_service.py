import pytest
from my_platform_sdk_package.http_client import ApiError
from config import  BASE_URL, MODEL_ID,LIMIT, OFFSET, TASK_ID, FROM, TO, COMMIT_HASH, VERIFY_STATUS


@pytest.mark.parametrize("model_id, offset, limit, verify_status, expect_success", [
    ("7332d265-171e-4055-9f2f-af51a52a82c4", 0, 5, "verified", True),
    ("7332d265-171e-4055-9f2f-af51a52a82c4", -9, 5, "verified", False),
])
def test_get_list_verified_model_versioning(api_key_model_versioning_service, model_id, offset, limit, verify_status, expect_success):
    try:
        resp = api_key_model_versioning_service.api_key_model_id_versioning_list_get(
            model_id, offset, limit, verify_status
        )
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
        else:
            pytest.fail("Expected ApiError but got success response")
    except ApiError as e:
        if expect_success:
            pytest.fail(f"Unexpected ApiError: {e}")
        else:
            assert "offset" in str(e).lower(), f"Expected offset validation error, got {e}"



@pytest.mark.parametrize("model_id, commit_hash, expect_success", [
    (MODEL_ID, COMMIT_HASH, False),
])
def test_change_current_model_versioning(api_key_model_versioning_service, model_id, commit_hash, expect_success):
    try:
        resp = api_key_model_versioning_service.api_key_model_id_versioning_put(
            model_id, commit_hash
        )
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
    except ApiError as e:
        assert "verified model versioning not exist" in str(e).lower(), \
                f"Expected 'verified model versioning not exist' in error, got {e}"


