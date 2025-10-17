from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
POWERBI_ENV_PREFIX = "CASTOR_POWERBI_"

CLIENT_APP_BASE = "https://login.microsoftonline.com"
REST_API_BASE_PATH = "https://api.powerbi.com/v1.0/myorg"


class PowerbiCertificate(BaseModel):
    """
    Supports all dict credentials formats supported by PowerBI
    https://learn.microsoft.com/en-us/python/api/msal/msal.application.confidentialclientapplication
    """

    client_assertion: Optional[str] = None
    passphrase: Optional[str] = None
    private_key: Optional[str] = None
    private_key_pfx_path: Optional[str] = None
    public_certificate: Optional[str] = None
    thumbprint: Optional[str] = None


class PowerbiCredentials(BaseSettings):
    """Class to handle PowerBI rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=POWERBI_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    client_id: str
    tenant_id: str
    secret: Optional[str] = None
    certificate: Optional[PowerbiCertificate] = None
    api_base: str = REST_API_BASE_PATH
    login_url: str = CLIENT_APP_BASE
    scopes: list[str] = [DEFAULT_SCOPE]

    @field_validator("scopes", mode="before")
    @classmethod
    def _check_scopes(cls, scopes: Optional[list[str]]) -> list[str]:
        return scopes if scopes is not None else [DEFAULT_SCOPE]

    @field_validator("login_url", mode="before")
    @classmethod
    def _check_login_url(cls, login_url: Optional[str]) -> str:
        return login_url if login_url is not None else CLIENT_APP_BASE

    @field_validator("api_base", mode="before")
    @classmethod
    def _check_api_base(cls, api_base: Optional[str]) -> str:
        return api_base if api_base is not None else REST_API_BASE_PATH
