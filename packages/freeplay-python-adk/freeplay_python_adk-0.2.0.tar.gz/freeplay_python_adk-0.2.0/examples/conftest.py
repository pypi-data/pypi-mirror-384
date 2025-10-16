import pytest


@pytest.fixture(scope="session", autouse=True)
def vcr_config():
    return {
        "filter_headers": [
            "authorization",
            "x-api-key",
            "x-goog-api-key",
            "x-auth-token",
            "cookie",
            "set-cookie",
            "x-session-token",
            "bearer",
            "api-key",
            "secret",
            "token",
            "password",
            "x-secret",
            "x-token",
        ],
        "ignore_hosts": ["localhost"],
    }
