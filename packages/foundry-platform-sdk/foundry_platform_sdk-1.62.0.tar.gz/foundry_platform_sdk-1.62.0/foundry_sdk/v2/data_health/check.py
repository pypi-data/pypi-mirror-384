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
from foundry_sdk.v2.core import models as core_models
from foundry_sdk.v2.data_health import errors as data_health_errors
from foundry_sdk.v2.data_health import models as data_health_models


class CheckClient:
    """
    The API client for the Check Resource.

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

        self.with_streaming_response = _CheckClientStreaming(self)
        self.with_raw_response = _CheckClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def create(
        self,
        *,
        config: data_health_models.CheckConfig,
        intent: typing.Optional[data_health_models.CheckIntent] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> data_health_models.Check:
        """
        Creates a new Check.
        :param config:
        :type config: CheckConfig
        :param intent:
        :type intent: Optional[CheckIntent]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: data_health_models.Check

        :raises CheckAlreadyExists: A check of the given type for the given subject(s) already exists. The conflicting check will be returned if the provided token has permission to view it.
        :raises CheckTypeNotSupported: The type of the requested check is not yet supported in the Platform API.
        :raises CreateCheckPermissionDenied: Could not create the Check.
        :raises InvalidPercentageCheckConfig: The PercentageCheckConfig is invalid. It must contain at least one of percentageBounds or medianDeviation.
        :raises InvalidTimeCheckConfig: The TimeCheckConfig is invalid. It must contain at least one of timeBounds or medianDeviation.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/dataHealth/checks",
                query_params={
                    "preview": preview,
                },
                path_params={},
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=data_health_models.CreateCheckRequest(
                    config=config,
                    intent=intent,
                ),
                response_type=data_health_models.Check,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckAlreadyExists": data_health_errors.CheckAlreadyExists,
                    "CheckTypeNotSupported": data_health_errors.CheckTypeNotSupported,
                    "CreateCheckPermissionDenied": data_health_errors.CreateCheckPermissionDenied,
                    "InvalidPercentageCheckConfig": data_health_errors.InvalidPercentageCheckConfig,
                    "InvalidTimeCheckConfig": data_health_errors.InvalidTimeCheckConfig,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def delete(
        self,
        check_rid: core_models.CheckRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """
        Delete the Check with the specified rid.
        :param check_rid:
        :type check_rid: CheckRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises CheckNotFound: The given Check could not be found.
        :raises DeleteCheckPermissionDenied: Could not delete the Check.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="DELETE",
                resource_path="/v2/dataHealth/checks/{checkRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "checkRid": check_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckNotFound": data_health_errors.CheckNotFound,
                    "DeleteCheckPermissionDenied": data_health_errors.DeleteCheckPermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        check_rid: core_models.CheckRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> data_health_models.Check:
        """
        Get the Check with the specified rid.
        :param check_rid:
        :type check_rid: CheckRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: data_health_models.Check

        :raises CheckNotFound: The given Check could not be found.
        :raises CheckTypeNotSupported: The type of the requested check is not yet supported in the Platform API.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/dataHealth/checks/{checkRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "checkRid": check_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=data_health_models.Check,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckNotFound": data_health_errors.CheckNotFound,
                    "CheckTypeNotSupported": data_health_errors.CheckTypeNotSupported,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def replace(
        self,
        check_rid: core_models.CheckRid,
        *,
        config: data_health_models.ReplaceCheckConfig,
        intent: typing.Optional[data_health_models.CheckIntent] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> data_health_models.Check:
        """
        Replace the Check with the specified rid. Changing the type of a check after it has been created  is not supported.
        :param check_rid:
        :type check_rid: CheckRid
        :param config:
        :type config: ReplaceCheckConfig
        :param intent:
        :type intent: Optional[CheckIntent]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: data_health_models.Check

        :raises CheckNotFound: The given Check could not be found.
        :raises CheckTypeNotSupported: The type of the requested check is not yet supported in the Platform API.
        :raises InvalidPercentageCheckConfig: The PercentageCheckConfig is invalid. It must contain at least one of percentageBounds or medianDeviation.
        :raises InvalidTimeCheckConfig: The TimeCheckConfig is invalid. It must contain at least one of timeBounds or medianDeviation.
        :raises ModifyingCheckTypeNotSupported: Changing the type of a check after it has been created is not supported.
        :raises ReplaceCheckPermissionDenied: Could not replace the Check.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="PUT",
                resource_path="/v2/dataHealth/checks/{checkRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "checkRid": check_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=data_health_models.ReplaceCheckRequest(
                    config=config,
                    intent=intent,
                ),
                response_type=data_health_models.Check,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckNotFound": data_health_errors.CheckNotFound,
                    "CheckTypeNotSupported": data_health_errors.CheckTypeNotSupported,
                    "InvalidPercentageCheckConfig": data_health_errors.InvalidPercentageCheckConfig,
                    "InvalidTimeCheckConfig": data_health_errors.InvalidTimeCheckConfig,
                    "ModifyingCheckTypeNotSupported": data_health_errors.ModifyingCheckTypeNotSupported,
                    "ReplaceCheckPermissionDenied": data_health_errors.ReplaceCheckPermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _CheckClientRaw:
    def __init__(self, client: CheckClient) -> None:
        def create(_: data_health_models.Check): ...
        def delete(_: None): ...
        def get(_: data_health_models.Check): ...
        def replace(_: data_health_models.Check): ...

        self.create = core.with_raw_response(create, client.create)
        self.delete = core.with_raw_response(delete, client.delete)
        self.get = core.with_raw_response(get, client.get)
        self.replace = core.with_raw_response(replace, client.replace)


class _CheckClientStreaming:
    def __init__(self, client: CheckClient) -> None:
        def create(_: data_health_models.Check): ...
        def get(_: data_health_models.Check): ...
        def replace(_: data_health_models.Check): ...

        self.create = core.with_streaming_response(create, client.create)
        self.get = core.with_streaming_response(get, client.get)
        self.replace = core.with_streaming_response(replace, client.replace)


class AsyncCheckClient:
    """
    The API client for the Check Resource.

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

        self.with_streaming_response = _AsyncCheckClientStreaming(self)
        self.with_raw_response = _AsyncCheckClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def create(
        self,
        *,
        config: data_health_models.CheckConfig,
        intent: typing.Optional[data_health_models.CheckIntent] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[data_health_models.Check]:
        """
        Creates a new Check.
        :param config:
        :type config: CheckConfig
        :param intent:
        :type intent: Optional[CheckIntent]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[data_health_models.Check]

        :raises CheckAlreadyExists: A check of the given type for the given subject(s) already exists. The conflicting check will be returned if the provided token has permission to view it.
        :raises CheckTypeNotSupported: The type of the requested check is not yet supported in the Platform API.
        :raises CreateCheckPermissionDenied: Could not create the Check.
        :raises InvalidPercentageCheckConfig: The PercentageCheckConfig is invalid. It must contain at least one of percentageBounds or medianDeviation.
        :raises InvalidTimeCheckConfig: The TimeCheckConfig is invalid. It must contain at least one of timeBounds or medianDeviation.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/dataHealth/checks",
                query_params={
                    "preview": preview,
                },
                path_params={},
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=data_health_models.CreateCheckRequest(
                    config=config,
                    intent=intent,
                ),
                response_type=data_health_models.Check,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckAlreadyExists": data_health_errors.CheckAlreadyExists,
                    "CheckTypeNotSupported": data_health_errors.CheckTypeNotSupported,
                    "CreateCheckPermissionDenied": data_health_errors.CreateCheckPermissionDenied,
                    "InvalidPercentageCheckConfig": data_health_errors.InvalidPercentageCheckConfig,
                    "InvalidTimeCheckConfig": data_health_errors.InvalidTimeCheckConfig,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def delete(
        self,
        check_rid: core_models.CheckRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """
        Delete the Check with the specified rid.
        :param check_rid:
        :type check_rid: CheckRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises CheckNotFound: The given Check could not be found.
        :raises DeleteCheckPermissionDenied: Could not delete the Check.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="DELETE",
                resource_path="/v2/dataHealth/checks/{checkRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "checkRid": check_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckNotFound": data_health_errors.CheckNotFound,
                    "DeleteCheckPermissionDenied": data_health_errors.DeleteCheckPermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        check_rid: core_models.CheckRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[data_health_models.Check]:
        """
        Get the Check with the specified rid.
        :param check_rid:
        :type check_rid: CheckRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[data_health_models.Check]

        :raises CheckNotFound: The given Check could not be found.
        :raises CheckTypeNotSupported: The type of the requested check is not yet supported in the Platform API.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/dataHealth/checks/{checkRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "checkRid": check_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=data_health_models.Check,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckNotFound": data_health_errors.CheckNotFound,
                    "CheckTypeNotSupported": data_health_errors.CheckTypeNotSupported,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def replace(
        self,
        check_rid: core_models.CheckRid,
        *,
        config: data_health_models.ReplaceCheckConfig,
        intent: typing.Optional[data_health_models.CheckIntent] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[data_health_models.Check]:
        """
        Replace the Check with the specified rid. Changing the type of a check after it has been created  is not supported.
        :param check_rid:
        :type check_rid: CheckRid
        :param config:
        :type config: ReplaceCheckConfig
        :param intent:
        :type intent: Optional[CheckIntent]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[data_health_models.Check]

        :raises CheckNotFound: The given Check could not be found.
        :raises CheckTypeNotSupported: The type of the requested check is not yet supported in the Platform API.
        :raises InvalidPercentageCheckConfig: The PercentageCheckConfig is invalid. It must contain at least one of percentageBounds or medianDeviation.
        :raises InvalidTimeCheckConfig: The TimeCheckConfig is invalid. It must contain at least one of timeBounds or medianDeviation.
        :raises ModifyingCheckTypeNotSupported: Changing the type of a check after it has been created is not supported.
        :raises ReplaceCheckPermissionDenied: Could not replace the Check.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="PUT",
                resource_path="/v2/dataHealth/checks/{checkRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "checkRid": check_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=data_health_models.ReplaceCheckRequest(
                    config=config,
                    intent=intent,
                ),
                response_type=data_health_models.Check,
                request_timeout=request_timeout,
                throwable_errors={
                    "CheckNotFound": data_health_errors.CheckNotFound,
                    "CheckTypeNotSupported": data_health_errors.CheckTypeNotSupported,
                    "InvalidPercentageCheckConfig": data_health_errors.InvalidPercentageCheckConfig,
                    "InvalidTimeCheckConfig": data_health_errors.InvalidTimeCheckConfig,
                    "ModifyingCheckTypeNotSupported": data_health_errors.ModifyingCheckTypeNotSupported,
                    "ReplaceCheckPermissionDenied": data_health_errors.ReplaceCheckPermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncCheckClientRaw:
    def __init__(self, client: AsyncCheckClient) -> None:
        def create(_: data_health_models.Check): ...
        def delete(_: None): ...
        def get(_: data_health_models.Check): ...
        def replace(_: data_health_models.Check): ...

        self.create = core.async_with_raw_response(create, client.create)
        self.delete = core.async_with_raw_response(delete, client.delete)
        self.get = core.async_with_raw_response(get, client.get)
        self.replace = core.async_with_raw_response(replace, client.replace)


class _AsyncCheckClientStreaming:
    def __init__(self, client: AsyncCheckClient) -> None:
        def create(_: data_health_models.Check): ...
        def get(_: data_health_models.Check): ...
        def replace(_: data_health_models.Check): ...

        self.create = core.async_with_streaming_response(create, client.create)
        self.get = core.async_with_streaming_response(get, client.get)
        self.replace = core.async_with_streaming_response(replace, client.replace)
