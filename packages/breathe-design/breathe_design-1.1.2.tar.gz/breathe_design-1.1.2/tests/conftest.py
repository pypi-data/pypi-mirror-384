from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import httpx
from functools import lru_cache
import pytest
from unittest.mock import patch
import breathe_design.device_flow_auth
import dotenv
import logging
import sys

dotenv.load_dotenv()


class Auth0Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    service_iss: str = Field(validation_alias="AUTH0_SERVICE_ISS")
    audience: str = Field(validation_alias="AUTH0_AUDIENCE")
    client_id: str = Field(validation_alias="AUTH0_CLIENT_ID")
    client_secret: str = Field(validation_alias="AUTH0_CLIENT_SECRET")


@lru_cache
def _get_access_token() -> str:
    """Request an access token from Auth0 using the Client Secret flow

    Raises:
        RuntimeError: Raised if endpoint returns non-200

    Returns:
        str: The access token string
    """
    auth0_config = Auth0Config()
    payload = {
        "client_id": auth0_config.client_id,
        "client_secret": auth0_config.client_secret,
        "audience": auth0_config.audience,
        "grant_type": "client_credentials",
    }
    headers = {"content-type": "application/x-www-form-urlencoded"}

    resp = httpx.post(
        f"{auth0_config.service_iss}/oauth/token", data=payload, headers=headers
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Token request from Auth0 failed with code {resp.status_code}: {resp.reason_phrase}"
        )

    return resp.json()["access_token"]


@pytest.fixture
def use_m2m_auth():
    token = _get_access_token()
    with patch.object(
        breathe_design.device_flow_auth.device_auth, "get_token", return_value=token
    ) as mock_method:
        yield mock_method


@pytest.fixture(autouse=True, scope="session")
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    for module_name in [
        "breathe_design.api_interface",
        "breathe_design.cycler",
        "breathe_design.dynamic_analysis",
        "breathe_design.plots",
        "breathe_design.results",
        "breathe_design.utilities",
    ]:
        logging.getLogger(module_name).setLevel(logging.DEBUG)
