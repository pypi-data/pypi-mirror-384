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
from foundry_sdk.v2.core import models as core_models
from foundry_sdk.v2.filesystem import errors as filesystem_errors
from foundry_sdk.v2.filesystem import models as filesystem_models


class ResourceRoleClient:
    """
    The API client for the ResourceRole Resource.

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

        self.with_streaming_response = _ResourceRoleClientStreaming(self)
        self.with_raw_response = _ResourceRoleClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def add(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        roles: typing.List[filesystem_models.ResourceRoleIdentifier],
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param roles:
        :type roles: List[ResourceRoleIdentifier]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises AddResourceRolesPermissionDenied: Could not add the ResourceRole.
        :raises InvalidRoleIds: A roleId referenced in either default roles or role grants does not exist in the project role set for the space.
        :raises PrincipalNotFound: A principal (User or Group) with the given PrincipalId could not be found
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/roles/add",
                query_params={},
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.AddResourceRolesRequest(
                    roles=roles,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "AddResourceRolesPermissionDenied": filesystem_errors.AddResourceRolesPermissionDenied,
                    "InvalidRoleIds": filesystem_errors.InvalidRoleIds,
                    "PrincipalNotFound": admin_errors.PrincipalNotFound,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def list(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        include_inherited: typing.Optional[bool] = None,
        page_size: typing.Optional[core_models.PageSize] = None,
        page_token: typing.Optional[core_models.PageToken] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core.ResourceIterator[filesystem_models.ResourceRole]:
        """
        List the roles on a resource.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param include_inherited: Whether to include inherited roles on the resource.
        :type include_inherited: Optional[bool]
        :param page_size: The page size to use for the endpoint.
        :type page_size: Optional[PageSize]
        :param page_token: The page token indicates where to start paging. This should be omitted from the first page's request. To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response and use it to populate the `pageToken` field of the next request.
        :type page_token: Optional[PageToken]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core.ResourceIterator[filesystem_models.ResourceRole]

        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}/roles",
                query_params={
                    "includeInherited": include_inherited,
                    "pageSize": page_size,
                    "pageToken": page_token,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.ListResourceRolesResponse,
                request_timeout=request_timeout,
                throwable_errors={
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode", "ITERATOR"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def remove(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        roles: typing.List[filesystem_models.ResourceRoleIdentifier],
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param roles:
        :type roles: List[ResourceRoleIdentifier]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises InvalidRoleIds: A roleId referenced in either default roles or role grants does not exist in the project role set for the space.
        :raises PrincipalNotFound: A principal (User or Group) with the given PrincipalId could not be found
        :raises RemoveResourceRolesPermissionDenied: Could not remove the ResourceRole.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/roles/remove",
                query_params={},
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.RemoveResourceRolesRequest(
                    roles=roles,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "InvalidRoleIds": filesystem_errors.InvalidRoleIds,
                    "PrincipalNotFound": admin_errors.PrincipalNotFound,
                    "RemoveResourceRolesPermissionDenied": filesystem_errors.RemoveResourceRolesPermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _ResourceRoleClientRaw:
    def __init__(self, client: ResourceRoleClient) -> None:
        def add(_: None): ...
        def list(_: filesystem_models.ListResourceRolesResponse): ...
        def remove(_: None): ...

        self.add = core.with_raw_response(add, client.add)
        self.list = core.with_raw_response(list, client.list)
        self.remove = core.with_raw_response(remove, client.remove)


class _ResourceRoleClientStreaming:
    def __init__(self, client: ResourceRoleClient) -> None:
        def list(_: filesystem_models.ListResourceRolesResponse): ...

        self.list = core.with_streaming_response(list, client.list)


class AsyncResourceRoleClient:
    """
    The API client for the ResourceRole Resource.

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

        self.with_streaming_response = _AsyncResourceRoleClientStreaming(self)
        self.with_raw_response = _AsyncResourceRoleClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def add(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        roles: typing.List[filesystem_models.ResourceRoleIdentifier],
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param roles:
        :type roles: List[ResourceRoleIdentifier]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises AddResourceRolesPermissionDenied: Could not add the ResourceRole.
        :raises InvalidRoleIds: A roleId referenced in either default roles or role grants does not exist in the project role set for the space.
        :raises PrincipalNotFound: A principal (User or Group) with the given PrincipalId could not be found
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/roles/add",
                query_params={},
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.AddResourceRolesRequest(
                    roles=roles,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "AddResourceRolesPermissionDenied": filesystem_errors.AddResourceRolesPermissionDenied,
                    "InvalidRoleIds": filesystem_errors.InvalidRoleIds,
                    "PrincipalNotFound": admin_errors.PrincipalNotFound,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def list(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        include_inherited: typing.Optional[bool] = None,
        page_size: typing.Optional[core_models.PageSize] = None,
        page_token: typing.Optional[core_models.PageToken] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core.AsyncResourceIterator[filesystem_models.ResourceRole]:
        """
        List the roles on a resource.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param include_inherited: Whether to include inherited roles on the resource.
        :type include_inherited: Optional[bool]
        :param page_size: The page size to use for the endpoint.
        :type page_size: Optional[PageSize]
        :param page_token: The page token indicates where to start paging. This should be omitted from the first page's request. To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response and use it to populate the `pageToken` field of the next request.
        :type page_token: Optional[PageToken]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core.AsyncResourceIterator[filesystem_models.ResourceRole]

        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}/roles",
                query_params={
                    "includeInherited": include_inherited,
                    "pageSize": page_size,
                    "pageToken": page_token,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.ListResourceRolesResponse,
                request_timeout=request_timeout,
                throwable_errors={
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode", "ITERATOR"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def remove(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        roles: typing.List[filesystem_models.ResourceRoleIdentifier],
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param roles:
        :type roles: List[ResourceRoleIdentifier]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises InvalidRoleIds: A roleId referenced in either default roles or role grants does not exist in the project role set for the space.
        :raises PrincipalNotFound: A principal (User or Group) with the given PrincipalId could not be found
        :raises RemoveResourceRolesPermissionDenied: Could not remove the ResourceRole.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/roles/remove",
                query_params={},
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.RemoveResourceRolesRequest(
                    roles=roles,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "InvalidRoleIds": filesystem_errors.InvalidRoleIds,
                    "PrincipalNotFound": admin_errors.PrincipalNotFound,
                    "RemoveResourceRolesPermissionDenied": filesystem_errors.RemoveResourceRolesPermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncResourceRoleClientRaw:
    def __init__(self, client: AsyncResourceRoleClient) -> None:
        def add(_: None): ...
        def list(_: filesystem_models.ListResourceRolesResponse): ...
        def remove(_: None): ...

        self.add = core.async_with_raw_response(add, client.add)
        self.list = core.async_with_raw_response(list, client.list)
        self.remove = core.async_with_raw_response(remove, client.remove)


class _AsyncResourceRoleClientStreaming:
    def __init__(self, client: AsyncResourceRoleClient) -> None:
        def list(_: filesystem_models.ListResourceRolesResponse): ...

        self.list = core.async_with_streaming_response(list, client.list)
