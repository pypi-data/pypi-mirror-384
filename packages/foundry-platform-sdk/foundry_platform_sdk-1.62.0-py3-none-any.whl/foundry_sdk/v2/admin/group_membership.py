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
from foundry_sdk.v2.core import errors as core_errors
from foundry_sdk.v2.core import models as core_models


class GroupMembershipClient:
    """
    The API client for the GroupMembership Resource.

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

        self.with_streaming_response = _GroupMembershipClientStreaming(self)
        self.with_raw_response = _GroupMembershipClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def list(
        self,
        user_id: core_models.UserId,
        *,
        page_size: typing.Optional[core_models.PageSize] = None,
        page_token: typing.Optional[core_models.PageToken] = None,
        transitive: typing.Optional[bool] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core.ResourceIterator[admin_models.GroupMembership]:
        """
        Lists all Groups a given User is a member of.

        This is a paged endpoint. Each page may be smaller or larger than the requested page size. However,
        it is guaranteed that if there are more results available, the `nextPageToken` field will be populated.
        To get the next page, make the same request again, but set the value of the `pageToken` query parameter
        to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field
        in the response, you are on the last page.

        :param user_id:
        :type user_id: UserId
        :param page_size: The page size to use for the endpoint.
        :type page_size: Optional[PageSize]
        :param page_token: The page token indicates where to start paging. This should be omitted from the first page's request. To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response and use it to populate the `pageToken` field of the next request.
        :type page_token: Optional[PageToken]
        :param transitive: When true, includes the transitive memberships of the Groups the User is a member of. For example, say the User is a member of Group A, and Group A is a member of Group B. If `transitive=false` only Group A will be returned, but if `transitive=true` then Groups A and B will be returned. This will recursively resolve Groups through all layers of nesting.  Defaults to false.
        :type transitive: Optional[bool]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core.ResourceIterator[admin_models.GroupMembership]

        :raises InvalidPageSize: The provided page size was zero or negative. Page sizes must be greater than zero.
        :raises UserDeleted: The user is deleted.
        :raises UserNotFound: The given User could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/admin/users/{userId}/groupMemberships",
                query_params={
                    "pageSize": page_size,
                    "pageToken": page_token,
                    "transitive": transitive,
                },
                path_params={
                    "userId": user_id,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=admin_models.ListGroupMembershipsResponse,
                request_timeout=request_timeout,
                throwable_errors={
                    "InvalidPageSize": core_errors.InvalidPageSize,
                    "UserDeleted": admin_errors.UserDeleted,
                    "UserNotFound": admin_errors.UserNotFound,
                },
                response_mode=_sdk_internal.get("response_mode", "ITERATOR"),
            ),
        )


class _GroupMembershipClientRaw:
    def __init__(self, client: GroupMembershipClient) -> None:
        def list(_: admin_models.ListGroupMembershipsResponse): ...

        self.list = core.with_raw_response(list, client.list)


class _GroupMembershipClientStreaming:
    def __init__(self, client: GroupMembershipClient) -> None:
        def list(_: admin_models.ListGroupMembershipsResponse): ...

        self.list = core.with_streaming_response(list, client.list)


class AsyncGroupMembershipClient:
    """
    The API client for the GroupMembership Resource.

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

        self.with_streaming_response = _AsyncGroupMembershipClientStreaming(self)
        self.with_raw_response = _AsyncGroupMembershipClientRaw(self)

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def list(
        self,
        user_id: core_models.UserId,
        *,
        page_size: typing.Optional[core_models.PageSize] = None,
        page_token: typing.Optional[core_models.PageToken] = None,
        transitive: typing.Optional[bool] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core.AsyncResourceIterator[admin_models.GroupMembership]:
        """
        Lists all Groups a given User is a member of.

        This is a paged endpoint. Each page may be smaller or larger than the requested page size. However,
        it is guaranteed that if there are more results available, the `nextPageToken` field will be populated.
        To get the next page, make the same request again, but set the value of the `pageToken` query parameter
        to be value of the `nextPageToken` value of the previous response. If there is no `nextPageToken` field
        in the response, you are on the last page.

        :param user_id:
        :type user_id: UserId
        :param page_size: The page size to use for the endpoint.
        :type page_size: Optional[PageSize]
        :param page_token: The page token indicates where to start paging. This should be omitted from the first page's request. To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response and use it to populate the `pageToken` field of the next request.
        :type page_token: Optional[PageToken]
        :param transitive: When true, includes the transitive memberships of the Groups the User is a member of. For example, say the User is a member of Group A, and Group A is a member of Group B. If `transitive=false` only Group A will be returned, but if `transitive=true` then Groups A and B will be returned. This will recursively resolve Groups through all layers of nesting.  Defaults to false.
        :type transitive: Optional[bool]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core.AsyncResourceIterator[admin_models.GroupMembership]

        :raises InvalidPageSize: The provided page size was zero or negative. Page sizes must be greater than zero.
        :raises UserDeleted: The user is deleted.
        :raises UserNotFound: The given User could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/admin/users/{userId}/groupMemberships",
                query_params={
                    "pageSize": page_size,
                    "pageToken": page_token,
                    "transitive": transitive,
                },
                path_params={
                    "userId": user_id,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=admin_models.ListGroupMembershipsResponse,
                request_timeout=request_timeout,
                throwable_errors={
                    "InvalidPageSize": core_errors.InvalidPageSize,
                    "UserDeleted": admin_errors.UserDeleted,
                    "UserNotFound": admin_errors.UserNotFound,
                },
                response_mode=_sdk_internal.get("response_mode", "ITERATOR"),
            ),
        )


class _AsyncGroupMembershipClientRaw:
    def __init__(self, client: AsyncGroupMembershipClient) -> None:
        def list(_: admin_models.ListGroupMembershipsResponse): ...

        self.list = core.async_with_raw_response(list, client.list)


class _AsyncGroupMembershipClientStreaming:
    def __init__(self, client: AsyncGroupMembershipClient) -> None:
        def list(_: admin_models.ListGroupMembershipsResponse): ...

        self.list = core.async_with_streaming_response(list, client.list)
