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


import typing
from functools import cached_property

from foundry_sdk import _core as core


class LanguageModelsClient:
    """
    The API client for the LanguageModels Namespace.

    :param auth: Your auth configuration.
    :param hostname: Your Foundry hostname (for example, "myfoundry.palantirfoundry.com"). This can also include your API gateway service URI.
    :param config: Optionally specify the configuration for the HTTP session.
    """

    def __init__(
        self,
        auth: core.Auth,
        hostname: str,
        config: typing.Optional[core.Config] = None,
    ):
        self._auth = auth
        self._hostname = hostname
        self._config = config

    @cached_property
    def AnthropicModel(self):
        from foundry_sdk.v2.language_models.anthropic_model import AnthropicModelClient

        return AnthropicModelClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @cached_property
    def OpenAiModel(self):
        from foundry_sdk.v2.language_models.open_ai_model import OpenAiModelClient

        return OpenAiModelClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )


class AsyncLanguageModelsClient:
    """
    The Async API client for the LanguageModels Namespace.

    :param auth: Your auth configuration.
    :param hostname: Your Foundry hostname (for example, "myfoundry.palantirfoundry.com"). This can also include your API gateway service URI.
    :param config: Optionally specify the configuration for the HTTP session.
    """

    def __init__(
        self,
        auth: core.Auth,
        hostname: str,
        config: typing.Optional[core.Config] = None,
    ):
        from foundry_sdk.v2.language_models.anthropic_model import AsyncAnthropicModelClient  # NOQA
        from foundry_sdk.v2.language_models.open_ai_model import AsyncOpenAiModelClient

        self.AnthropicModel = AsyncAnthropicModelClient(auth=auth, hostname=hostname, config=config)

        self.OpenAiModel = AsyncOpenAiModelClient(auth=auth, hostname=hostname, config=config)
