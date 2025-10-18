import pytest
from my_platform_sdk_package.http_client import ApiError
from config import OWNER, REPO, PATH, SHA, PAGE, PAGE_SIZE, REPO_TYPE

@pytest.mark.parametrize(
    "owner, repo, expect_success",
    [
        (OWNER, REPO, False),
    ]
)
def test_get_commit_history(api_key_repository_service, owner, repo, expect_success):
    try:
        resp = api_key_repository_service.api_key_repository_owner_username_repository_name_commit_history_get(
            owner_username=owner,
            repository_name=repo,
            path=PATH,
            sha=SHA,
            page=PAGE,
            page_size=PAGE_SIZE,
            repo_type=REPO_TYPE,
        )
        if expect_success:
            assert resp.status == "success"
            assert resp.data is not None
    except ApiError as e:
        assert "repository not found" in str(e).lower(), \
                f"Expected 'repository not found' in error, got {e}"
