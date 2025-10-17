from typing import Optional, Union

import msal  # type: ignore

from ....utils import BearerAuth
from .constants import Keys
from .credentials import PowerbiCertificate, PowerbiCredentials
from .endpoints import PowerBiEndpointFactory


def _get_client_credential(
    secret: Optional[str], certificate: Optional[PowerbiCertificate]
) -> Union[str, dict]:
    if secret:
        return secret
    if certificate:
        return certificate.model_dump()

    raise ValueError("Either certificate or secret must be provided.")


class PowerBiBearerAuth(BearerAuth):
    def __init__(self, credentials: PowerbiCredentials):
        self.credentials = credentials
        endpoint_factory = PowerBiEndpointFactory(
            login_url=self.credentials.login_url,
            api_base=self.credentials.api_base,
        )
        authority = endpoint_factory.authority(self.credentials.tenant_id)

        client_credential = _get_client_credential(
            self.credentials.secret, self.credentials.certificate
        )

        self.app = msal.ConfidentialClientApplication(
            client_id=self.credentials.client_id,
            authority=authority,
            client_credential=client_credential,
        )

    def fetch_token(self):
        token = self.app.acquire_token_for_client(
            scopes=self.credentials.scopes
        )

        if Keys.ACCESS_TOKEN not in token:
            raise ValueError(f"No access token in token response: {token}")

        return token[Keys.ACCESS_TOKEN]
