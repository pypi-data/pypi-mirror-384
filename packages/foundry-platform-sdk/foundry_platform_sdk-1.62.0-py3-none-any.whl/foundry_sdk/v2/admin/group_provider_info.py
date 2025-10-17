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

import pydantic
import typing_extensions

from foundry_sdk import _core as core
from foundry_sdk import _errors as errors
from foundry_sdk.v2.admin import errors as admin_errors
from foundry_sdk.v2.admin import models as admin_models
from foundry_sdk.v2.core import models as core_models


class GroupProviderInfoClient:
    """
    The API client for the GroupProviderInfo Resource.

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
        self._api_client = core.ApiClient(auth=auth, hostname=hostname, config=config)

        self.with_streaming_response = _GroupProviderInfoClientStreaming(self)
        self.with_raw_response = _GroupProviderInfoClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        group_id: core_models.GroupId,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> admin_models.GroupProviderInfo:
        """
        Get the GroupProviderInfo.
        :param group_id:
        :type group_id: GroupId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: admin_models.GroupProviderInfo

        :raises GetGroupProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given group.
        :raises GroupNotFound: The given Group could not be found.
        :raises GroupProviderInfoNotFound: The given GroupProviderInfo could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/admin/groups/{groupId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "groupId": group_id,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=admin_models.GroupProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetGroupProviderInfoPermissionDenied": admin_errors.GetGroupProviderInfoPermissionDenied,
                    "GroupNotFound": admin_errors.GroupNotFound,
                    "GroupProviderInfoNotFound": admin_errors.GroupProviderInfoNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def replace(
        self,
        group_id: core_models.GroupId,
        *,
        provider_id: admin_models.ProviderId,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> admin_models.GroupProviderInfo:
        """
        Replace the GroupProviderInfo.
        :param group_id:
        :type group_id: GroupId
        :param provider_id: The ID of the Group in the external authentication provider. This value is determined by the authentication provider. At most one Group can have a given provider ID in a given Realm.
        :type provider_id: ProviderId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: admin_models.GroupProviderInfo

        :raises CannotReplaceProviderInfoForPrincipalInProtectedRealm: Provider information for Principals in this Realm cannot be replaced.
        :raises GetGroupProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given group.
        :raises GroupNotFound: The given Group could not be found.
        :raises GroupProviderInfoNotFound: The given GroupProviderInfo could not be found.
        :raises ReplaceGroupProviderInfoPermissionDenied: Could not replace the GroupProviderInfo.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="PUT",
                resource_path="/v2/admin/groups/{groupId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "groupId": group_id,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=admin_models.ReplaceGroupProviderInfoRequest(
                    provider_id=provider_id,
                ),
                response_type=admin_models.GroupProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "CannotReplaceProviderInfoForPrincipalInProtectedRealm": admin_errors.CannotReplaceProviderInfoForPrincipalInProtectedRealm,
                    "GetGroupProviderInfoPermissionDenied": admin_errors.GetGroupProviderInfoPermissionDenied,
                    "GroupNotFound": admin_errors.GroupNotFound,
                    "GroupProviderInfoNotFound": admin_errors.GroupProviderInfoNotFound,
                    "ReplaceGroupProviderInfoPermissionDenied": admin_errors.ReplaceGroupProviderInfoPermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _GroupProviderInfoClientRaw:
    def __init__(self, client: GroupProviderInfoClient) -> None:
        def get(_: admin_models.GroupProviderInfo): ...
        def replace(_: admin_models.GroupProviderInfo): ...

        self.get = core.with_raw_response(get, client.get)
        self.replace = core.with_raw_response(replace, client.replace)


class _GroupProviderInfoClientStreaming:
    def __init__(self, client: GroupProviderInfoClient) -> None:
        def get(_: admin_models.GroupProviderInfo): ...
        def replace(_: admin_models.GroupProviderInfo): ...

        self.get = core.with_streaming_response(get, client.get)
        self.replace = core.with_streaming_response(replace, client.replace)


class AsyncGroupProviderInfoClient:
    """
    The API client for the GroupProviderInfo Resource.

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
        self._api_client = core.AsyncApiClient(auth=auth, hostname=hostname, config=config)

        self.with_streaming_response = _AsyncGroupProviderInfoClientStreaming(self)
        self.with_raw_response = _AsyncGroupProviderInfoClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        group_id: core_models.GroupId,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[admin_models.GroupProviderInfo]:
        """
        Get the GroupProviderInfo.
        :param group_id:
        :type group_id: GroupId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[admin_models.GroupProviderInfo]

        :raises GetGroupProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given group.
        :raises GroupNotFound: The given Group could not be found.
        :raises GroupProviderInfoNotFound: The given GroupProviderInfo could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/admin/groups/{groupId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "groupId": group_id,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=admin_models.GroupProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetGroupProviderInfoPermissionDenied": admin_errors.GetGroupProviderInfoPermissionDenied,
                    "GroupNotFound": admin_errors.GroupNotFound,
                    "GroupProviderInfoNotFound": admin_errors.GroupProviderInfoNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def replace(
        self,
        group_id: core_models.GroupId,
        *,
        provider_id: admin_models.ProviderId,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[admin_models.GroupProviderInfo]:
        """
        Replace the GroupProviderInfo.
        :param group_id:
        :type group_id: GroupId
        :param provider_id: The ID of the Group in the external authentication provider. This value is determined by the authentication provider. At most one Group can have a given provider ID in a given Realm.
        :type provider_id: ProviderId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[admin_models.GroupProviderInfo]

        :raises CannotReplaceProviderInfoForPrincipalInProtectedRealm: Provider information for Principals in this Realm cannot be replaced.
        :raises GetGroupProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given group.
        :raises GroupNotFound: The given Group could not be found.
        :raises GroupProviderInfoNotFound: The given GroupProviderInfo could not be found.
        :raises ReplaceGroupProviderInfoPermissionDenied: Could not replace the GroupProviderInfo.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="PUT",
                resource_path="/v2/admin/groups/{groupId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "groupId": group_id,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=admin_models.ReplaceGroupProviderInfoRequest(
                    provider_id=provider_id,
                ),
                response_type=admin_models.GroupProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "CannotReplaceProviderInfoForPrincipalInProtectedRealm": admin_errors.CannotReplaceProviderInfoForPrincipalInProtectedRealm,
                    "GetGroupProviderInfoPermissionDenied": admin_errors.GetGroupProviderInfoPermissionDenied,
                    "GroupNotFound": admin_errors.GroupNotFound,
                    "GroupProviderInfoNotFound": admin_errors.GroupProviderInfoNotFound,
                    "ReplaceGroupProviderInfoPermissionDenied": admin_errors.ReplaceGroupProviderInfoPermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncGroupProviderInfoClientRaw:
    def __init__(self, client: AsyncGroupProviderInfoClient) -> None:
        def get(_: admin_models.GroupProviderInfo): ...
        def replace(_: admin_models.GroupProviderInfo): ...

        self.get = core.async_with_raw_response(get, client.get)
        self.replace = core.async_with_raw_response(replace, client.replace)


class _AsyncGroupProviderInfoClientStreaming:
    def __init__(self, client: AsyncGroupProviderInfoClient) -> None:
        def get(_: admin_models.GroupProviderInfo): ...
        def replace(_: admin_models.GroupProviderInfo): ...

        self.get = core.async_with_streaming_response(get, client.get)
        self.replace = core.async_with_streaming_response(replace, client.replace)
