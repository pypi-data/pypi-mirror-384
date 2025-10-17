#  Copyright 2024 Palantir Technologies, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import time
from typing import List
from typing import Optional

from foundry_sdk._core.config import Config
from foundry_sdk._core.oauth_utils import ConfidentialClientOAuthFlowProvider
from foundry_sdk._core.oauth_utils import OAuth
from foundry_sdk._core.oauth_utils import OAuthToken
from foundry_sdk._core.oauth_utils import SignInResponse
from foundry_sdk._core.oauth_utils import SignOutResponse
from foundry_sdk._core.utils import assert_non_empty_string


class ConfidentialClientAuth(OAuth):
    """
    Client for Confidential Client OAuth-authenticated Ontology applications.
    Runs a background thread to periodically refresh access token.

    :param client_id: OAuth client id to be used by the application.
    :param client_secret: OAuth client secret to be used by the application.
    :param scopes: The list of scopes to request. By default, no specific scope is provided and a token will be returned with all scopes.
    :param hostname: Hostname for authentication. This is only required if using ConfidentialClientAuth independently of the FoundryClient.
    :param config: The HTTP config for authentication. This is only required if using ConfidentialClientAuth independently of the FoundryClient.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        hostname: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        should_refresh: bool = True,
        *,
        config: Optional[Config] = None,
    ) -> None:
        assert_non_empty_string(client_id, "client_id")
        assert_non_empty_string(client_secret, "client_secret")

        if hostname is not None:
            assert_non_empty_string(hostname, "hostname")

        if scopes is not None:
            if not isinstance(scopes, list):
                raise TypeError(f"The scopes must be a list, not {type(scopes)}.")

        self._client_id = client_id
        self._client_secret = client_secret
        self._server_oauth_flow_provider = ConfidentialClientOAuthFlowProvider(
            client_id,
            client_secret,
            scopes=scopes,
        )
        super().__init__(hostname=hostname, should_refresh=should_refresh, config=config)

    @property
    def scopes(self) -> List[str]:
        return self._server_oauth_flow_provider.scopes or []

    def get_token(self) -> OAuthToken:
        if self._token is None:
            self._token = self._server_oauth_flow_provider.get_token(self._get_client())

            if self._should_refresh:
                self._start_auto_refresh()

        return self._token

    def _revoke_token(self) -> None:
        if self._token:
            self._server_oauth_flow_provider.revoke_token(
                self._get_client(),
                self._token.access_token,
            )

    @property
    def url(self) -> str:
        return self._get_client().base_url.host

    def _try_refresh_token(self) -> bool:
        self._token = self._server_oauth_flow_provider.get_token(self._get_client())
        return True
