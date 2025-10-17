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


class UserProviderInfoClient:
    """
    The API client for the UserProviderInfo Resource.

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

        self.with_streaming_response = _UserProviderInfoClientStreaming(self)
        self.with_raw_response = _UserProviderInfoClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        user_id: core_models.UserId,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> admin_models.UserProviderInfo:
        """
        Get the UserProviderInfo.
        :param user_id:
        :type user_id: UserId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: admin_models.UserProviderInfo

        :raises GetUserProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given user.
        :raises UserDeleted: The user is deleted.
        :raises UserNotFound: The given User could not be found.
        :raises UserProviderInfoNotFound: The given UserProviderInfo could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/admin/users/{userId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "userId": user_id,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=admin_models.UserProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetUserProviderInfoPermissionDenied": admin_errors.GetUserProviderInfoPermissionDenied,
                    "UserDeleted": admin_errors.UserDeleted,
                    "UserNotFound": admin_errors.UserNotFound,
                    "UserProviderInfoNotFound": admin_errors.UserProviderInfoNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def replace(
        self,
        user_id: core_models.UserId,
        *,
        provider_id: admin_models.ProviderId,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> admin_models.UserProviderInfo:
        """
        Replace the UserProviderInfo.
        :param user_id:
        :type user_id: UserId
        :param provider_id: The ID of the User in the external authentication provider. This value is determined by the authentication provider. At most one User can have a given provider ID in a given Realm.
        :type provider_id: ProviderId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: admin_models.UserProviderInfo

        :raises CannotReplaceProviderInfoForPrincipalInProtectedRealm: Provider information for Principals in this Realm cannot be replaced.
        :raises GetUserProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given user.
        :raises ReplaceUserProviderInfoPermissionDenied: Could not replace the UserProviderInfo.
        :raises UserDeleted: The user is deleted.
        :raises UserNotFound: The given User could not be found.
        :raises UserProviderInfoNotFound: The given UserProviderInfo could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="PUT",
                resource_path="/v2/admin/users/{userId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "userId": user_id,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=admin_models.ReplaceUserProviderInfoRequest(
                    provider_id=provider_id,
                ),
                response_type=admin_models.UserProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "CannotReplaceProviderInfoForPrincipalInProtectedRealm": admin_errors.CannotReplaceProviderInfoForPrincipalInProtectedRealm,
                    "GetUserProviderInfoPermissionDenied": admin_errors.GetUserProviderInfoPermissionDenied,
                    "ReplaceUserProviderInfoPermissionDenied": admin_errors.ReplaceUserProviderInfoPermissionDenied,
                    "UserDeleted": admin_errors.UserDeleted,
                    "UserNotFound": admin_errors.UserNotFound,
                    "UserProviderInfoNotFound": admin_errors.UserProviderInfoNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _UserProviderInfoClientRaw:
    def __init__(self, client: UserProviderInfoClient) -> None:
        def get(_: admin_models.UserProviderInfo): ...
        def replace(_: admin_models.UserProviderInfo): ...

        self.get = core.with_raw_response(get, client.get)
        self.replace = core.with_raw_response(replace, client.replace)


class _UserProviderInfoClientStreaming:
    def __init__(self, client: UserProviderInfoClient) -> None:
        def get(_: admin_models.UserProviderInfo): ...
        def replace(_: admin_models.UserProviderInfo): ...

        self.get = core.with_streaming_response(get, client.get)
        self.replace = core.with_streaming_response(replace, client.replace)


class AsyncUserProviderInfoClient:
    """
    The API client for the UserProviderInfo Resource.

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

        self.with_streaming_response = _AsyncUserProviderInfoClientStreaming(self)
        self.with_raw_response = _AsyncUserProviderInfoClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        user_id: core_models.UserId,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[admin_models.UserProviderInfo]:
        """
        Get the UserProviderInfo.
        :param user_id:
        :type user_id: UserId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[admin_models.UserProviderInfo]

        :raises GetUserProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given user.
        :raises UserDeleted: The user is deleted.
        :raises UserNotFound: The given User could not be found.
        :raises UserProviderInfoNotFound: The given UserProviderInfo could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/admin/users/{userId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "userId": user_id,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=admin_models.UserProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetUserProviderInfoPermissionDenied": admin_errors.GetUserProviderInfoPermissionDenied,
                    "UserDeleted": admin_errors.UserDeleted,
                    "UserNotFound": admin_errors.UserNotFound,
                    "UserProviderInfoNotFound": admin_errors.UserProviderInfoNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def replace(
        self,
        user_id: core_models.UserId,
        *,
        provider_id: admin_models.ProviderId,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[admin_models.UserProviderInfo]:
        """
        Replace the UserProviderInfo.
        :param user_id:
        :type user_id: UserId
        :param provider_id: The ID of the User in the external authentication provider. This value is determined by the authentication provider. At most one User can have a given provider ID in a given Realm.
        :type provider_id: ProviderId
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[admin_models.UserProviderInfo]

        :raises CannotReplaceProviderInfoForPrincipalInProtectedRealm: Provider information for Principals in this Realm cannot be replaced.
        :raises GetUserProviderInfoPermissionDenied: The provided token does not have permission to view the provider information for the given user.
        :raises ReplaceUserProviderInfoPermissionDenied: Could not replace the UserProviderInfo.
        :raises UserDeleted: The user is deleted.
        :raises UserNotFound: The given User could not be found.
        :raises UserProviderInfoNotFound: The given UserProviderInfo could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="PUT",
                resource_path="/v2/admin/users/{userId}/providerInfo",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "userId": user_id,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=admin_models.ReplaceUserProviderInfoRequest(
                    provider_id=provider_id,
                ),
                response_type=admin_models.UserProviderInfo,
                request_timeout=request_timeout,
                throwable_errors={
                    "CannotReplaceProviderInfoForPrincipalInProtectedRealm": admin_errors.CannotReplaceProviderInfoForPrincipalInProtectedRealm,
                    "GetUserProviderInfoPermissionDenied": admin_errors.GetUserProviderInfoPermissionDenied,
                    "ReplaceUserProviderInfoPermissionDenied": admin_errors.ReplaceUserProviderInfoPermissionDenied,
                    "UserDeleted": admin_errors.UserDeleted,
                    "UserNotFound": admin_errors.UserNotFound,
                    "UserProviderInfoNotFound": admin_errors.UserProviderInfoNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncUserProviderInfoClientRaw:
    def __init__(self, client: AsyncUserProviderInfoClient) -> None:
        def get(_: admin_models.UserProviderInfo): ...
        def replace(_: admin_models.UserProviderInfo): ...

        self.get = core.async_with_raw_response(get, client.get)
        self.replace = core.async_with_raw_response(replace, client.replace)


class _AsyncUserProviderInfoClientStreaming:
    def __init__(self, client: AsyncUserProviderInfoClient) -> None:
        def get(_: admin_models.UserProviderInfo): ...
        def replace(_: admin_models.UserProviderInfo): ...

        self.get = core.async_with_streaming_response(get, client.get)
        self.replace = core.async_with_streaming_response(replace, client.replace)
