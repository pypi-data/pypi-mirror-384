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

import annotated_types
import pydantic
import typing_extensions

from foundry_sdk import _core as core
from foundry_sdk import _errors as errors
from foundry_sdk.v2.core import models as core_models
from foundry_sdk.v2.filesystem import errors as filesystem_errors
from foundry_sdk.v2.filesystem import models as filesystem_models


class ResourceClient:
    """
    The API client for the Resource Resource.

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

        self.with_streaming_response = _ResourceClientStreaming(self)
        self.with_raw_response = _ResourceClientRaw(self)

    @cached_property
    def Role(self):
        from foundry_sdk.v2.filesystem.resource_role import ResourceRoleClient

        return ResourceRoleClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def add_markings(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        marking_ids: typing.List[core_models.MarkingId],
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """
        Adds a list of Markings to a resource.
        :param resource_rid:
        :type resource_rid: ResourceRid
        :param marking_ids:
        :type marking_ids: List[MarkingId]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises AddMarkingsPermissionDenied: Could not addMarkings the Resource.
        :raises ForbiddenOperationOnAutosavedResource: Performing this operation on an autosaved resource is not supported.
        :raises ForbiddenOperationOnHiddenResource: Performing this operation on a hidden resource is not supported.
        :raises MarkingNotFound: A provided marking ID cannot be found.
        :raises OrganizationMarkingNotSupported: Adding an organization marking as a regular marking is not supported. Use the organization endpoints on a  project resource instead.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/addMarkings",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.AddMarkingsRequest(
                    marking_ids=marking_ids,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "AddMarkingsPermissionDenied": filesystem_errors.AddMarkingsPermissionDenied,
                    "ForbiddenOperationOnAutosavedResource": filesystem_errors.ForbiddenOperationOnAutosavedResource,
                    "ForbiddenOperationOnHiddenResource": filesystem_errors.ForbiddenOperationOnHiddenResource,
                    "MarkingNotFound": filesystem_errors.MarkingNotFound,
                    "OrganizationMarkingNotSupported": filesystem_errors.OrganizationMarkingNotSupported,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def delete(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """
        Move the given resource to the trash. Following this operation, the resource can be restored, using the
        `restore` operation, or permanently deleted using the `permanentlyDelete` operation.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises DeleteResourcePermissionDenied: Could not delete the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        :raises TrashingAutosavedResourcesNotSupported: Auto-saved Resources cannot be trashed.
        :raises TrashingHiddenResourcesNotSupported: Hidden Resources cannot be trashed.
        :raises TrashingSpaceNotSupported: Spaces cannot be trashed.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="DELETE",
                resource_path="/v2/filesystem/resources/{resourceRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "DeleteResourcePermissionDenied": filesystem_errors.DeleteResourcePermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                    "TrashingAutosavedResourcesNotSupported": filesystem_errors.TrashingAutosavedResourcesNotSupported,
                    "TrashingHiddenResourcesNotSupported": filesystem_errors.TrashingHiddenResourcesNotSupported,
                    "TrashingSpaceNotSupported": filesystem_errors.TrashingSpaceNotSupported,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> filesystem_models.Resource:
        """
        Get the Resource with the specified rid.
        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: filesystem_models.Resource

        :raises GetRootFolderNotSupported: Getting the root folder as a resource is not supported.
        :raises GetSpaceResourceNotSupported: Getting a space as a resource is not supported.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.Resource,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetRootFolderNotSupported": filesystem_errors.GetRootFolderNotSupported,
                    "GetSpaceResourceNotSupported": filesystem_errors.GetSpaceResourceNotSupported,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_access_requirements(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> filesystem_models.AccessRequirements:
        """
        Returns a list of access requirements a user needs in order to view a resource. Access requirements are
        composed of Organizations and Markings, and can either be applied directly to the resource or inherited.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: filesystem_models.AccessRequirements

        :raises GetAccessRequirementsPermissionDenied: Could not getAccessRequirements the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}/getAccessRequirements",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.AccessRequirements,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetAccessRequirementsPermissionDenied": filesystem_errors.GetAccessRequirementsPermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_batch(
        self,
        body: typing_extensions.Annotated[
            typing.List[filesystem_models.GetResourcesBatchRequestElement],
            annotated_types.Len(min_length=1, max_length=1000),
        ],
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> filesystem_models.GetResourcesBatchResponse:
        """
        Fetches multiple resources in a single request.
        Returns a map from RID to the corresponding resource. If a resource does not exist, or if it is a root folder or space, its RID will not be included in the map.
        At most 1,000 resources should be requested at once.


        The maximum batch size for this endpoint is 1000.
        :param body: Body of the request
        :type body: List[GetResourcesBatchRequestElement]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: filesystem_models.GetResourcesBatchResponse
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/getBatch",
                query_params={
                    "preview": preview,
                },
                path_params={},
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=body,
                response_type=filesystem_models.GetResourcesBatchResponse,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_by_path(
        self,
        *,
        path: filesystem_models.ResourcePath,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> filesystem_models.Resource:
        """
        Get a Resource by its absolute path.
        :param path: The path to the Resource. The leading slash is optional.
        :type path: ResourcePath
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: filesystem_models.Resource

        :raises GetByPathPermissionDenied: Could not getByPath the Resource.
        :raises GetRootFolderNotSupported: Getting the root folder as a resource is not supported.
        :raises GetSpaceResourceNotSupported: Getting a space as a resource is not supported.
        :raises InvalidPath: The given path is invalid.   A valid path has all components separated by a single `/`.
        :raises PathNotFound: The given path could not be found.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/getByPath",
                query_params={
                    "path": path,
                    "preview": preview,
                },
                path_params={},
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.Resource,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetByPathPermissionDenied": filesystem_errors.GetByPathPermissionDenied,
                    "GetRootFolderNotSupported": filesystem_errors.GetRootFolderNotSupported,
                    "GetSpaceResourceNotSupported": filesystem_errors.GetSpaceResourceNotSupported,
                    "InvalidPath": filesystem_errors.InvalidPath,
                    "PathNotFound": filesystem_errors.PathNotFound,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def markings(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        page_size: typing.Optional[core_models.PageSize] = None,
        page_token: typing.Optional[core_models.PageToken] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core.ResourceIterator[core_models.MarkingId]:
        """
        List of Markings directly applied to a resource. The number of Markings on a resource is typically small
        so the `pageSize` and `pageToken` parameters are not required.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param page_size: The page size to use for the endpoint.
        :type page_size: Optional[PageSize]
        :param page_token: The page token indicates where to start paging. This should be omitted from the first page's request. To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response and use it to populate the `pageToken` field of the next request.
        :type page_token: Optional[PageToken]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core.ResourceIterator[core_models.MarkingId]

        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}/markings",
                query_params={
                    "pageSize": page_size,
                    "pageToken": page_token,
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.ListMarkingsOfResourceResponse,
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
    def permanently_delete(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """
        Permanently delete the given resource from the trash. If the Resource is not directly trashed, a
        `ResourceNotTrashed` error will be thrown.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises PermanentlyDeleteResourcePermissionDenied: Could not permanentlyDelete the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        :raises ResourceNotTrashed: The Resource should be directly trashed before being permanently deleted.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/permanentlyDelete",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "PermanentlyDeleteResourcePermissionDenied": filesystem_errors.PermanentlyDeleteResourcePermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                    "ResourceNotTrashed": filesystem_errors.ResourceNotTrashed,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def remove_markings(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        marking_ids: typing.List[core_models.MarkingId],
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """
        Removes Markings from a resource.
        :param resource_rid:
        :type resource_rid: ResourceRid
        :param marking_ids:
        :type marking_ids: List[MarkingId]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises ForbiddenOperationOnAutosavedResource: Performing this operation on an autosaved resource is not supported.
        :raises ForbiddenOperationOnHiddenResource: Performing this operation on a hidden resource is not supported.
        :raises MarkingNotFound: A provided marking ID cannot be found.
        :raises OrganizationMarkingNotSupported: Adding an organization marking as a regular marking is not supported. Use the organization endpoints on a  project resource instead.
        :raises RemoveMarkingsPermissionDenied: Could not removeMarkings the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/removeMarkings",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.RemoveMarkingsRequest(
                    marking_ids=marking_ids,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "ForbiddenOperationOnAutosavedResource": filesystem_errors.ForbiddenOperationOnAutosavedResource,
                    "ForbiddenOperationOnHiddenResource": filesystem_errors.ForbiddenOperationOnHiddenResource,
                    "MarkingNotFound": filesystem_errors.MarkingNotFound,
                    "OrganizationMarkingNotSupported": filesystem_errors.OrganizationMarkingNotSupported,
                    "RemoveMarkingsPermissionDenied": filesystem_errors.RemoveMarkingsPermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def restore(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> None:
        """
        Restore the given resource and any directly trashed ancestors from the trash. If the resource is not
        trashed, this operation will be ignored.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: None

        :raises ResourceNotDirectlyTrashed: The Resource is not directly trashed.
        :raises ResourceNotFound: The given Resource could not be found.
        :raises RestoreResourcePermissionDenied: Could not restore the Resource.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/restore",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "ResourceNotDirectlyTrashed": filesystem_errors.ResourceNotDirectlyTrashed,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                    "RestoreResourcePermissionDenied": filesystem_errors.RestoreResourcePermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _ResourceClientRaw:
    def __init__(self, client: ResourceClient) -> None:
        def add_markings(_: None): ...
        def delete(_: None): ...
        def get(_: filesystem_models.Resource): ...
        def get_access_requirements(_: filesystem_models.AccessRequirements): ...
        def get_batch(_: filesystem_models.GetResourcesBatchResponse): ...
        def get_by_path(_: filesystem_models.Resource): ...
        def markings(_: filesystem_models.ListMarkingsOfResourceResponse): ...
        def permanently_delete(_: None): ...
        def remove_markings(_: None): ...
        def restore(_: None): ...

        self.add_markings = core.with_raw_response(add_markings, client.add_markings)
        self.delete = core.with_raw_response(delete, client.delete)
        self.get = core.with_raw_response(get, client.get)
        self.get_access_requirements = core.with_raw_response(
            get_access_requirements, client.get_access_requirements
        )
        self.get_batch = core.with_raw_response(get_batch, client.get_batch)
        self.get_by_path = core.with_raw_response(get_by_path, client.get_by_path)
        self.markings = core.with_raw_response(markings, client.markings)
        self.permanently_delete = core.with_raw_response(
            permanently_delete, client.permanently_delete
        )
        self.remove_markings = core.with_raw_response(remove_markings, client.remove_markings)
        self.restore = core.with_raw_response(restore, client.restore)


class _ResourceClientStreaming:
    def __init__(self, client: ResourceClient) -> None:
        def get(_: filesystem_models.Resource): ...
        def get_access_requirements(_: filesystem_models.AccessRequirements): ...
        def get_batch(_: filesystem_models.GetResourcesBatchResponse): ...
        def get_by_path(_: filesystem_models.Resource): ...
        def markings(_: filesystem_models.ListMarkingsOfResourceResponse): ...

        self.get = core.with_streaming_response(get, client.get)
        self.get_access_requirements = core.with_streaming_response(
            get_access_requirements, client.get_access_requirements
        )
        self.get_batch = core.with_streaming_response(get_batch, client.get_batch)
        self.get_by_path = core.with_streaming_response(get_by_path, client.get_by_path)
        self.markings = core.with_streaming_response(markings, client.markings)


class AsyncResourceClient:
    """
    The API client for the Resource Resource.

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

        self.with_streaming_response = _AsyncResourceClientStreaming(self)
        self.with_raw_response = _AsyncResourceClientRaw(self)

    @cached_property
    def Role(self):
        from foundry_sdk.v2.filesystem.resource_role import AsyncResourceRoleClient

        return AsyncResourceRoleClient(
            auth=self._auth,
            hostname=self._hostname,
            config=self._config,
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def add_markings(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        marking_ids: typing.List[core_models.MarkingId],
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """
        Adds a list of Markings to a resource.
        :param resource_rid:
        :type resource_rid: ResourceRid
        :param marking_ids:
        :type marking_ids: List[MarkingId]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises AddMarkingsPermissionDenied: Could not addMarkings the Resource.
        :raises ForbiddenOperationOnAutosavedResource: Performing this operation on an autosaved resource is not supported.
        :raises ForbiddenOperationOnHiddenResource: Performing this operation on a hidden resource is not supported.
        :raises MarkingNotFound: A provided marking ID cannot be found.
        :raises OrganizationMarkingNotSupported: Adding an organization marking as a regular marking is not supported. Use the organization endpoints on a  project resource instead.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/addMarkings",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.AddMarkingsRequest(
                    marking_ids=marking_ids,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "AddMarkingsPermissionDenied": filesystem_errors.AddMarkingsPermissionDenied,
                    "ForbiddenOperationOnAutosavedResource": filesystem_errors.ForbiddenOperationOnAutosavedResource,
                    "ForbiddenOperationOnHiddenResource": filesystem_errors.ForbiddenOperationOnHiddenResource,
                    "MarkingNotFound": filesystem_errors.MarkingNotFound,
                    "OrganizationMarkingNotSupported": filesystem_errors.OrganizationMarkingNotSupported,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def delete(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """
        Move the given resource to the trash. Following this operation, the resource can be restored, using the
        `restore` operation, or permanently deleted using the `permanentlyDelete` operation.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises DeleteResourcePermissionDenied: Could not delete the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        :raises TrashingAutosavedResourcesNotSupported: Auto-saved Resources cannot be trashed.
        :raises TrashingHiddenResourcesNotSupported: Hidden Resources cannot be trashed.
        :raises TrashingSpaceNotSupported: Spaces cannot be trashed.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="DELETE",
                resource_path="/v2/filesystem/resources/{resourceRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "DeleteResourcePermissionDenied": filesystem_errors.DeleteResourcePermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                    "TrashingAutosavedResourcesNotSupported": filesystem_errors.TrashingAutosavedResourcesNotSupported,
                    "TrashingHiddenResourcesNotSupported": filesystem_errors.TrashingHiddenResourcesNotSupported,
                    "TrashingSpaceNotSupported": filesystem_errors.TrashingSpaceNotSupported,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[filesystem_models.Resource]:
        """
        Get the Resource with the specified rid.
        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[filesystem_models.Resource]

        :raises GetRootFolderNotSupported: Getting the root folder as a resource is not supported.
        :raises GetSpaceResourceNotSupported: Getting a space as a resource is not supported.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.Resource,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetRootFolderNotSupported": filesystem_errors.GetRootFolderNotSupported,
                    "GetSpaceResourceNotSupported": filesystem_errors.GetSpaceResourceNotSupported,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_access_requirements(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[filesystem_models.AccessRequirements]:
        """
        Returns a list of access requirements a user needs in order to view a resource. Access requirements are
        composed of Organizations and Markings, and can either be applied directly to the resource or inherited.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[filesystem_models.AccessRequirements]

        :raises GetAccessRequirementsPermissionDenied: Could not getAccessRequirements the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}/getAccessRequirements",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.AccessRequirements,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetAccessRequirementsPermissionDenied": filesystem_errors.GetAccessRequirementsPermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_batch(
        self,
        body: typing_extensions.Annotated[
            typing.List[filesystem_models.GetResourcesBatchRequestElement],
            annotated_types.Len(min_length=1, max_length=1000),
        ],
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[filesystem_models.GetResourcesBatchResponse]:
        """
        Fetches multiple resources in a single request.
        Returns a map from RID to the corresponding resource. If a resource does not exist, or if it is a root folder or space, its RID will not be included in the map.
        At most 1,000 resources should be requested at once.


        The maximum batch size for this endpoint is 1000.
        :param body: Body of the request
        :type body: List[GetResourcesBatchRequestElement]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[filesystem_models.GetResourcesBatchResponse]
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/getBatch",
                query_params={
                    "preview": preview,
                },
                path_params={},
                header_params={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body=body,
                response_type=filesystem_models.GetResourcesBatchResponse,
                request_timeout=request_timeout,
                throwable_errors={},
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def get_by_path(
        self,
        *,
        path: filesystem_models.ResourcePath,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[filesystem_models.Resource]:
        """
        Get a Resource by its absolute path.
        :param path: The path to the Resource. The leading slash is optional.
        :type path: ResourcePath
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[filesystem_models.Resource]

        :raises GetByPathPermissionDenied: Could not getByPath the Resource.
        :raises GetRootFolderNotSupported: Getting the root folder as a resource is not supported.
        :raises GetSpaceResourceNotSupported: Getting a space as a resource is not supported.
        :raises InvalidPath: The given path is invalid.   A valid path has all components separated by a single `/`.
        :raises PathNotFound: The given path could not be found.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/getByPath",
                query_params={
                    "path": path,
                    "preview": preview,
                },
                path_params={},
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.Resource,
                request_timeout=request_timeout,
                throwable_errors={
                    "GetByPathPermissionDenied": filesystem_errors.GetByPathPermissionDenied,
                    "GetRootFolderNotSupported": filesystem_errors.GetRootFolderNotSupported,
                    "GetSpaceResourceNotSupported": filesystem_errors.GetSpaceResourceNotSupported,
                    "InvalidPath": filesystem_errors.InvalidPath,
                    "PathNotFound": filesystem_errors.PathNotFound,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def markings(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        page_size: typing.Optional[core_models.PageSize] = None,
        page_token: typing.Optional[core_models.PageToken] = None,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> core.AsyncResourceIterator[core_models.MarkingId]:
        """
        List of Markings directly applied to a resource. The number of Markings on a resource is typically small
        so the `pageSize` and `pageToken` parameters are not required.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param page_size: The page size to use for the endpoint.
        :type page_size: Optional[PageSize]
        :param page_token: The page token indicates where to start paging. This should be omitted from the first page's request. To fetch the next page, clients should take the value from the `nextPageToken` field of the previous response and use it to populate the `pageToken` field of the next request.
        :type page_token: Optional[PageToken]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: core.AsyncResourceIterator[core_models.MarkingId]

        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="GET",
                resource_path="/v2/filesystem/resources/{resourceRid}/markings",
                query_params={
                    "pageSize": page_size,
                    "pageToken": page_token,
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Accept": "application/json",
                },
                body=None,
                response_type=filesystem_models.ListMarkingsOfResourceResponse,
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
    def permanently_delete(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """
        Permanently delete the given resource from the trash. If the Resource is not directly trashed, a
        `ResourceNotTrashed` error will be thrown.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises PermanentlyDeleteResourcePermissionDenied: Could not permanentlyDelete the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        :raises ResourceNotTrashed: The Resource should be directly trashed before being permanently deleted.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/permanentlyDelete",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "PermanentlyDeleteResourcePermissionDenied": filesystem_errors.PermanentlyDeleteResourcePermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                    "ResourceNotTrashed": filesystem_errors.ResourceNotTrashed,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def remove_markings(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        marking_ids: typing.List[core_models.MarkingId],
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """
        Removes Markings from a resource.
        :param resource_rid:
        :type resource_rid: ResourceRid
        :param marking_ids:
        :type marking_ids: List[MarkingId]
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises ForbiddenOperationOnAutosavedResource: Performing this operation on an autosaved resource is not supported.
        :raises ForbiddenOperationOnHiddenResource: Performing this operation on a hidden resource is not supported.
        :raises MarkingNotFound: A provided marking ID cannot be found.
        :raises OrganizationMarkingNotSupported: Adding an organization marking as a regular marking is not supported. Use the organization endpoints on a  project resource instead.
        :raises RemoveMarkingsPermissionDenied: Could not removeMarkings the Resource.
        :raises ResourceNotFound: The given Resource could not be found.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/removeMarkings",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={
                    "Content-Type": "application/json",
                },
                body=filesystem_models.RemoveMarkingsRequest(
                    marking_ids=marking_ids,
                ),
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "ForbiddenOperationOnAutosavedResource": filesystem_errors.ForbiddenOperationOnAutosavedResource,
                    "ForbiddenOperationOnHiddenResource": filesystem_errors.ForbiddenOperationOnHiddenResource,
                    "MarkingNotFound": filesystem_errors.MarkingNotFound,
                    "OrganizationMarkingNotSupported": filesystem_errors.OrganizationMarkingNotSupported,
                    "RemoveMarkingsPermissionDenied": filesystem_errors.RemoveMarkingsPermissionDenied,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )

    @core.maybe_ignore_preview
    @pydantic.validate_call
    @errors.handle_unexpected
    def restore(
        self,
        resource_rid: filesystem_models.ResourceRid,
        *,
        preview: typing.Optional[core_models.PreviewMode] = None,
        request_timeout: typing.Optional[core.Timeout] = None,
        _sdk_internal: core.SdkInternal = {},
    ) -> typing.Awaitable[None]:
        """
        Restore the given resource and any directly trashed ancestors from the trash. If the resource is not
        trashed, this operation will be ignored.

        :param resource_rid:
        :type resource_rid: ResourceRid
        :param preview: Enables the use of preview functionality.
        :type preview: Optional[PreviewMode]
        :param request_timeout: timeout setting for this request in seconds.
        :type request_timeout: Optional[int]
        :return: Returns the result object.
        :rtype: typing.Awaitable[None]

        :raises ResourceNotDirectlyTrashed: The Resource is not directly trashed.
        :raises ResourceNotFound: The given Resource could not be found.
        :raises RestoreResourcePermissionDenied: Could not restore the Resource.
        """

        return self._api_client.call_api(
            core.RequestInfo(
                method="POST",
                resource_path="/v2/filesystem/resources/{resourceRid}/restore",
                query_params={
                    "preview": preview,
                },
                path_params={
                    "resourceRid": resource_rid,
                },
                header_params={},
                body=None,
                response_type=None,
                request_timeout=request_timeout,
                throwable_errors={
                    "ResourceNotDirectlyTrashed": filesystem_errors.ResourceNotDirectlyTrashed,
                    "ResourceNotFound": filesystem_errors.ResourceNotFound,
                    "RestoreResourcePermissionDenied": filesystem_errors.RestoreResourcePermissionDenied,
                },
                response_mode=_sdk_internal.get("response_mode"),
            ),
        )


class _AsyncResourceClientRaw:
    def __init__(self, client: AsyncResourceClient) -> None:
        def add_markings(_: None): ...
        def delete(_: None): ...
        def get(_: filesystem_models.Resource): ...
        def get_access_requirements(_: filesystem_models.AccessRequirements): ...
        def get_batch(_: filesystem_models.GetResourcesBatchResponse): ...
        def get_by_path(_: filesystem_models.Resource): ...
        def markings(_: filesystem_models.ListMarkingsOfResourceResponse): ...
        def permanently_delete(_: None): ...
        def remove_markings(_: None): ...
        def restore(_: None): ...

        self.add_markings = core.async_with_raw_response(add_markings, client.add_markings)
        self.delete = core.async_with_raw_response(delete, client.delete)
        self.get = core.async_with_raw_response(get, client.get)
        self.get_access_requirements = core.async_with_raw_response(
            get_access_requirements, client.get_access_requirements
        )
        self.get_batch = core.async_with_raw_response(get_batch, client.get_batch)
        self.get_by_path = core.async_with_raw_response(get_by_path, client.get_by_path)
        self.markings = core.async_with_raw_response(markings, client.markings)
        self.permanently_delete = core.async_with_raw_response(
            permanently_delete, client.permanently_delete
        )
        self.remove_markings = core.async_with_raw_response(remove_markings, client.remove_markings)
        self.restore = core.async_with_raw_response(restore, client.restore)


class _AsyncResourceClientStreaming:
    def __init__(self, client: AsyncResourceClient) -> None:
        def get(_: filesystem_models.Resource): ...
        def get_access_requirements(_: filesystem_models.AccessRequirements): ...
        def get_batch(_: filesystem_models.GetResourcesBatchResponse): ...
        def get_by_path(_: filesystem_models.Resource): ...
        def markings(_: filesystem_models.ListMarkingsOfResourceResponse): ...

        self.get = core.async_with_streaming_response(get, client.get)
        self.get_access_requirements = core.async_with_streaming_response(
            get_access_requirements, client.get_access_requirements
        )
        self.get_batch = core.async_with_streaming_response(get_batch, client.get_batch)
        self.get_by_path = core.async_with_streaming_response(get_by_path, client.get_by_path)
        self.markings = core.async_with_streaming_response(markings, client.markings)
